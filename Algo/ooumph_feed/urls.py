from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

def health_check(request):
    """Comprehensive health check endpoint for production monitoring."""
    from django.db import connection
    from django.core.cache import cache
    import redis
    
    health_data = {
        'status': 'healthy',
        'service': 'Ooumph Feed Algorithm 1.0',
        'version': '1.0.0',
        'components': {}
    }
    
    # Database health check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_data['components']['database'] = 'healthy'
    except Exception as e:
        health_data['components']['database'] = f'unhealthy: {str(e)}'
        health_data['status'] = 'unhealthy'
    
    # Cache health check
    try:
        cache.set('health_check', 'test', 30)
        if cache.get('health_check') == 'test':
            health_data['components']['cache'] = 'healthy'
        else:
            health_data['components']['cache'] = 'unhealthy: cache test failed'
            health_data['status'] = 'unhealthy'
    except Exception as e:
        health_data['components']['cache'] = f'unhealthy: {str(e)}'
        health_data['status'] = 'unhealthy'
    
    # Redis health check (if configured)
    try:
        if hasattr(settings, 'REDIS_URL'):
            import redis
            r = redis.from_url(settings.REDIS_URL)
            r.ping()
            health_data['components']['redis'] = 'healthy'
    except Exception as e:
        health_data['components']['redis'] = f'unhealthy: {str(e)}'
        health_data['status'] = 'degraded'
    
    status_code = 200 if health_data['status'] == 'healthy' else 503
    return JsonResponse(health_data, status=status_code)

def ready_check(request):
    """Readiness check for container orchestration."""
    return JsonResponse({
        'status': 'ready',
        'service': 'Ooumph Feed Algorithm 1.0'
    })

urlpatterns = [
    # Health and monitoring endpoints
    path('health/', health_check, name='health_check'),
    path('ready/', ready_check, name='ready_check'),
    
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include('feed_algorithm.urls')),
    path('api/', include('analytics_dashboard.urls')),
    
    # Analytics dashboard (admin interface)
    path('', RedirectView.as_view(url='/admin/analytics/', permanent=False)),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Add debug toolbar in development
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns

# Custom error handlers for production
handler404 = 'django.views.defaults.page_not_found'
handler500 = 'django.views.defaults.server_error'
handler403 = 'django.views.defaults.permission_denied'
handler400 = 'django.views.defaults.bad_request'
