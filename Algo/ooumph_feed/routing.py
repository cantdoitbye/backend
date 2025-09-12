from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from django.urls import path

# Import consumers
from analytics_dashboard.consumers import (
    AnalyticsDashboardConsumer,
    MetricsConsumer
)

# WebSocket URL patterns
websocket_urlpatterns = [
    path('ws/analytics/dashboard/', AnalyticsDashboardConsumer.as_asgi()),
    path('ws/analytics/metrics/<str:metric_name>/', MetricsConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    # HTTP requests
    "http": get_asgi_application(),
    
    # WebSocket requests
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
