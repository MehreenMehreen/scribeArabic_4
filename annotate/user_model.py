from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

class ScribeUserManager(BaseUserManager):
    def create_user(self, email, name, fullname, password=None, is_public=True, **extra_fields):
        
        email = self.normalize_email(email)
        name = name.lower()
        user = self.model(email=email, name=name, fullname=fullname, is_public=is_public, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, fullname, password=None, is_public=False, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        return self.create_user(email, name, fullname, password, is_public, **extra_fields)

class ScribeUser(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    fullname = models.CharField(max_length=255)
    is_public = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = ScribeUserManager()

    USERNAME_FIELD = 'name'
    REQUIRED_FIELDS = ['fullname', 'email']

    def __str__(self):
        return self.name
