from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from autoslug import AutoSlugField
from model_utils.models import StatusModel, SoftDeletableModel, TimeStampedModel
from model_utils import Choices
from model_utils.managers import QueryManager
from auditlog.registry import auditlog
from cloudinary.models import CloudinaryField
from django.db.models import Q, UniqueConstraint


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
    objects = models.Manager()
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
        on_delete=models.CASCADE,
        related_name='assets'
    )
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


    objects = models.Manager()  # The default manager
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


    def __str__(self):
        return self.name or "Unnamed Asset"
    

# Register models with auditlog
auditlog.register(Asset)
auditlog.register(Department)
