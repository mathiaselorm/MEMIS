from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
import uuid






User = get_user_model()

class AssetStatus(models.TextChoices):
    ACTIVE = 'active', _('Active')
    INACTIVE = 'inactive', _('Inactive')
    REPAIR = 'repair', _('Under Maintenance')
    DECOMMISSIONED = 'decommissioned', _('Decommissioned')

class Department(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    head = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='head_of_department')
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:  # Only set the slug when it's not provided.
            self.slug = slugify(self.name)
        super(Department, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def total_assets(self):
        return self.assets.count()

    @property
    def total_active_assets(self):
        return self.assets.filter(status=AssetStatus.ACTIVE).count()

    @property
    def total_archive_assets(self):
        return self.assets.filter(is_archived=True).count()


    @property
    def total_assets_under_maintenance(self):
        return self.assets.filter(status=AssetStatus.REPAIR).count()
    
    @property
    def total_commissioned_assets(self):
        return self.assets.filter(status=AssetStatus.ACTIVE).count()

    @property
    def total_decommissioned_assets(self):
        return self.assets.filter(status=AssetStatus.DECOMMISSIONED).count()

class Asset(models.Model):
    asset_id = models.UUIDField(_("Asset ID"), primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    embossment_id = models.CharField(max_length=100, unique=True)
    device_type = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=AssetStatus.choices, default=AssetStatus.ACTIVE)
    department = models.ForeignKey(Department, related_name='assets', on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    model = models.CharField(max_length=100, null=True, blank=True)
    manufacturer = models.CharField(max_length=100, null=True, blank=True)
    serial_number = models.CharField(max_length=100, unique=True)
    embossment_date = models.DateField(null=True, blank=True)
    manufacturing_date = models.DateField(null=True, blank=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    commission_date = models.DateField(null=True, blank=True)
    decommission_date = models.DateField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assets')

    def __str__(self):
        return f"{self.name} - {self.embossment_id}"
    
    def commission(self, date=None):
        """ Mark the asset as commissioned. """
        self.status = AssetStatus.ACTIVE
        self.commission_date = date or timezone.now()
        self.save()

    def decommission(self, date=None):
        """ Mark the asset as decommissioned. """
        self.status = AssetStatus.DECOMMISSIONED
        self.decommission_date = date or timezone.now()
        self.save()

    def archive(self):
        """ Mark the asset as archived. """
        self.is_archived = True
        self.save()


class MaintenanceReport(models.Model):
    MAINTENANCE_TYPE_CHOICES = [
        ('maintenance', 'Maintenance'),
        ('repair', 'Repair'),
        ('calibration', 'Calibration')
    ]


    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='maintenance_reports')
    maintenance_type = models.CharField(max_length=50, choices=MAINTENANCE_TYPE_CHOICES)
    date_performed = models.DateField()
    details = models.TextField()
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='report_added_by')


    def __str__(self):
        return f"{self.asset.name} - {self.maintenance_type} on {self.date_performed}"
