from django.urls import path
from . import views

urlpatterns = [
    path('feed/', views.user_feed, name='user_feed'),
    path('feed/composition/', views.feed_composition, name='feed_composition'),
    path('trending/', views.trending_content, name='trending_content'),
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
]
