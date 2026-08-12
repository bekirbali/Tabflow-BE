from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email',)


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    list_display = ('email', 'username', 'is_staff', 'is_active', 'api_key')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('email', 'username')
    ordering = ('email',)
    readonly_fields = ('api_key', 'last_login', 'date_joined')

    # Fields shown when editing an existing user
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Kişisel Bilgiler', {'fields': ('username', 'first_name', 'last_name')}),
        ('İzinler', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Önemli Tarihler', {'fields': ('last_login', 'date_joined')}),
        ('API', {'fields': ('api_key',)}),
    )

    # Fields shown when ADDING a new user — uses proper password hashing
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_active', 'is_staff'),
        }),
    )
