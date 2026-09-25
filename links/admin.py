from django.contrib import admin
from .models import Link

@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'type', 'is_clean', 'watched_at', 'created_at')
    list_filter = ('is_clean', 'type', 'created_at', 'watched_at')
    search_fields = ('title', 'url', 'video_id', 'user__email')
    ordering = ('-created_at',)
