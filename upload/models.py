from django.db import models
from django.conf import settings

class UploadFiles(models.Model):
    username = models.CharField(max_length=999)
    file = models.FileField(upload_to='feeds/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name
