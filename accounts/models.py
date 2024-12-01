from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier for authentication.
    """
    def create_user(self, email, password=None, user_role=None, first_name=None, last_name=None, phone_number=None, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))

        if not first_name:
            raise ValueError(_('The First Name must be set'))

        email = self.normalize_email(email)
        user_role = user_role or CustomUser.UserRole.TECHNICIAN

        user = self.model(email=email, user_role=user_role, first_name=first_name, last_name=last_name, phone_number=phone_number, **extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, first_name, last_name=None, phone_number=None, **extra_fields):
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

        return self.create_user(email, password, user_role=CustomUser.UserRole.SUPERADMIN, first_name=first_name, last_name=last_name, phone_number=phone_number, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    class UserRole(models.IntegerChoices):
        SUPERADMIN = 1, _('Superadmin')
        ADMIN = 2, _('Admin')
        TECHNICIAN = 3, _('Technician')

    first_name = models.CharField(_('First Name'), max_length=150)
    last_name = models.CharField(_('Last Name'), max_length=150, blank=True, null=True)
    email = models.EmailField(_('Email Address'), unique=True)
    phone_number = models.CharField(_('Phone Number'), max_length=20, blank=True, null=True)
    user_role = models.PositiveSmallIntegerField(_('User Role'), choices=UserRole.choices, default=UserRole.TECHNICIAN)
    date_joined = models.DateTimeField(_('Date Joined'), default=timezone.now)
    last_login = models.DateTimeField(_('Last Login'), null=True, blank=True)
    is_staff = models.BooleanField(_('Staff Status'), default=False)
    is_active = models.BooleanField(_('Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

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
        full_name = f"{self.first_name} {self.last_name or ''}".strip()
        return full_name

    def get_short_name(self):
        return self.first_name

    def has_perm(self, perm, obj=None):
        return self.is_superuser or self.is_staff

    def has_module_perms(self, app_label):
        return self.is_superuser or self.is_staff

class AuditLog(models.Model):
    class ActionChoices(models.TextChoices):
        CREATE = 'create', _('Create User')
        UPDATE = 'update', _('Update User')
        DELETE = 'delete', _('Delete User')
        LOGIN = 'login', _('Login')
        LOGOUT = 'logout', _('Logout')
        ASSIGN_ROLE = 'assign_role', _('Assign Role')
        REVOKE_ROLE = 'revoke_role', _('Revoke Role')

    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='action_user', verbose_name=_('User'))  # The user performing the action
    action = models.CharField(_('Action'), max_length=15, choices=ActionChoices.choices)
    target_user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='target_user', verbose_name=_('Target User'))  # Target user being acted on
    timestamp = models.DateTimeField(_('Timestamp'), auto_now_add=True)
    details = models.TextField(_('Details'), null=True, blank=True)

    class Meta:
        verbose_name = _('audit log')
        verbose_name_plural = _('audit logs')
        ordering = ['-timestamp']

    def __str__(self):
        user = self.user.get_full_name() if self.user else _('Unknown User')
        target = self.target_user.get_full_name() if self.target_user else _('N/A')
        return _('%(user)s performed %(action)s on %(target)s at %(timestamp)s') % {
            'user': user,
            'action': self.get_action_display(),
            'target': target,
            'timestamp': self.timestamp,
        }
