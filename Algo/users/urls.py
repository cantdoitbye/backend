from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'profiles', views.UserProfileViewSet, basename='userprofile')
router.register(r'connections', views.ConnectionViewSet, basename='connection')
router.register(r'interests', views.InterestViewSet, basename='interest')
router.register(r'user-interests', views.UserInterestViewSet, basename='userinterest')
router.register(r'interest-collections', views.InterestCollectionViewSet, basename='interestcollection')

urlpatterns = [
    path('', include(router.urls)),
]