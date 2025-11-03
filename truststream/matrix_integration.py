# Matrix Chat Integration for TrustStream v4.4
# Real-time AI Moderation and Content Analysis

import logging
import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import aiohttp
from nio import AsyncClient, MatrixRoom, RoomMessageText, RoomMessageMedia, Event
from nio.events import RoomMemberEvent, RoomRedactionEvent
import hashlib
import re

from .ai_providers import AIProviderManager, AnalysisType, AIResponse
from .agents.manager import AgentManager
from .trust_pyramid import TrustPyramidCalculator

logger = logging.getLogger(__name__)


class ModerationAction(Enum):
    """Matrix moderation actions"""
    NONE = "none"
    WARN = "warn"
    MUTE = "mute"
    KICK = "kick"
    BAN = "ban"
    REDACT = "redact"
    ROOM_LOCK = "room_lock"


class EventType(Enum):
    """Matrix event types to monitor"""
    MESSAGE = "m.room.message"
    MEMBER = "m.room.member"
    REDACTION = "m.room.redaction"
    REACTION = "m.reaction"
    EDIT = "m.room.message.edit"


@dataclass
class ModerationDecision:
    """Moderation decision for Matrix events"""
    event_id: str
    room_id: str
    user_id: str
    action: ModerationAction
    reason: str
    confidence: float
    ai_responses: List[AIResponse]
    trust_score: float
    expires_at: Optional[datetime]
    escalate_to_human: bool
    metadata: Dict[str, Any]


@dataclass
class RoomConfig:
    """Configuration for Matrix room moderation"""
    room_id: str
    moderation_level: str  # strict, moderate, relaxed
    auto_moderation: bool
    trust_threshold: float
    allowed_content_types: List[str]
    rate_limits: Dict[str, int]
    custom_rules: List[Dict[str, Any]]
    moderator_users: List[str]
    escalation_room: Optional[str]


class MatrixModerationBot:
    """
    Matrix Moderation Bot for TrustStream v4.4
    
    Provides real-time AI-powered moderation for Matrix chat rooms with:
    - Real-time content analysis using multiple AI providers
    - Trust-based user scoring and reputation management
    - Automated moderation actions (warn, mute, kick, ban, redact)
    - Escalation to human moderators for complex cases
    - Room-specific configuration and rules
    - Rate limiting and spam detection
    - Cross-room coordination and global user tracking
    - Audit logging and transparency features
    - Integration with TrustStream agent ecosystem
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.homeserver = config['matrix']['homeserver']
        self.username = config['matrix']['username']
        self.password = config['matrix']['password']
        self.device_name = config['matrix'].get('device_name', 'TrustStream-Bot')
        
        # Initialize Matrix client
        self.client = AsyncClient(self.homeserver, self.username)
        
        # Initialize TrustStream components
        self.ai_manager = AIProviderManager(config.get('ai_providers', {}))
        self.agent_manager = AgentManager(config.get('agents', {}))
        self.trust_calculator = TrustPyramidCalculator(config.get('trust_pyramid', {}))
        
        # Room configurations
        self.room_configs: Dict[str, RoomConfig] = {}
        self.monitored_rooms: Set[str] = set()
        
        # Moderation state
        self.active_moderations: Dict[str, ModerationDecision] = {}
        self.user_trust_cache: Dict[str, Dict[str, Any]] = {}
        self.rate_limiters: Dict[str, Dict[str, List[float]]] = {}
        
        # Event handlers
        self.event_handlers: Dict[EventType, List[Callable]] = {
            EventType.MESSAGE: [],
            EventType.MEMBER: [],
            EventType.REDACTION: [],
            EventType.REACTION: [],
            EventType.EDIT: []
        }
        
        # Performance metrics
        self.metrics = {
            'events_processed': 0,
            'moderations_applied': 0,
            'false_positives': 0,
            'escalations': 0,
            'response_times': []
        }
        
        # Setup event callbacks
        self._setup_event_callbacks()
        
        logger.info("Matrix Moderation Bot initialized")
    
    async def start(self):
        """Start the Matrix moderation bot."""
        try:
            logger.info("Starting Matrix moderation bot...")
            
            # Login to Matrix
            login_response = await self.client.login(self.password)
            if not login_response:
                raise Exception("Failed to login to Matrix")
            
            logger.info(f"Logged in as {self.username}")
            
            # Load room configurations
            await self._load_room_configurations()
            
            # Join monitored rooms
            await self._join_monitored_rooms()
            
            # Start sync loop
            await self.client.sync_forever(timeout=30000)
            
        except Exception as e:
            logger.error(f"Failed to start Matrix bot: {str(e)}")
            raise
    
    async def stop(self):
        """Stop the Matrix moderation bot."""
        try:
            logger.info("Stopping Matrix moderation bot...")
            
            # Close Matrix client
            await self.client.close()
            
            logger.info("Matrix moderation bot stopped")
            
        except Exception as e:
            logger.error(f"Error stopping Matrix bot: {str(e)}")
    
    def _setup_event_callbacks(self):
        """Setup Matrix event callbacks."""
        # Message events
        self.client.add_event_callback(self._handle_message_event, RoomMessageText)
        self.client.add_event_callback(self._handle_media_event, RoomMessageMedia)
        
        # Member events (joins, leaves, kicks, bans)
        self.client.add_event_callback(self._handle_member_event, RoomMemberEvent)
        
        # Redaction events
        self.client.add_event_callback(self._handle_redaction_event, RoomRedactionEvent)
        
        logger.info("Matrix event callbacks configured")
    
    async def _handle_message_event(self, room: MatrixRoom, event: RoomMessageText):
        """Handle text message events."""
        try:
            start_time = time.time()
            
            # Skip bot's own messages
            if event.sender == self.client.user_id:
                return
            
            # Check if room is monitored
            if room.room_id not in self.monitored_rooms:
                return
            
            logger.debug(f"Processing message from {event.sender} in {room.room_id}")
            
            # Get room configuration
            room_config = self.room_configs.get(room.room_id)
            if not room_config:
                return
            
            # Check rate limits
            if await self._check_rate_limits(event.sender, room.room_id):
                await self._apply_rate_limit_action(event.sender, room.room_id, event.event_id)
                return
            
            # Analyze message content
            moderation_decision = await self._analyze_message_content(
                room, event, room_config
            )
            
            # Apply moderation decision
            if moderation_decision and moderation_decision.action != ModerationAction.NONE:
                await self._apply_moderation_decision(moderation_decision)
            
            # Update metrics
            processing_time = time.time() - start_time
            self.metrics['events_processed'] += 1
            self.metrics['response_times'].append(processing_time)
            
            # Keep only last 1000 response times
            if len(self.metrics['response_times']) > 1000:
                self.metrics['response_times'] = self.metrics['response_times'][-1000:]
            
        except Exception as e:
            logger.error(f"Error handling message event: {str(e)}")
    
    async def _handle_media_event(self, room: MatrixRoom, event: RoomMessageMedia):
        """Handle media message events (images, videos, files)."""
        try:
            # Skip bot's own messages
            if event.sender == self.client.user_id:
                return
            
            # Check if room is monitored
            if room.room_id not in self.monitored_rooms:
                return
            
            logger.debug(f"Processing media from {event.sender} in {room.room_id}")
            
            # Get room configuration
            room_config = self.room_configs.get(room.room_id)
            if not room_config:
                return
            
            # Check if media type is allowed
            if not await self._check_media_allowed(event, room_config):
                await self._apply_media_restriction(event.sender, room.room_id, event.event_id)
                return
            
            # Analyze media content (if supported)
            moderation_decision = await self._analyze_media_content(
                room, event, room_config
            )
            
            # Apply moderation decision
            if moderation_decision and moderation_decision.action != ModerationAction.NONE:
                await self._apply_moderation_decision(moderation_decision)
            
        except Exception as e:
            logger.error(f"Error handling media event: {str(e)}")
    
    async def _handle_member_event(self, room: MatrixRoom, event: RoomMemberEvent):
        """Handle room member events (joins, leaves, etc.)."""
        try:
            # Check if room is monitored
            if room.room_id not in self.monitored_rooms:
                return
            
            logger.debug(f"Member event: {event.membership} for {event.state_key} in {room.room_id}")
            
            # Handle new joins
            if event.membership == "join" and event.prev_membership != "join":
                await self._handle_user_join(room, event)
            
            # Handle leaves/kicks/bans
            elif event.membership in ["leave", "ban"]:
                await self._handle_user_departure(room, event)
            
        except Exception as e:
            logger.error(f"Error handling member event: {str(e)}")
    
    async def _handle_redaction_event(self, room: MatrixRoom, event: RoomRedactionEvent):
        """Handle message redaction events."""
        try:
            logger.debug(f"Redaction event in {room.room_id}: {event.redacts}")
            
            # Track redactions for audit purposes
            await self._log_redaction(room.room_id, event)
            
        except Exception as e:
            logger.error(f"Error handling redaction event: {str(e)}")
    
    async def _analyze_message_content(
        self, 
        room: MatrixRoom, 
        event: RoomMessageText, 
        room_config: RoomConfig
    ) -> Optional[ModerationDecision]:
        """Analyze message content using AI providers and agents."""
        try:
            content = event.body
            user_id = event.sender
            
            # Get user trust score
            trust_score = await self._get_user_trust_score(user_id, room.room_id)
            
            # Skip analysis for highly trusted users in relaxed mode
            if (room_config.moderation_level == "relaxed" and 
                trust_score > 0.8):
                return None
            
            # Prepare analysis context
            context = {
                'room_id': room.room_id,
                'user_id': user_id,
                'trust_score': trust_score,
                'room_config': asdict(room_config),
                'message_metadata': {
                    'event_id': event.event_id,
                    'timestamp': event.server_timestamp,
                    'formatted_body': getattr(event, 'formatted_body', None)
                }
            }
            
            # Run AI analysis
            ai_responses = []
            
            # Content moderation analysis
            content_response = await self.ai_manager.analyze_content(
                content, AnalysisType.CONTENT_MODERATION, context
            )
            ai_responses.append(content_response)
            
            # Additional analyses based on content and trust score
            if trust_score < 0.5:  # Lower trust users get more scrutiny
                # Harassment detection
                harassment_response = await self.ai_manager.analyze_content(
                    content, AnalysisType.HARASSMENT_DETECTION, context
                )
                ai_responses.append(harassment_response)
                
                # Bias detection
                bias_response = await self.ai_manager.analyze_content(
                    content, AnalysisType.BIAS_DETECTION, context
                )
                ai_responses.append(bias_response)
            
            # Cultural sensitivity (always check)
            cultural_response = await self.ai_manager.analyze_content(
                content, AnalysisType.CULTURAL_SENSITIVITY, context
            )
            ai_responses.append(cultural_response)
            
            # Mental health support check
            mental_health_response = await self.ai_manager.analyze_content(
                content, AnalysisType.MENTAL_HEALTH_SUPPORT, context
            )
            ai_responses.append(mental_health_response)
            
            # Determine overall moderation decision
            moderation_decision = await self._make_moderation_decision(
                event.event_id, room.room_id, user_id, ai_responses, trust_score, room_config
            )
            
            return moderation_decision
            
        except Exception as e:
            logger.error(f"Content analysis failed: {str(e)}")
            return None
    
    async def _analyze_media_content(
        self, 
        room: MatrixRoom, 
        event: RoomMessageMedia, 
        room_config: RoomConfig
    ) -> Optional[ModerationDecision]:
        """Analyze media content (placeholder for future image/video analysis)."""
        try:
            # For now, just check basic media properties
            user_id = event.sender
            trust_score = await self._get_user_trust_score(user_id, room.room_id)
            
            # Basic media validation
            if hasattr(event, 'url') and event.url:
                # Check file size, type, etc.
                # This would be expanded with actual media analysis
                pass
            
            # For low trust users, flag media for review
            if trust_score < 0.3:
                return ModerationDecision(
                    event_id=event.event_id,
                    room_id=room.room_id,
                    user_id=user_id,
                    action=ModerationAction.WARN,
                    reason="Media from low-trust user requires review",
                    confidence=0.6,
                    ai_responses=[],
                    trust_score=trust_score,
                    expires_at=None,
                    escalate_to_human=True,
                    metadata={'media_type': getattr(event, 'msgtype', 'unknown')}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Media analysis failed: {str(e)}")
            return None
    
    async def _make_moderation_decision(
        self,
        event_id: str,
        room_id: str,
        user_id: str,
        ai_responses: List[AIResponse],
        trust_score: float,
        room_config: RoomConfig
    ) -> Optional[ModerationDecision]:
        """Make final moderation decision based on AI responses and trust score."""
        try:
            if not ai_responses:
                return None
            
            # Analyze AI responses
            block_responses = [r for r in ai_responses if r.decision == 'BLOCK']
            flag_responses = [r for r in ai_responses if r.decision == 'FLAG']
            monitor_responses = [r for r in ai_responses if r.decision == 'MONITOR']
            
            # Calculate overall confidence
            avg_confidence = sum(r.confidence for r in ai_responses) / len(ai_responses)
            
            # Adjust based on trust score
            trust_adjustment = 1.0 - (trust_score * 0.3)  # Lower trust = higher sensitivity
            adjusted_confidence = avg_confidence * trust_adjustment
            
            # Determine action based on responses and room config
            action = ModerationAction.NONE
            reason = "Content approved"
            escalate = False
            
            if block_responses:
                # Immediate blocking required
                if room_config.moderation_level == "strict":
                    action = ModerationAction.BAN if trust_score < 0.2 else ModerationAction.KICK
                elif room_config.moderation_level == "moderate":
                    action = ModerationAction.KICK if trust_score < 0.3 else ModerationAction.MUTE
                else:  # relaxed
                    action = ModerationAction.MUTE if trust_score < 0.4 else ModerationAction.WARN
                
                reason = f"Content violation detected: {block_responses[0].reasoning}"
                escalate = adjusted_confidence < 0.8
                
            elif flag_responses:
                # Content needs attention
                if room_config.moderation_level == "strict":
                    action = ModerationAction.MUTE if trust_score < 0.4 else ModerationAction.WARN
                elif room_config.moderation_level == "moderate":
                    action = ModerationAction.WARN
                else:  # relaxed
                    action = ModerationAction.NONE
                
                reason = f"Content flagged for review: {flag_responses[0].reasoning}"
                escalate = True
                
            elif monitor_responses and trust_score < 0.3:
                # Monitor low-trust users more closely
                action = ModerationAction.WARN
                reason = "Content from low-trust user requires monitoring"
                escalate = False
            
            # Don't moderate if confidence is too low
            if adjusted_confidence < 0.5 and action != ModerationAction.NONE:
                escalate = True
                if action in [ModerationAction.BAN, ModerationAction.KICK]:
                    action = ModerationAction.WARN
            
            if action == ModerationAction.NONE:
                return None
            
            # Calculate expiration for temporary actions
            expires_at = None
            if action in [ModerationAction.MUTE, ModerationAction.WARN]:
                duration_hours = 1 if trust_score > 0.5 else 24
                expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
            
            return ModerationDecision(
                event_id=event_id,
                room_id=room_id,
                user_id=user_id,
                action=action,
                reason=reason,
                confidence=adjusted_confidence,
                ai_responses=ai_responses,
                trust_score=trust_score,
                expires_at=expires_at,
                escalate_to_human=escalate,
                metadata={
                    'room_moderation_level': room_config.moderation_level,
                    'ai_response_count': len(ai_responses),
                    'trust_adjustment': trust_adjustment
                }
            )
            
        except Exception as e:
            logger.error(f"Moderation decision failed: {str(e)}")
            return None
    
    async def _apply_moderation_decision(self, decision: ModerationDecision):
        """Apply moderation decision to Matrix room."""
        try:
            logger.info(f"Applying moderation: {decision.action.value} to {decision.user_id} in {decision.room_id}")
            
            # Store decision
            self.active_moderations[decision.event_id] = decision
            
            # Apply action
            if decision.action == ModerationAction.WARN:
                await self._send_warning(decision)
                
            elif decision.action == ModerationAction.MUTE:
                await self._mute_user(decision)
                
            elif decision.action == ModerationAction.KICK:
                await self._kick_user(decision)
                
            elif decision.action == ModerationAction.BAN:
                await self._ban_user(decision)
                
            elif decision.action == ModerationAction.REDACT:
                await self._redact_message(decision)
            
            # Escalate to human moderators if needed
            if decision.escalate_to_human:
                await self._escalate_to_humans(decision)
            
            # Update metrics
            self.metrics['moderations_applied'] += 1
            if decision.escalate_to_human:
                self.metrics['escalations'] += 1
            
            # Log decision for audit
            await self._log_moderation_decision(decision)
            
        except Exception as e:
            logger.error(f"Failed to apply moderation decision: {str(e)}")
    
    async def _send_warning(self, decision: ModerationDecision):
        """Send warning message to user."""
        try:
            warning_message = f"⚠️ **Moderation Warning**\n\n"
            warning_message += f"Your message has been flagged for: {decision.reason}\n"
            warning_message += f"Please review our community guidelines.\n"
            warning_message += f"Trust Score: {decision.trust_score:.2f}\n"
            
            if decision.expires_at:
                warning_message += f"This warning expires: {decision.expires_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
            
            await self.client.room_send(
                decision.room_id,
                "m.room.message",
                {
                    "msgtype": "m.notice",
                    "body": warning_message,
                    "format": "org.matrix.custom.html",
                    "formatted_body": warning_message.replace('\n', '<br>')
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to send warning: {str(e)}")
    
    async def _mute_user(self, decision: ModerationDecision):
        """Mute user in room (remove send permissions)."""
        try:
            # Set user power level to prevent sending messages
            await self.client.room_put_state(
                decision.room_id,
                "m.room.power_levels",
                {
                    "users": {
                        decision.user_id: -1  # Muted
                    }
                }
            )
            
            # Send notification
            mute_message = f"🔇 User {decision.user_id} has been muted.\n"
            mute_message += f"Reason: {decision.reason}\n"
            if decision.expires_at:
                mute_message += f"Expires: {decision.expires_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
            
            await self.client.room_send(
                decision.room_id,
                "m.room.message",
                {
                    "msgtype": "m.notice",
                    "body": mute_message
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to mute user: {str(e)}")
    
    async def _kick_user(self, decision: ModerationDecision):
        """Kick user from room."""
        try:
            await self.client.room_kick(
                decision.room_id,
                decision.user_id,
                reason=decision.reason
            )
            
            # Send notification
            kick_message = f"👢 User {decision.user_id} has been kicked.\n"
            kick_message += f"Reason: {decision.reason}\n"
            
            await self.client.room_send(
                decision.room_id,
                "m.room.message",
                {
                    "msgtype": "m.notice",
                    "body": kick_message
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to kick user: {str(e)}")
    
    async def _ban_user(self, decision: ModerationDecision):
        """Ban user from room."""
        try:
            await self.client.room_ban(
                decision.room_id,
                decision.user_id,
                reason=decision.reason
            )
            
            # Send notification
            ban_message = f"🚫 User {decision.user_id} has been banned.\n"
            ban_message += f"Reason: {decision.reason}\n"
            
            await self.client.room_send(
                decision.room_id,
                "m.room.message",
                {
                    "msgtype": "m.notice",
                    "body": ban_message
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to ban user: {str(e)}")
    
    async def _redact_message(self, decision: ModerationDecision):
        """Redact (delete) message."""
        try:
            await self.client.room_redact(
                decision.room_id,
                decision.event_id,
                reason=decision.reason
            )
            
        except Exception as e:
            logger.error(f"Failed to redact message: {str(e)}")
    
    async def _escalate_to_humans(self, decision: ModerationDecision):
        """Escalate decision to human moderators."""
        try:
            room_config = self.room_configs.get(decision.room_id)
            if not room_config or not room_config.escalation_room:
                return
            
            escalation_message = f"🚨 **Moderation Escalation**\n\n"
            escalation_message += f"Room: {decision.room_id}\n"
            escalation_message += f"User: {decision.user_id}\n"
            escalation_message += f"Action: {decision.action.value}\n"
            escalation_message += f"Reason: {decision.reason}\n"
            escalation_message += f"Confidence: {decision.confidence:.2f}\n"
            escalation_message += f"Trust Score: {decision.trust_score:.2f}\n"
            escalation_message += f"Event ID: {decision.event_id}\n"
            
            await self.client.room_send(
                room_config.escalation_room,
                "m.room.message",
                {
                    "msgtype": "m.notice",
                    "body": escalation_message,
                    "format": "org.matrix.custom.html",
                    "formatted_body": escalation_message.replace('\n', '<br>')
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to escalate to humans: {str(e)}")
    
    # Utility methods
    
    async def _get_user_trust_score(self, user_id: str, room_id: str) -> float:
        """Get user trust score from cache or calculate."""
        try:
            cache_key = f"{user_id}:{room_id}"
            
            # Check cache
            if cache_key in self.user_trust_cache:
                cache_entry = self.user_trust_cache[cache_key]
                if datetime.utcnow() - cache_entry['timestamp'] < timedelta(hours=1):
                    return cache_entry['trust_score']
            
            # Calculate trust score
            # This would integrate with your user data system
            user_data = await self._get_user_data(user_id, room_id)
            trust_profile = await self.trust_calculator.calculate_trust_profile(
                user_id, room_id, user_data
            )
            
            # Cache result
            self.user_trust_cache[cache_key] = {
                'trust_score': trust_profile.overall_score,
                'timestamp': datetime.utcnow()
            }
            
            return trust_profile.overall_score
            
        except Exception as e:
            logger.error(f"Trust score calculation failed: {str(e)}")
            return 0.5  # Default neutral score
    
    async def _get_user_data(self, user_id: str, room_id: str) -> Dict[str, Any]:
        """Get user data for trust calculation."""
        # Placeholder - would integrate with your user data system
        return {
            'content_history': [],
            'engagement_metrics': {},
            'connections': [],
            'recent_activity_count': 0
        }
    
    async def _check_rate_limits(self, user_id: str, room_id: str) -> bool:
        """Check if user is rate limited."""
        try:
            now = time.time()
            key = f"{user_id}:{room_id}"
            
            if key not in self.rate_limiters:
                self.rate_limiters[key] = {'messages': [], 'limit': 10}  # 10 messages per minute
            
            rate_limiter = self.rate_limiters[key]
            
            # Remove old messages (older than 1 minute)
            rate_limiter['messages'] = [msg_time for msg_time in rate_limiter['messages'] 
                                       if now - msg_time < 60]
            
            # Check limit
            if len(rate_limiter['messages']) >= rate_limiter['limit']:
                return True
            
            # Add current message
            rate_limiter['messages'].append(now)
            return False
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            return False
    
    async def _apply_rate_limit_action(self, user_id: str, room_id: str, event_id: str):
        """Apply rate limit moderation action."""
        try:
            decision = ModerationDecision(
                event_id=event_id,
                room_id=room_id,
                user_id=user_id,
                action=ModerationAction.MUTE,
                reason="Rate limit exceeded",
                confidence=1.0,
                ai_responses=[],
                trust_score=0.0,
                expires_at=datetime.utcnow() + timedelta(minutes=5),
                escalate_to_human=False,
                metadata={'rate_limit': True}
            )
            
            await self._apply_moderation_decision(decision)
            
        except Exception as e:
            logger.error(f"Rate limit action failed: {str(e)}")
    
    async def _check_media_allowed(self, event: RoomMessageMedia, room_config: RoomConfig) -> bool:
        """Check if media type is allowed in room."""
        try:
            if not hasattr(event, 'msgtype'):
                return False
            
            return event.msgtype in room_config.allowed_content_types
            
        except Exception as e:
            logger.error(f"Media check failed: {str(e)}")
            return True  # Default to allow
    
    async def _apply_media_restriction(self, user_id: str, room_id: str, event_id: str):
        """Apply media restriction."""
        try:
            decision = ModerationDecision(
                event_id=event_id,
                room_id=room_id,
                user_id=user_id,
                action=ModerationAction.REDACT,
                reason="Media type not allowed in this room",
                confidence=1.0,
                ai_responses=[],
                trust_score=0.5,
                expires_at=None,
                escalate_to_human=False,
                metadata={'media_restriction': True}
            )
            
            await self._apply_moderation_decision(decision)
            
        except Exception as e:
            logger.error(f"Media restriction failed: {str(e)}")
    
    async def _handle_user_join(self, room: MatrixRoom, event: RoomMemberEvent):
        """Handle new user joining room."""
        try:
            user_id = event.state_key
            trust_score = await self._get_user_trust_score(user_id, room.room_id)
            
            # Welcome message for new users
            if trust_score < 0.3:
                welcome_message = f"👋 Welcome {user_id}!\n"
                welcome_message += "Please review our community guidelines and be respectful.\n"
                welcome_message += "Your messages will be monitored initially to ensure community safety."
                
                await self.client.room_send(
                    room.room_id,
                    "m.room.message",
                    {
                        "msgtype": "m.notice",
                        "body": welcome_message
                    }
                )
            
        except Exception as e:
            logger.error(f"User join handling failed: {str(e)}")
    
    async def _handle_user_departure(self, room: MatrixRoom, event: RoomMemberEvent):
        """Handle user leaving/being removed from room."""
        try:
            user_id = event.state_key
            
            # Clean up user data
            cache_key = f"{user_id}:{room.room_id}"
            if cache_key in self.user_trust_cache:
                del self.user_trust_cache[cache_key]
            
            rate_key = f"{user_id}:{room.room_id}"
            if rate_key in self.rate_limiters:
                del self.rate_limiters[rate_key]
            
        except Exception as e:
            logger.error(f"User departure handling failed: {str(e)}")
    
    async def _load_room_configurations(self):
        """Load room configurations from database/config."""
        # Placeholder - would load from database
        default_config = RoomConfig(
            room_id="",
            moderation_level="moderate",
            auto_moderation=True,
            trust_threshold=0.3,
            allowed_content_types=["m.text", "m.image", "m.file"],
            rate_limits={"messages_per_minute": 10},
            custom_rules=[],
            moderator_users=[],
            escalation_room=None
        )
        
        # Apply to all monitored rooms
        for room_id in self.config.get('monitored_rooms', []):
            self.room_configs[room_id] = default_config
            self.room_configs[room_id].room_id = room_id
            self.monitored_rooms.add(room_id)
    
    async def _join_monitored_rooms(self):
        """Join all monitored rooms."""
        for room_id in self.monitored_rooms:
            try:
                await self.client.join(room_id)
                logger.info(f"Joined room: {room_id}")
            except Exception as e:
                logger.error(f"Failed to join room {room_id}: {str(e)}")
    
    async def _log_moderation_decision(self, decision: ModerationDecision):
        """Log moderation decision for audit purposes."""
        # Placeholder - would log to database
        logger.info(f"Moderation logged: {decision.action.value} for {decision.user_id}")
    
    async def _log_redaction(self, room_id: str, event: RoomRedactionEvent):
        """Log redaction event for audit purposes."""
        # Placeholder - would log to database
        logger.info(f"Redaction logged: {event.redacts} in {room_id}")
    
    # Public API methods
    
    async def get_room_stats(self, room_id: str) -> Dict[str, Any]:
        """Get moderation statistics for a room."""
        try:
            room_moderations = [d for d in self.active_moderations.values() 
                              if d.room_id == room_id]
            
            return {
                'room_id': room_id,
                'active_moderations': len(room_moderations),
                'moderation_breakdown': {
                    action.value: len([d for d in room_moderations if d.action == action])
                    for action in ModerationAction
                },
                'avg_trust_score': sum(d.trust_score for d in room_moderations) / len(room_moderations) if room_moderations else 0.5
            }
            
        except Exception as e:
            logger.error(f"Room stats failed: {str(e)}")
            return {}
    
    async def get_global_metrics(self) -> Dict[str, Any]:
        """Get global moderation metrics."""
        try:
            avg_response_time = (sum(self.metrics['response_times']) / len(self.metrics['response_times']) 
                               if self.metrics['response_times'] else 0.0)
            
            return {
                **self.metrics,
                'avg_response_time': avg_response_time,
                'active_moderations': len(self.active_moderations),
                'monitored_rooms': len(self.monitored_rooms),
                'cached_trust_scores': len(self.user_trust_cache)
            }
            
        except Exception as e:
            logger.error(f"Global metrics failed: {str(e)}")
            return {}