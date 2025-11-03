import json
from django.conf import settings

from minio import Minio
from minio.error import S3Error

from upload.models import UploadFiles
from upload.utils import extract_hostname
import mimetypes
import os
from graphql import GraphQLError

from django.core.files.storage import default_storage

def generate_presigned_url(image_id):
    try:
        if image_id is None or image_id == "":
            return None
        image = UploadFiles.objects.get(id=image_id)
        client = Minio(
            endpoint=extract_hostname(settings.AWS_S3_ENDPOINT_URL),
            access_key=settings.AWS_ACCESS_KEY_ID,
            secret_key=settings.AWS_SECRET_ACCESS_KEY,
            secure=True
        )
        try:
            url = client.presigned_get_object(settings.AWS_STORAGE_BUCKET_NAME, image.file.name)
            return url
        except Exception as error:
            return image.file.url
        
    except UploadFiles.DoesNotExist:
        return None
    except S3Error as e:
        raise e
    


def generate_file_info(image_id):
    try:
        if image_id is None or image_id == "":
            return {
                'url': None,
                'file_extension': None,
                'file_type': None,
                'file_size': None
            }
        image = UploadFiles.objects.get(id=image_id)
        file_name = image.file.name
        file_url = None
        file_size = 0
        try:
            file_url = default_storage.url(file_name) if default_storage.exists(file_name) else None
            # file_size = default_storage.size(file_name)
        except Exception as e:
            file_url = f"https://{os.getenv('AWS_S3_CUSTOM_DOMAIN')}/{file_name}"
            # file_size = image.file.size if hasattr(image.file, 'size') else 0
        file_extension = file_name.split('.')[-1] if '.' in file_name else 'unknown'
        mime_type = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'

        return {
            'url': file_url if file_url else f"https://{os.getenv('AWS_S3_CUSTOM_DOMAIN')}/{file_name}",
            'file_extension': file_extension,
            'file_type': mime_type,
            'file_size': file_size
        }
    except UploadFiles.DoesNotExist:
        return {
            'url': None,
            'file_extension': None,
            'file_type': None,
            'file_size': None
        }
    except Exception as e:
        # Initialize file_url and file_name to avoid reference before assignment
        file_url = None
        file_name = ""
        print(f"Error in generate_file_info: {e}")
        return {
            'url': None,
            'file_extension': None,
            'file_type': None,
            'file_size': None
        }


def get_valid_image(image_id: str):
    """
    Validates if the given image_id exists in the UploadFiles model.

    :param image_id: The image ID to validate.
    :return: The valid image instance if found.
    :raises GraphQLError: If the image ID is invalid or does not exist.
    """
    # If image_id is None or empty, just return None without raising an error
    if not image_id or image_id == "":
        return None

    try:
        # Check if the image_id is a valid numeric string
        if not isinstance(image_id, str) or not image_id.isdigit():
            raise GraphQLError(f"Invalid file ID format: {image_id}. File ID must be a numeric string.")

        # Try to get the image
        return UploadFiles.objects.get(id=image_id)
    except UploadFiles.DoesNotExist:
        raise GraphQLError(f"File with ID {image_id} does not exist.")
    except Exception as e:
        # Log the error but don't raise it
        print(f"Error validating image_id {image_id}: {e}")
        raise GraphQLError(f"Error validating file ID {image_id}: {str(e)}")
