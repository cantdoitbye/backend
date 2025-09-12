"""
Content type registry for the Ooumph Feed Algorithm system.

Provides a centralized system for registering and managing
extensible content types.
"""

from typing import Dict, List, Type, Any
from django.apps import apps
import structlog

logger = structlog.get_logger(__name__)


class ContentTypeRegistry:
    """
    Registry for managing content types in the feed system.
    
    Allows dynamic registration of content types and provides
    a unified interface for content type operations.
    """
    
    def __init__(self):
        self._registered_types: Dict[str, Type] = {}
        self._type_metadata: Dict[str, Dict[str, Any]] = {}
    
    def register_content_type(
        self, 
        content_type: Type, 
        name: str = None,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Register a new content type.
        
        Args:
            content_type: The content type class
            name: Optional custom name (defaults to class name)
            metadata: Optional metadata dictionary
        
        Returns:
            Success status
        """
        try:
            type_name = name or content_type.__name__.lower()
            
            self._registered_types[type_name] = content_type
            self._type_metadata[type_name] = metadata or {}
            
            logger.info(
                "Content type registered",
                type_name=type_name,
                class_name=content_type.__name__
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to register content type",
                content_type=content_type.__name__,
                error=str(e)
            )
            return False
    
    def get_content_type(self, name: str) -> Type:
        """
        Get a registered content type by name.
        
        Args:
            name: Content type name
        
        Returns:
            Content type class or None
        """
        return self._registered_types.get(name)
    
    def get_all_content_types(self) -> Dict[str, Type]:
        """
        Get all registered content types.
        
        Returns:
            Dictionary of type name -> type class
        """
        return self._registered_types.copy()
    
    def get_content_type_metadata(self, name: str) -> Dict[str, Any]:
        """
        Get metadata for a content type.
        
        Args:
            name: Content type name
        
        Returns:
            Metadata dictionary
        """
        return self._type_metadata.get(name, {})
    
    def is_registered(self, name: str) -> bool:
        """
        Check if a content type is registered.
        
        Args:
            name: Content type name
        
        Returns:
            True if registered
        """
        return name in self._registered_types
    
    def unregister_content_type(self, name: str) -> bool:
        """
        Unregister a content type.
        
        Args:
            name: Content type name
        
        Returns:
            Success status
        """
        try:
            if name in self._registered_types:
                del self._registered_types[name]
                del self._type_metadata[name]
                
                logger.info(
                    "Content type unregistered",
                    type_name=name
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(
                "Failed to unregister content type",
                type_name=name,
                error=str(e)
            )
            return False


# Global registry instance
content_type_registry = ContentTypeRegistry()


def register_default_content_types():
    """
    Register the default content types (Post, Community, Product).
    
    Called during app initialization.
    """
    try:
        # Import models
        from feed_algorithm.models import Post, Community, Product
        
        # Register Post
        content_type_registry.register_content_type(
            Post,
            name='post',
            metadata={
                'description': 'Social media posts with text and media',
                'fields': ['content', 'media_urls', 'share_count', 'comment_count'],
                'scoring_factors': ['engagement', 'recency', 'connections'],
                'feed_weight': 1.0
            }
        )
        
        # Register Community
        content_type_registry.register_content_type(
            Community,
            name='community',
            metadata={
                'description': 'Communities and groups',
                'fields': ['member_count', 'is_public', 'category'],
                'scoring_factors': ['member_count', 'engagement', 'category_match'],
                'feed_weight': 0.8
            }
        )
        
        # Register Product
        content_type_registry.register_content_type(
            Product,
            name='product',
            metadata={
                'description': 'Marketplace products and services',
                'fields': ['price', 'currency', 'availability', 'rating_average'],
                'scoring_factors': ['rating', 'availability', 'price_range'],
                'feed_weight': 0.6
            }
        )
        
        logger.info("Default content types registered successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to register default content types: {e}")
        return False


def get_content_type_info() -> Dict[str, Any]:
    """
    Get information about all registered content types.
    
    Returns:
        Dictionary with content type information
    """
    info = {
        'registered_types': {},
        'total_count': len(content_type_registry._registered_types)
    }
    
    for name, content_type in content_type_registry.get_all_content_types().items():
        metadata = content_type_registry.get_content_type_metadata(name)
        
        info['registered_types'][name] = {
            'class_name': content_type.__name__,
            'module': content_type.__module__,
            'metadata': metadata
        }
    
    return info


def create_content_instance(type_name: str, **kwargs) -> Any:
    """
    Create an instance of a registered content type.
    
    Args:
        type_name: Name of the content type
        **kwargs: Arguments for content creation
    
    Returns:
        Created content instance or None
    """
    try:
        content_type = content_type_registry.get_content_type(type_name)
        if not content_type:
            logger.error(f"Content type '{type_name}' not registered")
            return None
        
        instance = content_type(**kwargs)
        
        logger.debug(
            "Content instance created",
            type_name=type_name,
            instance_id=getattr(instance, 'id', None)
        )
        
        return instance
        
    except Exception as e:
        logger.error(
            "Failed to create content instance",
            type_name=type_name,
            error=str(e)
        )
        return None
