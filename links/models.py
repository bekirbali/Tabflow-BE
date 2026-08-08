import uuid
from django.db import models
from django.conf import settings

class Link(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='links'
    )
    url = models.TextField()
    video_id = models.CharField(max_length=11, blank=True, null=True)
    type = models.CharField(
        max_length=50,
        choices=[
            ('video', 'Video'),
            ('article', 'Article'),
            ('code', 'Code Repository'),
            ('general', 'General Link')
        ],
        default='general'
    )
    title = models.TextField(blank=True, null=True)
    source_name = models.CharField(max_length=255, blank=True, null=True)
    is_clean = models.BooleanField(default=False)
    liked = models.BooleanField(default=False)
    bookmarked = models.BooleanField(default=False)
    duration = models.CharField(max_length=50, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    curator = models.CharField(max_length=100, default='@feed_master')
    category = models.CharField(max_length=100, default='Tech')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title or self.video_id or self.url} ({self.user.email})"
