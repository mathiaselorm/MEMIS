from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils.text import slugify
import uuid
from auditlog.registry import auditlog
from auditlog.models import AuditlogHistoryField
from dirtyfields import DirtyFieldsMixin 


User = get_user_model()

class AssetStatus(models.TextChoices):
    ACTIVE = 'active', _('Active')
    INACTIVE = 'inactive', _('Inactive')
    REPAIR = 'repair', _('Under Maintenance')
    DECOMMISSIONED = 'decommissioned', _('Decommissioned')

class DepartmentStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    PUBLISHED = 'published', 'Published'
    
    

class Department(DirtyFieldsMixin, models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    head = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='head_of_department')
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=DepartmentStatus.choices, default=DepartmentStatus.DRAFT)
    is_draft = models.BooleanField(default=False)  # Track if the department is in draft status

    def __str__(self):
        return self.name
    
    @property
    def total_assets(self):
        return self.assets.count()

    @property
    def total_active_assets(self):
        return self.assets.filter(status='active').count()

    @property
    def total_archive_assets(self):
        return self.assets.filter(is_archived=True).count()

    @property
    def total_assets_under_maintenance(self):
        return self.assets.filter(status='repair').count()

    @property
    def total_commissioned_assets(self):
        return self.assets.filter(commission_date__isnull=False).count()

    @property
    def total_decommissioned_assets(self):
        return self.assets.filter(status='decommissioned').count()
    

class Asset(DirtyFieldsMixin, models.Model):  # Include DirtyFieldsMixin
    name = models.CharField(max_length=255)
    device_type = models.CharField(max_length=255, null=True, blank=True)
    embossment_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=AssetStatus.choices, default=AssetStatus.ACTIVE)
    department = models.ForeignKey(Department, related_name='assets', on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    model = models.CharField(max_length=100, null=True, blank=True)
    manufacturer = models.CharField(max_length=100, null=True, blank=True)
    serial_number = models.CharField(max_length=100, unique=True)
    embossment_date = models.DateField(null=True, blank=True)
    manufacturing_date = models.DateField(null=True, blank=True)
    description = models.TextField()
    image = models.ImageField(upload_to='assets/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    commission_date = models.DateField(null=True, blank=True)
    decommission_date = models.DateField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assets')
    is_draft = models.BooleanField(default=False)  # New field to track if the asset is in draft
    history = AuditlogHistoryField()

    def __str__(self):
        return f"{self.name} - {self.embossment_id}"

    def change_status(self, new_status, reason=''):
        if not self.is_draft:  # Only change status if not in draft
            self.status = new_status
            self.save()
        else:
            raise ValueError("Cannot change status of a draft asset.")
        
    def delete(self, *args, **kwargs):
        """
        Override the delete method to implement soft delete (archiving).
        """
        self.is_archived = True
        self.save(update_fields=['is_archived'])

class ActionType(models.TextChoices):
    CREATE = 'create', _('Create')
    UPDATE = 'update', _('Update')
    DELETE = 'delete', _('Delete')


class ActionLog(models.Model):
    action = models.CharField(max_length=10, choices=ActionType.choices, help_text=_("The type of action performed."))
    asset = models.ForeignKey('Asset', on_delete=models.CASCADE, related_name="action_logs", help_text=_("The asset that the action was performed on."))
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="action_logs", help_text=_("The user who performed the action."))
    timestamp = models.DateTimeField(auto_now_add=True, help_text=_("The time the action was logged."))
    changes = models.TextField(help_text=_("A detailed description of what was changed."))
    reason = models.TextField(help_text=_("The reason for the change."), blank=True)

    def __str__(self):
        return f"{self.action} on {self.timestamp} by {self.performed_by}"


# Register models with auditlog
auditlog.register(Asset)
auditlog.register(Department)
