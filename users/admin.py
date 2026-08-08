from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'is_staff', 'is_active', 'api_key')
    search_fields = ('email', 'username')
    readonly_fields = ('api_key',)

