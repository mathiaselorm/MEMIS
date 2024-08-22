from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import EmailValidator

class CustomUserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifiers for authentication.
    """
    def create_user(self, email, password=None, first_name="", last_name="",  phone_number= "", **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        email_validator = EmailValidator()
        email_validator(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name, phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password,  first_name="", last_name="",  phone_number= "", **extra_fields):
        """
        Create and save a Superuser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, first_name, last_name, phone_number, **extra_fields)

    

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True, validators=[EmailValidator()])
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    phone_number = models.CharField(_('phone number'), max_length=20, blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(default=timezone.now)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']  

    objects = CustomUserManager()

    class Meta:
        app_label = 'accounts'
        db_table = 'custom_user'

    def __str__(self):
        return f'{self.email}'  


class UserProfile(models.Model):
    """
    User profile model to store additional information that doesn't fit in the CustomUser model.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(_("Biography"), null=True, blank=True)
    birth_date = models.DateField(_("Birth Date"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created at"), default=timezone.now)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    def __str__(self):
        return f'Profile of {self.user.email}'
