from rest_framework import serializers
from .models import Link

class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = (
            'id', 'url', 'video_id', 'type', 'title', 'source_name',
            'is_clean', 'liked', 'bookmarked', 'duration', 'metadata',
            'curator', 'category', 'created_at'
        )
        read_only_fields = ('id', 'created_at')
