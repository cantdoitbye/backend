from django.urls import path
from .views import UploadMultipleImagesView,PrivateImageView


urlpatterns = [
    path('upload/', UploadMultipleImagesView.as_view(), name='upload_image'),
    path('image/<int:image_id>/', PrivateImageView.as_view(), name='private_image'),
]
