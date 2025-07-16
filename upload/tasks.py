import uuid
import os
import logging
from celery import shared_task
from django.core.files.storage import default_storage
from django.conf import settings
from .models import UploadFiles
from django.utils import timezone
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

@shared_task
def process_file(file_data):
    temp_file_path = file_data['file_path']
    original_name = file_data['file_name']
    file_size = file_data['file_size']
    content_type = file_data['content_type']

    # Generate a random file name
    new_name = f"{uuid.uuid4().hex}{os.path.splitext(original_name)[1]}"
    file_url = f"https://bucket.debuginit.com/ooumph/uploads/{new_name}"

    try:
        # Save the file to the bucket
        file_path = f'ooumph/uploads/{new_name}'
        with open(temp_file_path, 'rb') as file:
            default_storage.save(file_path, ContentFile(file.read()))
        logger.info(f"File saved to bucket at {file_path}")

        # Save file information in the database
        uploaded_file = UploadedFile(
            file=file_path,
            file_name=new_name,
            file_size=file_size,
            content_type=content_type,
            file_url=file_url,
            uploaded_at=timezone.now()
        )
        uploaded_file.save()
        logger.info(f"File information saved in database with ID {uploaded_file.id}")

        # Optionally, clean up temporary file
        os.remove(temp_file_path)

        return {
            'id': uploaded_file.id,
            'file_url': file_url,
            'file_name': new_name,
            'file_size': uploaded_file.file_size,
            'content_type': uploaded_file.content_type,
            'uploaded_at': uploaded_file.uploaded_at.isoformat(),
        }
    except ValidationError as e:
        logger.error(f"Validation error: {e.messages}")
        return {'errors': e.messages}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {'errors': str(e)}
