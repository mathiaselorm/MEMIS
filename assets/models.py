
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from autoslug import AutoSlugField
from model_utils.models import StatusModel, SoftDeletableModel, TimeStampedModel
from model_utils import Choices
from model_utils.managers import QueryManager
from auditlog.registry import auditlog
from cloudinary.models import CloudinaryField
from django.db.models import Q, UniqueConstraint
from django.core.exceptions import ValidationError
from dateutil import rrule 

User = get_user_model()

class ConditionalValidationMixin:
    def save(self, *args, **kwargs):
        if self.status != self.STATUS.draft:
            self.full_clean()
        super().save(*args, **kwargs)

class Department(ConditionalValidationMixin, StatusModel, SoftDeletableModel, TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)
    slug = AutoSlugField(populate_from='name', unique=True, max_length=255)
    head = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='head_of_department',
        blank=True,
        null=True
    )
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    STATUS = Choices('draft', 'published')

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['name'],
                condition=Q(status='published'),
                name='unique_department_name_when_published'
            )
        ]
    
    # Custom managers
    published = QueryManager(status=STATUS.published)
    draft = QueryManager(status=STATUS.draft)
        
    def publish(self):
        if self.status != self.STATUS.published:
            self.status = self.STATUS.published
            self.save()

    def __str__(self):
        return self.name or 'Unknown Department'

    @property
    def total_assets(self):
        return self.assets.count()

    @property
    def total_active_assets(self):
        return self.assets.filter(operational_status='active').count()

    @property
    def total_archive_assets(self):
        return self.assets.filter(is_removed=True).count()

    @property
    def total_assets_under_maintenance(self):
        return self.assets.filter(operational_status='under_maintenance').count()

    @property
    def total_commissioned_assets(self):
        return self.assets.filter(commission_date__isnull=False).count()

    @property
    def total_decommissioned_assets(self):
        return self.assets.filter(operational_status='decommissioned').count()



class Asset(ConditionalValidationMixin, StatusModel, SoftDeletableModel, TimeStampedModel):
    name = models.CharField(max_length=255)
    device_type = models.CharField(max_length=255, blank=True, null=True)
    embossment_id = models.CharField(max_length=100)
    department = models.ForeignKey(
        Department,
        related_name='assets',
        on_delete=models.CASCADE
    )
    OPERATIONAL_STATUS = Choices(
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('under_maintenance', 'Under Maintenance'),
        ('decommissioned', 'Decommissioned')
    )
    operational_status = models.CharField(
        max_length=20,
        choices=OPERATIONAL_STATUS,
        default=OPERATIONAL_STATUS.inactive
    )
    quantity = models.IntegerField(default=1)
    model = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100)
    embossment_date = models.DateField()
    manufacturing_date = models.DateField()
    description = models.TextField(blank=True, null=True)
    image = CloudinaryField(
        'image',
        blank=True,
        null=True,
        resource_type='image',
        folder='assets',
        unique_filename=True
    )
    commission_date = models.DateField()
    decommission_date = models.DateField(blank=True, null=True)
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assets'
    )
    added_by_name = models.CharField(max_length=255, null=True, editable=False)
    STATUS = Choices('draft', 'published')  # Workflow status

    class Meta:
        verbose_name = _('Asset')
        verbose_name_plural = _('Assets')
        constraints = [
            UniqueConstraint(
                fields=['embossment_id'],
                condition=Q(status='published'),
                name='unique_embossment_id_when_published'
            ),
            UniqueConstraint(
                fields=['serial_number'],
                condition=Q(status='published'),
                name='unique_assets_serial_number_when_published'
            )
        ]

    published = QueryManager(status=STATUS.published)
    draft = QueryManager(status=STATUS.draft)
    active = QueryManager(operational_status='active')
    inactive = QueryManager(operational_status='inactive')
    under_maintenance = QueryManager(operational_status='under_maintenance')
    decommissioned = QueryManager(operational_status='decommissioned')
    
    def publish(self):
        if self.status != self.STATUS.published:
            self.status = self.STATUS.published
            self.save()

    def save(self, *args, **kwargs):
        if self.added_by:
            self.added_by_name = self.added_by.get_full_name()
        else:
            self.added_by_name = 'Unknown'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name or "Unnamed Asset"
    
    

class AssetActivity(SoftDeletableModel, TimeStampedModel):
    ACTIVITY_TYPE_CHOICES = Choices(
        ('maintenance', 'Maintenance'),
        ('repair', 'Repair'),
        ('calibration', 'Calibration'),
    )

    asset = models.ForeignKey(
        Asset,
        related_name='activities',
        on_delete=models.CASCADE
    )
    activity_type = models.CharField(
        max_length=20,
        choices=ACTIVITY_TYPE_CHOICES,
        default=ACTIVITY_TYPE_CHOICES.maintenance
    )
    date_time = models.DateTimeField()
    technician = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activities_performed'
    )
    technician_name = models.CharField(max_length=255, editable=False)
    STATUS_CHOICES = Asset.OPERATIONAL_STATUS  # Reuse the choices from Asset model
    pre_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        null=True,
        blank=True
    )
    post_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date_time']
        
    def save(self, *args, **kwargs):
        if self.technician:
            self.technician_name = self.technician.get_full_name()
        else:
            self.technician_name = 'Unknown'
        super().save(*args, **kwargs)
        
    def __str__(self):
        technician_name = self.technician.get_full_name() if self.technician else 'Unknown'
        return f"{self.get_activity_type_display()} on {self.asset.name} by {technician_name}"
    
    

class MaintenanceSchedule(TimeStampedModel):
    FREQUENCY_CHOICES = (
        ('once', 'Once'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    )

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='maintenance_schedules',
        null=True,
        blank=True
    )
    is_general = models.BooleanField(default=False)  # True for general maintenance
    technician = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='maintenance_schedules')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(null=True, blank=True)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='once')
    interval = models.PositiveIntegerField(default=1)  # Interval between recurrences
    until = models.DateTimeField(null=True, blank=True)  # End date for recurring events
    is_active = models.BooleanField(default=True)
    last_notification = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['start_datetime']),
            models.Index(fields=['is_active']),
            models.Index(fields=['last_notification']),
        ]
    
    def clean(self):
        if self.end_datetime and self.end_datetime <= self.start_datetime:
            raise ValidationError("End time must be after the start time.")
        if self.until and self.until < self.start_datetime:
            raise ValidationError("Recurring end date ('until') must be on or after the start time.")
        if self.is_general and self.asset is not None:
            raise ValidationError("A general reminder cannot be linked to a specific asset.")
        if not self.is_general and self.asset is None:
            raise ValidationError("A specific reminder must be linked to an asset.")

    def __str__(self):
        if self.is_general:
            return f"General Maintenance: {self.title}"
        if self.asset:
            return f"{self.title} for {self.asset.name}"
        return f"{self.title}"

    def get_next_occurrences(self, count=1, lookahead_days=1):
        if not self.is_active:
            return []
        
        if self.frequency == 'once':
            if self.start_datetime > datetime.now():
                return [self.start_datetime]
            else:
                return []
        
        freq_map = {
            'daily': rrule.DAILY,
            'weekly': rrule.WEEKLY,
            'monthly': rrule.MONTHLY,
            'yearly': rrule.YEARLY,
        }
        freq = freq_map.get(self.frequency)
        rule = rrule.rrule(
            freq,
            dtstart=self.start_datetime,
            interval=self.interval,
            until=self.until,
        )
        now = datetime.now()
        occurrences = rule.between(now, now + timedelta(days=lookahead_days), inc=True)
        return occurrences[:count]



class Notification(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    link = models.URLField(blank=True, null=True)  # Link to related details
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.username}"

# Register models with auditlog
auditlog.register(Asset)
auditlog.register(Department)
auditlog.register(AssetActivity)
