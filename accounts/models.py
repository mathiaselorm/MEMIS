from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import EmailValidator

class CustomUserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier for authentication.
    """
    def create_user(self, email, password=None, user_type=3, first_name="", last_name="", phone_number="", **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        if not password:
            raise ValueError(_('The Password must be set'))

        email = self.normalize_email(email)
        user = self.model(email=email, user_type=user_type, first_name=first_name, last_name=last_name, phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, first_name="", last_name="", phone_number="", **extra_fields):
        """
        Create and save a Superuser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields['is_staff'] is not True or extra_fields['is_superuser'] is not True:
            raise ValueError(_('Superuser must have is_staff=True and is_superuser=True.'))

        return self.create_user(email, password, first_name=first_name, last_name=last_name, phone_number=phone_number, user_type=1, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    class UserType(models.IntegerChoices):
        SUPERADMIN = 1, 'Superadmin'
        ADMIN = 2, 'Admin'
        TECHNICIAN = 3, 'Technician'

    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    phone_number = models.CharField(_('phone number'), max_length=20, blank=True, null=True)
    user_type = models.PositiveSmallIntegerField(choices=UserType.choices, default=UserType.TECHNICIAN)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(default=timezone.now)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    class Meta:
        app_label = 'accounts'
        db_table = 'custom_user'
        indexes = [
            models.Index(fields=['email'], name='email_idx')
        ]
    
    def __str__(self):
        return f"{self.email} ({self.get_full_name()})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"