from rest_framework import serializers
from .models import UploadFiles
from .utils import get_user_from_token

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadFiles
        fields = ['id', 'username','uploaded_at']

class MultipleImageUploadSerializer(serializers.Serializer):
    files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True
    )
    uploaded_images = ImageSerializer(many=True, read_only=True)

    def create(self, validated_data):
        files = validated_data.get('files', [])
        request = self.context['request']
        user=get_user_from_token(request)
        images = []
        for file in files:
            image = UploadFiles.objects.create(file=file, username=user.username)
            images.append(image)

        return {'uploaded_files': ImageSerializer(images, many=True).data}
