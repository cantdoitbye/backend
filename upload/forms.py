from django import forms
from .models import UploadFiles

class FileUploadForm(forms.ModelForm):
    class Meta:
        model = UploadFiles
        fields = ['file']
