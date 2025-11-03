# TrustStream AI Agent Manager
# This module manages the deployment and coordination of 15 specialized AI moderation agents

import logging
from typing import Dict, Any, List, Optional, Type
from datetime import datetime
import asyncio

from agentic.models import Agent, AgentCommunityAssignment
from agentic.services.agent_service import AgentService
from community.models import Community

from .base_agent import BaseAIAgent
from .community_guardian import CommunityGuardianAgent
from .content_quality import ContentQualityAgent
from .transparency_moderator import TransparencyModeratorAgent
from .harassment_detector import HarassmentDetectorAgent
from .misinformation_guardian import MisinformationGuardianAgent
from .bias_prevention import BiasPreventionAgent
from .engagement_optimizer import EngagementOptimizerAgent
from .election_integrity import ElectionIntegrityAgent
from .privacy_protection import PrivacyProtectionAgent
from .crisis_management import CrisisManagementAgent
from .fact_checker import FactCheckerAgent
from .sentiment_analyzer import SentimentAnalyzerAgent
from .spam_detector import SpamDetectorAgent
from .image_moderator import ImageModeratorAgent
from .multilingual_moderator import MultilingualModeratorAgent

logger = logging.getLogger(__name__)


class AIAgentManager:
    """
    AI Agent Manager for TrustStream v4.4
    
    This class manages the deployment, coordination, and performance monitoring
    of 15 specialized AI moderation agents. It integrates with the existing
    agentic module to leverage agent infrastructure while adding TrustStream-specific
    capabilities.
    
    Key Responsibilities:
    - Deploy appropriate agents based on community characteristics
    - Coordinate multi-agent decision making
    - Monitor agent performance and effectiveness
    - Handle agent failover and load balancing
    - Integrate with existing agent memory and logging systems
    """
    
    # Registry of all available TrustStream AI agents
    AGENT_REGISTRY: Dict[str, Type[BaseAIAgent]] = {
        'community_guardian': CommunityGuardianAgent,
        'content_quality': ContentQualityAgent,
        'transparency_moderator': TransparencyModeratorAgent,
        'harassment_detector': HarassmentDetectorAgent,
        'misinformation_guardian': MisinformationGuardianAgent,
        'bias_prevention': BiasPreventionAgent,
        'engagement_optimizer': EngagementOptimizerAgent,
        'election_integrity': ElectionIntegrityAgent,
        'privacy_protection': PrivacyProtectionAgent,
        'crisis_management': CrisisManagementAgent,
        'fact_checker': FactCheckerAgent,
        'sentiment_analyzer': SentimentAnalyzerAgent,
        'spam_detector': SpamDetectorAgent,
        'image_moderator': ImageModeratorAgent,
        'multilingual_moderator': MultilingualModeratorAgent
    }
    
    # Default agent deployment configurations
    DEFAULT_AGENT_CONFIGS = {
        'small_community': [
            'community_guardian',
            'content_quality',
            'transparency_moderator',
            'harassment_detector',
            'spam_detector'
        ],
        'medium_community': [
            'community_guardian',
            'content_quality',
            'transparency_moderator',
            'harassment_detector',
            'misinformation_guardian',
            'bias_prevention',
            'engagement_optimizer',
            'spam_detector',
            'sentiment_analyzer'
        ],
        'large_community': [
            'community_guardian',
            'content_quality',
            'transparency_moderator',
            'harassment_detector',
            'misinformation_guardian',
            'bias_prevention',
            'engagement_optimizer',
            'election_integrity',
            'privacy_protection',
            'crisis_management',
            'fact_checker',
            'sentiment_analyzer',
            'spam_detector',
            'image_moderator',
            'multilingual_moderator'
        ]
    }
    
    def __init__(self, config):
        """Initialize the AI Agent Manager with configuration."""
        self.config = config
        self.agent_service = AgentService()
        self.active_agents: Dict[str, Dict[str, BaseAIAgent]] = {}  # community_id -> agent_type -> agent_instance
        self.agent_performance: Dict[str, Dict[str, Any]] = {}  # community_id -> agent_type -> performance_metrics
        
        logger.info("AI Agent Manager initialized")
    
    async def deploy_agents_for_community(
        self, 
        community_id: str, 
        community_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Deploy appropriate AI agents for a community based on its characteristics.
        
        Args:
            community_id: The community to deploy agents for
            community_analysis: Analysis of community characteristics
            
        Returns:
            List of deployed agent information
        """
        try:
            # Determine which agents to deploy based on community analysis
            agents_to_deploy = self._determine_agents_for_community(community_analysis)
            
            deployed_agents = []
            
            for agent_type in agents_to_deploy:
                # Create TrustStream AI agent instance
                agent_instance = await self._create_agent_instance(
                    agent_type=agent_type,
                    community_id=community_id,
                    community_analysis=community_analysis
                )
                
                # Register with existing agentic system
                existing_agent = await self._register_with_agentic_system(
                    agent_type=agent_type,
                    community_id=community_id,
                    agent_instance=agent_instance
                )
                
                # Store in active agents registry
                if community_id not in self.active_agents:
                    self.active_agents[community_id] = {}
                
                self.active_agents[community_id][agent_type] = agent_instance
                
                deployed_agents.append({
                    'agent_type': agent_type,
                    'agent_id': existing_agent.uid,
                    'capabilities': agent_instance.get_capabilities(),
                    'status': 'deployed',
                    'deployment_time': datetime.utcnow().isoformat()
                })
                
                logger.info(f"Deployed {agent_type} agent for community {community_id}")
            
            return deployed_agents
            
        except Exception as e:
            logger.error(f"Failed to deploy agents for community {community_id}: {str(e)}")
            raise
    
    async def coordinate_moderation_decision(
        self, 
        content_data: Dict[str, Any], 
        trust_score: float
    ) -> Dict[str, Any]:
        """
        Coordinate multiple AI agents to make a moderation decision.
        
        Args:
            content_data: The content to moderate
            trust_score: Trust score of the content author
            
        Returns:
            Coordinated moderation decision
        """
        try:
            community_id = content_data.get('community_id')
            if not community_id or community_id not in self.active_agents:
                raise ValueError(f"No agents deployed for community {community_id}")
            
            # Get relevant agents for this content type
            relevant_agents = self._get_relevant_agents(content_data, community_id)
            
            # Collect decisions from all relevant agents
            agent_decisions = []
            
            for agent_type, agent_instance in relevant_agents.items():
                try:
                    decision = await agent_instance.analyze_content(
                        content=content_data,
                        trust_score=trust_score,
                        context=await self._get_agent_context(agent_type, community_id)
                    )
                    
                    agent_decisions.append({
                        'agent_type': agent_type,
                        'decision': decision,
                        'confidence': decision.get('confidence', 0.5),
                        'reasoning': decision.get('reasoning', '')
                    })
                    
                except Exception as e:
                    logger.error(f"Agent {agent_type} failed to analyze content: {str(e)}")
                    # Continue with other agents
            
            # Coordinate final decision using ensemble method
            final_decision = await self._coordinate_agent_decisions(
                agent_decisions=agent_decisions,
                content_data=content_data,
                trust_score=trust_score
            )
            
            # Update agent performance metrics
            await self._update_agent_performance(community_id, agent_decisions, final_decision)
            
            return final_decision
            
        except Exception as e:
            logger.error(f"Failed to coordinate moderation decision: {str(e)}")
            raise
    
    async def get_agent_performance(self, community_id: str) -> Dict[str, Any]:
        """
        Get performance metrics for all agents in a community.
        
        Args:
            community_id: The community to get metrics for
            
        Returns:
            Dictionary containing agent performance metrics
        """
        try:
            if community_id not in self.agent_performance:
                return {'message': 'No performance data available'}
            
            community_performance = self.agent_performance[community_id]
            
            # Calculate aggregate metrics
            total_decisions = sum(
                metrics.get('decisions_made', 0) 
                for metrics in community_performance.values()
            )
            
            average_confidence = sum(
                metrics.get('average_confidence', 0) 
                for metrics in community_performance.values()
            ) / len(community_performance) if community_performance else 0
            
            average_response_time = sum(
                metrics.get('average_response_time', 0) 
                for metrics in community_performance.values()
            ) / len(community_performance) if community_performance else 0
            
            return {
                'community_id': community_id,
                'total_agents': len(community_performance),
                'total_decisions': total_decisions,
                'average_confidence': round(average_confidence, 3),
                'average_response_time_ms': round(average_response_time, 2),
                'agent_details': community_performance,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get agent performance: {str(e)}")
            raise
    
    async def handle_agent_failure(self, community_id: str, agent_type: str) -> bool:
        """
        Handle agent failure by attempting recovery or failover.
        
        Args:
            community_id: The community where the agent failed
            agent_type: The type of agent that failed
            
        Returns:
            True if recovery was successful, False otherwise
        """
        try:
            logger.warning(f"Handling failure for {agent_type} in community {community_id}")
            
            # Attempt to restart the agent
            if await self._restart_agent(community_id, agent_type):
                logger.info(f"Successfully restarted {agent_type} in community {community_id}")
                return True
            
            # If restart fails, try to deploy a backup agent
            if await self._deploy_backup_agent(community_id, agent_type):
                logger.info(f"Successfully deployed backup for {agent_type} in community {community_id}")
                return True
            
            # If all else fails, mark agent as failed and continue with remaining agents
            await self._mark_agent_failed(community_id, agent_type)
            logger.error(f"Failed to recover {agent_type} in community {community_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error handling agent failure: {str(e)}")
            return False
    
    # Private helper methods
    
    def _determine_agents_for_community(self, community_analysis: Dict[str, Any]) -> List[str]:
        """Determine which agents to deploy based on community characteristics."""
        size = community_analysis.get('size', 'medium')
        risk_level = community_analysis.get('risk_level', 'medium')
        content_types = community_analysis.get('content_types', ['text'])
        languages = community_analysis.get('languages', ['en'])
        
        # Start with default configuration
        if size == 'small':
            agents = self.DEFAULT_AGENT_CONFIGS['small_community'].copy()
        elif size == 'large':
            agents = self.DEFAULT_AGENT_CONFIGS['large_community'].copy()
        else:
            agents = self.DEFAULT_AGENT_CONFIGS['medium_community'].copy()
        
        # Add specialized agents based on characteristics
        if risk_level == 'high':
            if 'crisis_management' not in agents:
                agents.append('crisis_management')
            if 'privacy_protection' not in agents:
                agents.append('privacy_protection')
        
        if 'images' in content_types and 'image_moderator' not in agents:
            agents.append('image_moderator')
        
        if len(languages) > 1 and 'multilingual_moderator' not in agents:
            agents.append('multilingual_moderator')
        
        return agents
    
    async def _create_agent_instance(
        self, 
        agent_type: str, 
        community_id: str, 
        community_analysis: Dict[str, Any]
    ) -> BaseAIAgent:
        """Create an instance of the specified agent type."""
        if agent_type not in self.AGENT_REGISTRY:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        agent_class = self.AGENT_REGISTRY[agent_type]
        agent_instance = agent_class(
            config=self.config,
            community_id=community_id,
            community_analysis=community_analysis
        )
        
        await agent_instance.initialize()
        return agent_instance
    
    async def _register_with_agentic_system(
        self, 
        agent_type: str, 
        community_id: str, 
        agent_instance: BaseAIAgent
    ) -> Agent:
        """Register the TrustStream agent with the existing agentic system."""
        # Create agent record in existing system
        agent_data = {
            'name': f"TrustStream {agent_type.replace('_', ' ').title()}",
            'agent_type': 'MODERATOR',  # Use existing agent type
            'capabilities': agent_instance.get_capabilities(),
            'description': agent_instance.get_description(),
            'created_by_uid': 'truststream_system'
        }
        
        # Use existing agent service to create agent
        existing_agent = await self.agent_service.create_agent(**agent_data)
        
        # Assign to community
        assignment_data = {
            'agent_uid': existing_agent.uid,
            'community_uid': community_id,
            'role': 'MODERATOR',
            'assigned_by_uid': 'truststream_system',
            'permissions': agent_instance.get_capabilities()
        }
        
        await self.agent_service.assign_agent_to_community(**assignment_data)
        
        return existing_agent
    
    def _get_relevant_agents(
        self, 
        content_data: Dict[str, Any], 
        community_id: str
    ) -> Dict[str, BaseAIAgent]:
        """Get agents relevant to the content type and context."""
        if community_id not in self.active_agents:
            return {}
        
        all_agents = self.active_agents[community_id]
        relevant_agents = {}
        
        # Always include core agents
        core_agents = ['community_guardian', 'content_quality', 'transparency_moderator']
        for agent_type in core_agents:
            if agent_type in all_agents:
                relevant_agents[agent_type] = all_agents[agent_type]
        
        # Add specialized agents based on content characteristics
        content_type = content_data.get('type', 'text')
        content_text = content_data.get('content', '')
        
        # Check for harassment indicators
        harassment_keywords = ['hate', 'attack', 'threat', 'abuse']
        if any(keyword in content_text.lower() for keyword in harassment_keywords):
            if 'harassment_detector' in all_agents:
                relevant_agents['harassment_detector'] = all_agents['harassment_detector']
        
        # Check for misinformation indicators
        misinfo_keywords = ['fake', 'conspiracy', 'hoax', 'debunked']
        if any(keyword in content_text.lower() for keyword in misinfo_keywords):
            if 'misinformation_guardian' in all_agents:
                relevant_agents['misinformation_guardian'] = all_agents['misinformation_guardian']
        
        # Add image moderator for image content
        if content_type == 'image' and 'image_moderator' in all_agents:
            relevant_agents['image_moderator'] = all_agents['image_moderator']
        
        # Add spam detector for potential spam
        spam_indicators = ['buy now', 'click here', 'limited time', 'act fast']
        if any(indicator in content_text.lower() for indicator in spam_indicators):
            if 'spam_detector' in all_agents:
                relevant_agents['spam_detector'] = all_agents['spam_detector']
        
        return relevant_agents
    
    async def _get_agent_context(self, agent_type: str, community_id: str) -> Dict[str, Any]:
        """Get context information for an agent."""
        # This would integrate with existing agent memory system
        return {
            'community_id': community_id,
            'agent_type': agent_type,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _coordinate_agent_decisions(
        self, 
        agent_decisions: List[Dict[str, Any]], 
        content_data: Dict[str, Any], 
        trust_score: float
    ) -> Dict[str, Any]:
        """Coordinate multiple agent decisions into a final decision."""
        if not agent_decisions:
            return {
                'action': 'approve',
                'confidence': 0.5,
                'reasoning': 'No agent decisions available'
            }
        
        # Weighted voting based on agent confidence and specialization
        action_votes = {'approve': 0, 'flag': 0, 'remove': 0, 'warn': 0}
        total_confidence = 0
        reasoning_parts = []
        
        for decision in agent_decisions:
            action = decision['decision'].get('action', 'approve')
            confidence = decision['confidence']
            agent_type = decision['agent_type']
            
            # Weight votes by confidence and agent specialization
            weight = confidence
            if agent_type in ['community_guardian', 'content_quality']:
                weight *= 1.2  # Core agents get higher weight
            
            if action in action_votes:
                action_votes[action] += weight
            
            total_confidence += confidence
            reasoning_parts.append(f"{agent_type}: {decision['reasoning']}")
        
        # Determine final action
        final_action = max(action_votes, key=action_votes.get)
        final_confidence = total_confidence / len(agent_decisions) if agent_decisions else 0.5
        
        # Adjust based on trust score
        if trust_score > 0.8 and final_action == 'remove':
            final_action = 'flag'  # High trust users get benefit of doubt
            final_confidence *= 0.9
        elif trust_score < 0.3 and final_action == 'approve':
            final_action = 'flag'  # Low trust users get extra scrutiny
            final_confidence *= 0.8
        
        return {
            'action': final_action,
            'confidence': round(final_confidence, 3),
            'reasoning': '; '.join(reasoning_parts),
            'agent_votes': action_votes,
            'trust_score_adjustment': trust_score
        }
    
    async def _update_agent_performance(
        self, 
        community_id: str, 
        agent_decisions: List[Dict[str, Any]], 
        final_decision: Dict[str, Any]
    ):
        """Update performance metrics for agents."""
        if community_id not in self.agent_performance:
            self.agent_performance[community_id] = {}
        
        for decision in agent_decisions:
            agent_type = decision['agent_type']
            
            if agent_type not in self.agent_performance[community_id]:
                self.agent_performance[community_id][agent_type] = {
                    'decisions_made': 0,
                    'total_confidence': 0,
                    'total_response_time': 0,
                    'correct_decisions': 0
                }
            
            metrics = self.agent_performance[community_id][agent_type]
            metrics['decisions_made'] += 1
            metrics['total_confidence'] += decision['confidence']
            
            # Calculate averages
            metrics['average_confidence'] = metrics['total_confidence'] / metrics['decisions_made']
    
    async def _restart_agent(self, community_id: str, agent_type: str) -> bool:
        """Attempt to restart a failed agent."""
        try:
            # Remove failed agent
            if community_id in self.active_agents and agent_type in self.active_agents[community_id]:
                del self.active_agents[community_id][agent_type]
            
            # Create new instance
            community_analysis = {'size': 'medium', 'risk_level': 'medium'}  # Default for restart
            agent_instance = await self._create_agent_instance(
                agent_type=agent_type,
                community_id=community_id,
                community_analysis=community_analysis
            )
            
            # Store new instance
            if community_id not in self.active_agents:
                self.active_agents[community_id] = {}
            
            self.active_agents[community_id][agent_type] = agent_instance
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to restart agent {agent_type}: {str(e)}")
            return False
    
    async def _deploy_backup_agent(self, community_id: str, agent_type: str) -> bool:
        """Deploy a backup agent to replace a failed one."""
        # For now, just attempt restart
        return await self._restart_agent(community_id, agent_type)
    
    async def _mark_agent_failed(self, community_id: str, agent_type: str):
        """Mark an agent as failed in the performance metrics."""
        if community_id not in self.agent_performance:
            self.agent_performance[community_id] = {}
        
        if agent_type not in self.agent_performance[community_id]:
            self.agent_performance[community_id][agent_type] = {}
        
        self.agent_performance[community_id][agent_type]['status'] = 'failed'
        self.agent_performance[community_id][agent_type]['failed_at'] = datetime.utcnow().isoformat()