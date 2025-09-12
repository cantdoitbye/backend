"""
Scoring engine registry for the Ooumph Feed Algorithm system.

Provides a centralized system for registering and managing
modular scoring engines.
"""

from typing import Dict, List, Type, Any, Callable
from abc import ABC, abstractmethod
import structlog

logger = structlog.get_logger(__name__)


class ScoringEngineInterface(ABC):
    """
    Abstract interface for scoring engines.
    """
    
    @abstractmethod
    def calculate_score(self, content_item, user_profile, *args, **kwargs) -> float:
        """
        Calculate score for a content item.
        
        Args:
            content_item: Content to score
            user_profile: User's profile
            *args, **kwargs: Additional arguments
        
        Returns:
            Calculated score (0-100)
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get the engine name.
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Get the engine description.
        """
        pass


class ScoringEngineRegistry:
    """
    Registry for managing scoring engines.
    
    Allows dynamic registration of scoring engines and provides
    a unified interface for scoring operations.
    """
    
    def __init__(self):
        self._engines: Dict[str, ScoringEngineInterface] = {}
        self._engine_metadata: Dict[str, Dict[str, Any]] = {}
    
    def register_engine(
        self, 
        engine: ScoringEngineInterface,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Register a scoring engine.
        
        Args:
            engine: Scoring engine instance
            metadata: Optional metadata dictionary
        
        Returns:
            Success status
        """
        try:
            engine_name = engine.name
            
            self._engines[engine_name] = engine
            self._engine_metadata[engine_name] = metadata or {}
            
            logger.info(
                "Scoring engine registered",
                engine_name=engine_name,
                description=engine.description
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to register scoring engine",
                engine_class=engine.__class__.__name__,
                error=str(e)
            )
            return False
    
    def get_engine(self, name: str) -> ScoringEngineInterface:
        """
        Get a registered scoring engine by name.
        
        Args:
            name: Engine name
        
        Returns:
            Scoring engine instance or None
        """
        return self._engines.get(name)
    
    def get_all_engines(self) -> Dict[str, ScoringEngineInterface]:
        """
        Get all registered scoring engines.
        
        Returns:
            Dictionary of engine name -> engine instance
        """
        return self._engines.copy()
    
    def get_engine_metadata(self, name: str) -> Dict[str, Any]:
        """
        Get metadata for a scoring engine.
        
        Args:
            name: Engine name
        
        Returns:
            Metadata dictionary
        """
        return self._engine_metadata.get(name, {})
    
    def is_registered(self, name: str) -> bool:
        """
        Check if a scoring engine is registered.
        
        Args:
            name: Engine name
        
        Returns:
            True if registered
        """
        return name in self._engines
    
    def score_content(
        self, 
        engine_name: str, 
        content_item, 
        user_profile, 
        *args, 
        **kwargs
    ) -> float:
        """
        Score content using a specific engine.
        
        Args:
            engine_name: Name of the scoring engine
            content_item: Content to score
            user_profile: User's profile
            *args, **kwargs: Additional arguments
        
        Returns:
            Calculated score or 0.0 if engine not found
        """
        engine = self.get_engine(engine_name)
        if not engine:
            logger.warning(
                "Scoring engine not found",
                engine_name=engine_name
            )
            return 0.0
        
        try:
            score = engine.calculate_score(
                content_item, user_profile, *args, **kwargs
            )
            
            logger.debug(
                "Content scored",
                engine_name=engine_name,
                content_id=getattr(content_item, 'id', None),
                user_id=getattr(user_profile, 'user_id', None),
                score=score
            )
            
            return score
            
        except Exception as e:
            logger.error(
                "Scoring failed",
                engine_name=engine_name,
                content_id=getattr(content_item, 'id', None),
                error=str(e)
            )
            return 0.0
    
    def unregister_engine(self, name: str) -> bool:
        """
        Unregister a scoring engine.
        
        Args:
            name: Engine name
        
        Returns:
            Success status
        """
        try:
            if name in self._engines:
                del self._engines[name]
                del self._engine_metadata[name]
                
                logger.info(
                    "Scoring engine unregistered",
                    engine_name=name
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(
                "Failed to unregister scoring engine",
                engine_name=name,
                error=str(e)
            )
            return False


# Global registry instance
scoring_engine_registry = ScoringEngineRegistry()


def register_default_scoring_engines():
    """
    Register the default scoring engines.
    
    Called during app initialization.
    """
    try:
        # Import scoring engines
        from .services import (
            PersonalConnectionsScoringEngine,
            InterestBasedScoringEngine,
            TrendingScoringEngine,
            DiscoveryScoringEngine
        )
        
        # Register Personal Connections Engine
        personal_engine = PersonalConnectionsScoringEngine()
        scoring_engine_registry.register_engine(
            personal_engine,
            metadata={
                'category': 'social',
                'weight': 1.0,
                'factors': ['circle_type', 'interaction_score', 'mutual_connections']
            }
        )
        
        # Register Interest-Based Engine
        interest_engine = InterestBasedScoringEngine()
        scoring_engine_registry.register_engine(
            interest_engine,
            metadata={
                'category': 'personalization',
                'weight': 1.0,
                'factors': ['explicit_interests', 'inferred_interests', 'content_tags']
            }
        )
        
        # Register Trending Engine
        trending_engine = TrendingScoringEngine()
        scoring_engine_registry.register_engine(
            trending_engine,
            metadata={
                'category': 'popularity',
                'weight': 1.0,
                'factors': ['trending_score', 'velocity', 'viral_coefficient']
            }
        )
        
        # Register Discovery Engine
        discovery_engine = DiscoveryScoringEngine()
        scoring_engine_registry.register_engine(
            discovery_engine,
            metadata={
                'category': 'exploration',
                'weight': 1.0,
                'factors': ['quality_score', 'diversity', 'serendipity']
            }
        )
        
        logger.info("Default scoring engines registered successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to register default scoring engines: {e}")
        return False


def get_scoring_engine_info() -> Dict[str, Any]:
    """
    Get information about all registered scoring engines.
    
    Returns:
        Dictionary with scoring engine information
    """
    info = {
        'registered_engines': {},
        'total_count': len(scoring_engine_registry._engines)
    }
    
    for name, engine in scoring_engine_registry.get_all_engines().items():
        metadata = scoring_engine_registry.get_engine_metadata(name)
        
        info['registered_engines'][name] = {
            'name': engine.name,
            'description': engine.description,
            'class_name': engine.__class__.__name__,
            'metadata': metadata
        }
    
    return info


def benchmark_scoring_engines(
    content_item, 
    user_profile, 
    iterations: int = 100
) -> Dict[str, Dict[str, float]]:
    """
    Benchmark all registered scoring engines.
    
    Args:
        content_item: Test content item
        user_profile: Test user profile
        iterations: Number of iterations for timing
    
    Returns:
        Benchmark results dictionary
    """
    import time
    
    results = {}
    
    for name, engine in scoring_engine_registry.get_all_engines().items():
        try:
            # Warm up
            engine.calculate_score(content_item, user_profile)
            
            # Benchmark
            start_time = time.time()
            for _ in range(iterations):
                score = engine.calculate_score(content_item, user_profile)
            end_time = time.time()
            
            total_time = end_time - start_time
            avg_time = total_time / iterations
            
            results[name] = {
                'total_time_seconds': total_time,
                'average_time_ms': avg_time * 1000,
                'iterations': iterations,
                'score': score
            }
            
        except Exception as e:
            logger.error(
                "Benchmark failed for engine",
                engine_name=name,
                error=str(e)
            )
            results[name] = {
                'error': str(e)
            }
    
    return results
