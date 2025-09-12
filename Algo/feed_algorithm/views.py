from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
import json
import hashlib
from datetime import timedelta
from typing import List, Dict, Any

# Core Feed Generation
class FeedGenerator:
    """
    Core feed generation engine that orchestrates different scoring algorithms.
    """
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.cache_ttl = getattr(settings, 'FEED_CACHE_TTL', 3600)  # 1 hour default
    
    def generate_feed(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Generate a personalized feed for the user.
        """
        cache_key = f"feed:user:{self.user_id}:limit:{limit}:offset:{offset}"
        
        # Check cache first
        cached_feed = cache.get(cache_key)
        if cached_feed:
            return cached_feed
        
        # Generate fresh feed
        feed_items = self._generate_fresh_feed(limit, offset)
        
        # Cache the result
        cache.set(cache_key, feed_items, self.cache_ttl)
        
        return feed_items
    
    def _generate_fresh_feed(self, limit: int, offset: int) -> Dict[str, Any]:
        """
        Generate a fresh feed using the composition algorithm.
        """
        start_time = timezone.now()
        
        # Default composition ratios (configurable)
        composition = {
            'personal_connections': 0.40,
            'interest_based': 0.25,
            'trending_content': 0.15,
            'discovery_content': 0.10,
            'community_content': 0.05,
            'product_content': 0.05
        }
        
        # Calculate items per category
        items_per_category = {}
        for category, ratio in composition.items():
            items_per_category[category] = int(limit * ratio)
        
        # Mock feed generation (replace with actual scoring logic)
        feed_items = []
        item_id = offset + 1
        
        for category, count in items_per_category.items():
            for i in range(count):
                feed_items.append({
                    'id': item_id,
                    'category': category,
                    'title': f'Sample {category} content {item_id}',
                    'content_type': 'post',
                    'score': 1.0 - (i * 0.1),
                    'created_at': (timezone.now() - timedelta(minutes=i*10)).isoformat(),
                    'author': f'user_{item_id % 10}'
                })
                item_id += 1
        
        # Sort by score (descending)
        feed_items.sort(key=lambda x: x['score'], reverse=True)
        
        generation_time = (timezone.now() - start_time).total_seconds() * 1000
        
        return {
            'items': feed_items,
            'composition': composition,
            'metadata': {
                'user_id': self.user_id,
                'total_items': len(feed_items),
                'generation_time_ms': generation_time,
                'cache_ttl': self.cache_ttl,
                'generated_at': timezone.now().isoformat()
            }
        }

# API Views
@csrf_exempt
@require_http_methods(["GET"])
@login_required
def user_feed(request):
    """
    Get personalized feed for authenticated user.
    """
    try:
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))
        
        # Validate parameters
        limit = min(max(limit, 1), 100)  # Between 1 and 100
        offset = max(offset, 0)  # Non-negative
        
        # Generate feed
        generator = FeedGenerator(request.user.id)
        feed_data = generator.generate_feed(limit, offset)
        
        return JsonResponse({
            'success': True,
            'data': feed_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET", "POST"])
@login_required
def feed_composition(request):
    """
    Get or update feed composition settings.
    """
    if request.method == 'GET':
        # Return current composition (mock data for now)
        composition = {
            'personal_connections': 0.40,
            'interest_based': 0.25,
            'trending_content': 0.15,
            'discovery_content': 0.10,
            'community_content': 0.05,
            'product_content': 0.05
        }
        
        return JsonResponse({
            'success': True,
            'data': {
                'composition': composition,
                'user_id': request.user.id
            }
        })
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_composition = data.get('composition', {})
            
            # Validate composition ratios sum to 1.0
            total_ratio = sum(new_composition.values())
            if abs(total_ratio - 1.0) > 0.01:  # Allow small floating point errors
                return JsonResponse({
                    'success': False,
                    'error': f'Composition ratios must sum to 1.0, got {total_ratio}'
                }, status=400)
            
            # In a real implementation, save to database
            # For now, just return success
            
            return JsonResponse({
                'success': True,
                'data': {
                    'composition': new_composition,
                    'updated_at': timezone.now().isoformat()
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON in request body'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def trending_content(request):
    """
    Get trending content across different time windows.
    """
    try:
        time_window = request.GET.get('window', '24h')
        content_type = request.GET.get('type', 'all')
        limit = int(request.GET.get('limit', 20))
        
        # Mock trending data
        trending_items = []
        for i in range(limit):
            trending_items.append({
                'id': f'trending_{i+1}',
                'title': f'Trending {content_type} #{i+1}',
                'content_type': content_type if content_type != 'all' else ['post', 'community', 'product'][i % 3],
                'trend_score': 100 - (i * 5),
                'engagement_rate': 0.95 - (i * 0.03),
                'velocity': 150 - (i * 8),
                'time_window': time_window
            })
        
        return JsonResponse({
            'success': True,
            'data': {
                'trending_items': trending_items,
                'time_window': time_window,
                'content_type': content_type,
                'generated_at': timezone.now().isoformat()
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def analytics_dashboard(request):
    """
    Get feed performance analytics.
    """
    try:
        # Mock analytics data
        analytics_data = {
            'feed_performance': {
                'avg_generation_time_ms': 125.5,
                'cache_hit_rate': 0.78,
                'total_feeds_generated': 15420,
                'error_rate': 0.02
            },
            'engagement_metrics': {
                'avg_items_per_feed': 47.3,
                'avg_engagement_rate': 0.23,
                'top_performing_categories': [
                    {'category': 'personal_connections', 'engagement_rate': 0.41},
                    {'category': 'trending_content', 'engagement_rate': 0.33},
                    {'category': 'interest_based', 'engagement_rate': 0.28}
                ]
            },
            'composition_effectiveness': {
                'personal_connections': 0.89,
                'interest_based': 0.76,
                'trending_content': 0.82,
                'discovery_content': 0.54,
                'community_content': 0.67,
                'product_content': 0.45
            },
            'generated_at': timezone.now().isoformat()
        }
        
        return JsonResponse({
            'success': True,
            'data': analytics_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
