import os
import uuid
import logging
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.uploadhandler import TemporaryFileUploadHandler

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

from minio import Minio
from minio.error import S3Error

from .forms import FileUploadForm
from .tasks import process_file
from .models import UploadFiles
from .serializers import ImageSerializer, MultipleImageUploadSerializer
from .utils import get_user_from_token, extract_hostname


logger = logging.getLogger(__name__)


def check_task_status(request, task_id):
    # Initialize the AsyncResult instance with the task ID
    result = AsyncResult(task_id, backend=settings.CELERY_RESULT_BACKEND)

    # Determine the task status
    if result.ready():
        response = {
            'status': result.status,
            'result': result.result if result.status == 'SUCCESS' else None,
            'error': result.result if result.status == 'FAILURE' else None
        }
    else:
        response = {
            'status': result.status,
            'result': None,
            'error': None
        }

    return JsonResponse(response)


def generate_presigned_url(image_id, user):
    try:
        image = UploadFiles.objects.get(id=image_id)
        client = Minio(
            endpoint=extract_hostname(settings.AWS_S3_ENDPOINT_URL),
            access_key=settings.AWS_ACCESS_KEY_ID,
            secret_key=settings.AWS_SECRET_ACCESS_KEY,
            secure=True
        )
        try:
            url = client.presigned_get_object(settings.AWS_STORAGE_BUCKET_NAME, image.file.name)
        except Exception as error :
            return image.file.url
        
    except UploadFiles.DoesNotExist:
        return None
    except S3Error as e:
        raise e




class UploadMultipleImagesView(generics.CreateAPIView):
    queryset = UploadFiles.objects.all()
    serializer_class = MultipleImageUploadSerializer

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            result = serializer.save()
            return Response({'success':True , 'message':"Files uploaded successfully." , **result})
        except Exception as error:
            return Response({
                "success":False,
                "message":str(error),
            })




class PrivateImageView(APIView):
    def get(self, request, *args, **kwargs):
        image_id = kwargs.get('image_id')
        user = get_user_from_token(request)
        try:
            url = generate_presigned_url(image_id, user)
            if url:
                return HttpResponse(url, content_type='text/plain')
            else:
                return HttpResponse('Image not found', status=404)
        except S3Error as e:
            return HttpResponse(f'Error: {e}', status=500)