import uuid
import secrets
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email address is required')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = models.CharField(max_length=150, blank=True, null=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    api_key = models.CharField(max_length=64, unique=True, db_index=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        if not self.api_key:
            self.api_key = secrets.token_hex(24)
        if not self.username and self.email:
            self.username = self.email.split('@')[0]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email
