from django.urls import path

from .views import GoogleLocationSearchView

app_name = "service"


urlpatterns = [
    path("location-search/", GoogleLocationSearchView.as_view(), name="location_search"),
]

