# TrustStream Configuration Module
# This module manages configuration settings for TrustStream v4.4

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class AIServiceConfig:
    """Configuration for AI service providers."""
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None
    huggingface_api_token: Optional[str] = None
    cohere_api_key: Optional[str] = None
    
    # Service endpoints
    openai_base_url: str = "https://api.openai.com/v1"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    claude_base_url: str = "https://api.anthropic.com/v1"
    huggingface_base_url: str = "https://api-inference.huggingface.co"
    cohere_base_url: str = "https://api.cohere.ai/v1"
    
    # Model configurations
    openai_models: Dict[str, str] = field(default_factory=lambda: {
        'chat': 'gpt-4-turbo-preview',
        'embedding': 'text-embedding-3-large',
        'moderation': 'text-moderation-latest'
    })
    
    gemini_models: Dict[str, str] = field(default_factory=lambda: {
        'chat': 'gemini-pro',
        'vision': 'gemini-pro-vision'
    })
    
    claude_models: Dict[str, str] = field(default_factory=lambda: {
        'chat': 'claude-3-opus-20240229',
        'reasoning': 'claude-3-sonnet-20240229'
    })
    
    huggingface_models: Dict[str, str] = field(default_factory=lambda: {
        'sentiment': 'cardiffnlp/twitter-roberta-base-sentiment-latest',
        'toxicity': 'unitary/toxic-bert-base',
        'hate_speech': 'unitary/unbiased-toxic-roberta',
        'embedding': 'sentence-transformers/all-MiniLM-L6-v2'
    })
    
    cohere_models: Dict[str, str] = field(default_factory=lambda: {
        'embedding': 'embed-english-v3.0',
        'classification': 'embed-multilingual-v3.0'
    })


@dataclass
class TrustPyramidConfig:
    """Configuration for Trust Pyramid Calculator."""
    # Layer weights (must sum to 1.0)
    iq_weight: float = 0.35
    appeal_weight: float = 0.25
    social_weight: float = 0.25
    humanity_weight: float = 0.15
    
    # Score thresholds
    high_trust_threshold: float = 0.8
    medium_trust_threshold: float = 0.6
    low_trust_threshold: float = 0.4
    
    # Calculation parameters
    activity_decay_days: int = 30
    minimum_activities_for_score: int = 5
    max_score: float = 1.0
    min_score: float = 0.0
    
    # Component weights within each layer
    iq_components: Dict[str, float] = field(default_factory=lambda: {
        'content_quality': 0.4,
        'technical_accuracy': 0.3,
        'problem_solving': 0.3
    })
    
    appeal_components: Dict[str, float] = field(default_factory=lambda: {
        'user_satisfaction': 0.5,
        'engagement_quality': 0.3,
        'helpfulness': 0.2
    })
    
    social_components: Dict[str, float] = field(default_factory=lambda: {
        'community_contribution': 0.4,
        'collaboration': 0.3,
        'leadership': 0.3
    })
    
    humanity_components: Dict[str, float] = field(default_factory=lambda: {
        'empathy': 0.4,
        'ethical_behavior': 0.4,
        'inclusivity': 0.2
    })


@dataclass
class ModerationConfig:
    """Configuration for AI moderation engine."""
    # Confidence thresholds for actions
    auto_approve_threshold: float = 0.9
    auto_remove_threshold: float = 0.8
    human_review_threshold: float = 0.6
    
    # Agent assignment rules
    primary_agents: list = field(default_factory=lambda: [
        'community_guardian',
        'content_quality',
        'transparency_moderator'
    ])
    
    specialized_agents: Dict[str, list] = field(default_factory=lambda: {
        'harassment': ['harassment_detector', 'bias_prevention'],
        'misinformation': ['misinformation_guardian', 'fact_checker'],
        'elections': ['election_integrity', 'bias_prevention'],
        'crisis': ['crisis_management', 'community_guardian']
    })
    
    # Response time targets (in seconds)
    real_time_threshold: float = 2.0
    standard_threshold: float = 30.0
    complex_threshold: float = 300.0
    
    # Content analysis settings
    analyze_text: bool = True
    analyze_images: bool = True
    analyze_videos: bool = False  # Requires additional setup
    analyze_links: bool = True
    
    # Language support
    supported_languages: list = field(default_factory=lambda: [
        'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ko'
    ])


@dataclass
class TransparencyConfig:
    """Configuration for transparency and explainability engine."""
    # Explanation detail levels
    user_explanation_max_words: int = 100
    technical_explanation_max_words: int = 500
    audit_explanation_max_words: int = 1000
    
    # Explanation components to include
    include_confidence_score: bool = True
    include_trust_score: bool = True
    include_agent_reasoning: bool = True
    include_similar_cases: bool = True
    include_appeal_process: bool = True
    
    # Audit trail settings
    retain_decisions_days: int = 2555  # 7 years for compliance
    anonymize_after_days: int = 365
    
    # Supported explanation formats
    supported_formats: list = field(default_factory=lambda: [
        'text', 'json', 'html', 'pdf'
    ])


class TrustStreamConfig:
    """Main TrustStream configuration class."""
    
    def __init__(self, env_file: Optional[str] = None):
        """Initialize configuration from environment variables or file."""
        self.ai_services = AIServiceConfig()
        self.trust_pyramid = TrustPyramidConfig()
        self.moderation = ModerationConfig()
        self.transparency = TransparencyConfig()
        
        # Load configuration from environment
        self._load_from_environment()
        
        # Validate configuration
        self._validate_config()
        
        logger.info("TrustStream configuration loaded successfully")
    
    def _load_from_environment(self):
        """Load configuration from environment variables."""
        # AI Service API Keys
        self.ai_services.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.ai_services.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.ai_services.claude_api_key = os.getenv('CLAUDE_API_KEY')
        self.ai_services.huggingface_api_token = os.getenv('HUGGINGFACE_API_TOKEN')
        self.ai_services.cohere_api_key = os.getenv('COHERE_API_KEY')
        
        # Override default model configurations if specified
        if os.getenv('OPENAI_CHAT_MODEL'):
            self.ai_services.openai_models['chat'] = os.getenv('OPENAI_CHAT_MODEL')
        
        if os.getenv('GEMINI_CHAT_MODEL'):
            self.ai_services.gemini_models['chat'] = os.getenv('GEMINI_CHAT_MODEL')
        
        # Trust pyramid configuration overrides
        if os.getenv('TRUST_IQ_WEIGHT'):
            self.trust_pyramid.iq_weight = float(os.getenv('TRUST_IQ_WEIGHT'))
        
        if os.getenv('TRUST_APPEAL_WEIGHT'):
            self.trust_pyramid.appeal_weight = float(os.getenv('TRUST_APPEAL_WEIGHT'))
        
        if os.getenv('TRUST_SOCIAL_WEIGHT'):
            self.trust_pyramid.social_weight = float(os.getenv('TRUST_SOCIAL_WEIGHT'))
        
        if os.getenv('TRUST_HUMANITY_WEIGHT'):
            self.trust_pyramid.humanity_weight = float(os.getenv('TRUST_HUMANITY_WEIGHT'))
        
        # Moderation configuration overrides
        if os.getenv('AUTO_APPROVE_THRESHOLD'):
            self.moderation.auto_approve_threshold = float(os.getenv('AUTO_APPROVE_THRESHOLD'))
        
        if os.getenv('AUTO_REMOVE_THRESHOLD'):
            self.moderation.auto_remove_threshold = float(os.getenv('AUTO_REMOVE_THRESHOLD'))
    
    def _validate_config(self):
        """Validate configuration settings."""
        # Validate trust pyramid weights sum to 1.0
        total_weight = (
            self.trust_pyramid.iq_weight +
            self.trust_pyramid.appeal_weight +
            self.trust_pyramid.social_weight +
            self.trust_pyramid.humanity_weight
        )
        
        if abs(total_weight - 1.0) > 0.001:
            logger.warning(f"Trust pyramid weights sum to {total_weight}, not 1.0. Normalizing...")
            # Normalize weights
            self.trust_pyramid.iq_weight /= total_weight
            self.trust_pyramid.appeal_weight /= total_weight
            self.trust_pyramid.social_weight /= total_weight
            self.trust_pyramid.humanity_weight /= total_weight
        
        # Validate thresholds are in correct order
        if not (
            self.moderation.auto_approve_threshold > 
            self.moderation.auto_remove_threshold > 
            self.moderation.human_review_threshold
        ):
            raise ValueError("Moderation thresholds must be in descending order")
        
        # Warn about missing API keys
        missing_keys = []
        if not self.ai_services.openai_api_key:
            missing_keys.append('OPENAI_API_KEY')
        if not self.ai_services.gemini_api_key:
            missing_keys.append('GEMINI_API_KEY')
        if not self.ai_services.claude_api_key:
            missing_keys.append('CLAUDE_API_KEY')
        if not self.ai_services.huggingface_api_token:
            missing_keys.append('HUGGINGFACE_API_TOKEN')
        if not self.ai_services.cohere_api_key:
            missing_keys.append('COHERE_API_KEY')
        
        if missing_keys:
            logger.warning(f"Missing API keys: {', '.join(missing_keys)}. Some features may be limited.")
    
    def get_active_ai_services(self) -> list:
        """Get list of AI services with valid API keys."""
        active_services = []
        
        if self.ai_services.openai_api_key:
            active_services.append('openai')
        if self.ai_services.gemini_api_key:
            active_services.append('gemini')
        if self.ai_services.claude_api_key:
            active_services.append('claude')
        if self.ai_services.huggingface_api_token:
            active_services.append('huggingface')
        if self.ai_services.cohere_api_key:
            active_services.append('cohere')
        
        return active_services
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive data)."""
        return {
            'trust_pyramid': {
                'iq_weight': self.trust_pyramid.iq_weight,
                'appeal_weight': self.trust_pyramid.appeal_weight,
                'social_weight': self.trust_pyramid.social_weight,
                'humanity_weight': self.trust_pyramid.humanity_weight,
                'thresholds': {
                    'high': self.trust_pyramid.high_trust_threshold,
                    'medium': self.trust_pyramid.medium_trust_threshold,
                    'low': self.trust_pyramid.low_trust_threshold
                }
            },
            'moderation': {
                'thresholds': {
                    'auto_approve': self.moderation.auto_approve_threshold,
                    'auto_remove': self.moderation.auto_remove_threshold,
                    'human_review': self.moderation.human_review_threshold
                },
                'supported_languages': self.moderation.supported_languages,
                'content_analysis': {
                    'text': self.moderation.analyze_text,
                    'images': self.moderation.analyze_images,
                    'videos': self.moderation.analyze_videos,
                    'links': self.moderation.analyze_links
                }
            },
            'transparency': {
                'explanation_limits': {
                    'user': self.transparency.user_explanation_max_words,
                    'technical': self.transparency.technical_explanation_max_words,
                    'audit': self.transparency.audit_explanation_max_words
                },
                'retention_days': self.transparency.retain_decisions_days,
                'supported_formats': self.transparency.supported_formats
            },
            'active_ai_services': self.get_active_ai_services()
        }