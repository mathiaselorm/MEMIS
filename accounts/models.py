from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier for authentication.
    """
    def create_user(self, email, password=None, user_role=3, first_name=None, last_name=None, phone_number=None, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        if not password:
            raise ValueError(_('The Password must be set'))

        email = self.normalize_email(email)
        user = self.model(email=email, user_role=user_role, first_name=first_name, last_name=last_name, phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, first_name=None, last_name=None, phone_number=None, **extra_fields):
        """
        Create and save a Superuser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)  # Superuser should always be active

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, first_name=first_name, last_name=last_name, phone_number=phone_number, user_role=1, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    class UseRole(models.IntegerChoices):
        SUPERADMIN = 1, 'Superadmin'
        ADMIN = 2, 'Admin'
        TECHNICIAN = 3, 'Technician'

    first_name = models.CharField(_('first name'), max_length=30, unique=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True, null=True)
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(_('phone number'), max_length=20, blank=True, null=True)
    user_role = models.PositiveSmallIntegerField(choices=UseRole.choices, default=UseRole.TECHNICIAN)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)  # Django handles login updates
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']

    objects = CustomUserManager()

    class Meta:
        app_label = 'accounts'
        db_table = 'custom_user'
        verbose_name = _('user')
        verbose_name_plural = _('users')
        indexes = [
            models.Index(fields=['email'], name='email_idx')
        ]
    
    def __str__(self):
        return self.get_full_name()
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

class AuditLog(models.Model):
    ACTION_CHOICES = (
        ('create', 'Create User'),
        ('update', 'Update User'),
        ('delete', 'Delete User'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('assign_role', 'Assign Role'),
        ('revoke_role', 'Revoke Role'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)  # The user performing the action
    action = models.CharField(max_length=15, choices=ACTION_CHOICES)
    target_user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='target_user', null=True, blank=True)  # Target user being acted on
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(null=True, blank=True)  # Optional details about the action

    class Meta:
        verbose_name = _('audit log')
        verbose_name_plural = _('audit logs')

    def __str__(self):
        return f'{self.user} performed {self.action} on {self.target_user or "N/A"} at {self.timestamp}'
