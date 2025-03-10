from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils import timezone
from autoslug import AutoSlugField
from model_utils.models import TimeStampedModel
from model_utils import Choices
from cloudinary.models import CloudinaryField
from django.core.exceptions import ValidationError
from dateutil import rrule 

User = get_user_model()


class Department(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    slug = AutoSlugField(
        populate_from='name', 
        max_length=255,
        unique=True,
    )
    head = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='head_of_department',
        blank=True,
        null=True
    )
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.name or 'Unknown Department'



class Supplier(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    contact = models.CharField(max_length=20, blank=True, null=True)
    office_address = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name or "Unknown Supplier"



class Equipment(TimeStampedModel):
    
    DEVICE_TYPE = Choices(
        ("diagnostic", "Diagnostic Device"),
        ("therapeutic", "Therapeutic Device"),
        ("life_support", "Life-Support Device"),
        ("monitoring", "Monitoring Device"),
        ("surgical", "Surgical Device"),
        ("radiology", "Radiology Device"),
        ("lab", "Laboratory Device"),  
        ("other", "Other Devices")
    )
    
    OPERATIONAL_STATUS = Choices(
        ("functional", "Functional"),
        ('in_process', 'In Process'),
        ('downtime', 'Downtime'),
    )
    name = models.CharField(max_length=255)
    device_type = models.CharField(
        max_length=255,
        choices=DEVICE_TYPE, 
        default=DEVICE_TYPE.other,
        db_index=True
    )
    embossment_id = models.CharField(max_length=100, unique=True)
    department = models.ForeignKey(
        Department,
        related_name='equipment',
        on_delete=models.CASCADE
    )

    operational_status = models.CharField(
        max_length=20,
        choices=OPERATIONAL_STATUS,
        default=OPERATIONAL_STATUS.functional
    )
    model = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100, unique=True)
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        related_name='equipment',
        blank=True,
        null=True
    )
    manufacturing_date = models.DateField()
    description = models.TextField(blank=True, null=True)
    image = CloudinaryField(
        'image',
        blank=True,
        null=True,
        resource_type='image',
        folder='equipment',
        unique_filename=True
    )
    decommission_date = models.DateField(blank=True, null=True)
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='added_equipment'
    )
    added_by_name = models.CharField(max_length=255, null=True, editable=False)

    class Meta:
        verbose_name = _('Equipment')
        verbose_name_plural = _('Equipment')
        indexes = [
            models.Index(fields=['name', 'department', 'operational_status']),
            models.Index(fields=['embossment_id']),
        ]

    
    def __str__(self):
        return f"{self.name} (Added by: {self.added_by.get_full_name() if self.added_by else 'Unknown'})"


class EquipmentMaintenanceActivity(TimeStampedModel):
    
    # Reuse the choices from Equipment model
    STATUS_CHOICES = Equipment.OPERATIONAL_STATUS 
    
    ACTIVITY_TYPE_CHOICES = Choices(
        ('preventive maintenance', 'Preventive Maintenance'),
        ('repair', 'Repair'),
        ('calibration', 'Calibration'),
    )

    equipment = models.ForeignKey(
        Equipment,
        related_name='activities',
        on_delete=models.CASCADE
    )
    activity_type = models.CharField(
        max_length=30,
        choices=ACTIVITY_TYPE_CHOICES,
        default='preventive maintenance'
    )
    date_time = models.DateTimeField()
    technician = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activities_performed'
    )
    pre_status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        null=True,
        blank=True 
    )
    post_status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date_time']
        indexes = [
            models.Index(fields=['equipment', 'date_time']),
        ]
        
    def save(self, *args, **kwargs):
        # Auto-assign pre_status on creation
        if not self.pk and not self.pre_status: 
            self.pre_status = self.equipment.operational_status
            
        super().save(*args, **kwargs)
        
        # Only update Equipment operational_status if post_status is set
        if self.post_status and self.post_status.strip():  # Ensures it's not empty or None
            self.equipment.operational_status = self.post_status
            self.equipment.save(update_fields=['operational_status'])

    def __str__(self):
        return f"{self.get_activity_type_display()} on {self.equipment.name}"

    
    

class MaintenanceSchedule(TimeStampedModel):
    """
    A model to define recurring (or one-off) maintenance schedules for
    either all equipment or a specific piece of equipment.
    """
  
    # Frequency choices to align with the UI's "Does not repeat," "Daily," etc.
    FREQUENCY_CHOICES = (
        ('once', 'Does not Repeat'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Biweekly'),
        ('monthly', 'Monthly'),
    )

    # We reuse the same activity choices from EquipmentMaintenanceActivity
    ACTIVITY_TYPE_CHOICES = EquipmentMaintenanceActivity.ACTIVITY_TYPE_CHOICES

    activity_type = models.CharField(
        max_length=30,
        choices=ACTIVITY_TYPE_CHOICES,
        help_text="Type of maintenance activity."
    )

    # If this schedule applies to all equipment rather than a single piece of equipment
    for_all_equipment = models.BooleanField(
        default=False,
        help_text="Check if the schedule is for all equipment."
    )

    # If 'for_all_equipment' is False, you can link a specific Equipment record
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='maintenance_schedules',
        null=True,
        blank=True
    )
    
    technician = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='maintenance_scheduled'
    )
    
    title = models.CharField(
        max_length=255,
        help_text="A short title for this maintenance schedule."
    )

    description = models.TextField(
        blank=True,
        null=True,
        help_text="Additional details about the maintenance schedule."
    )

    # Start and end date/time for this schedule
    start_date = models.DateTimeField(
        db_index=True,
        help_text="When the maintenance starts."
    )
    end_date = models.DateTimeField(
        db_index=True,
        blank=True,
        null=True,
        help_text="When the maintenance ends."
    )

    frequency = models.CharField(
        max_length=10,
        choices=FREQUENCY_CHOICES,
        default='once',
        help_text="How often this maintenance schedule repeats."
    )

    # Interval between occurrences (only relevant if frequency != 'once')
    interval = models.PositiveIntegerField(
        default=1,
        help_text="Interval between recurrences (e.g., every 2 weeks)."
    )

    # The date/time when recurring events should stop
    recurring_end = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Stop date/time for recurring schedules."
    )

    # Additional fields often used for internal logic
    last_notification = models.DateTimeField(blank=True, null=True)
    next_occurrence = models.DateTimeField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['start_date']),
            models.Index(fields=['last_notification']),
            models.Index(fields=['equipment']),
            models.Index(fields=['next_occurrence']),
        ]

    def clean(self):
        """
        Model-level validation to ensure logical consistency of schedule data.
        """
        if self.end_date and self.end_date <= self.start_date:
            raise ValidationError("End date/time must be after the start date/time.")

        # If the schedule repeats, it should have a recurring_end date
        if self.frequency != 'once' and not self.recurring_end:
            raise ValidationError("Recurring schedules must have a 'recurring_end' date/time.")

        # If for_all_equipment is True, equipment must be None
        if self.for_all_equipment and self.equipment is not None:
            raise ValidationError("A schedule for all equipment cannot be linked to a specific equipment.")

        # If for_all_equipment is False, equipment must not be None
        if not self.for_all_equipment and self.equipment is None:
            raise ValidationError("You must select an equipment if the schedule is not for all equipment.")
        
        # Force interval=2 for 'biweekly'
        if self.frequency == 'biweekly':
            self.interval = 2

    def __str__(self):
        """
        Return a readable string representation of this schedule.
        """
        if self.for_all_equipment:
            return f"[All Equipment] {self.title}"
        if self.equipment:
            return f"{self.title} for {self.equipment.name}"
        return self.title

     # ----------------------------------------------------------------------
    # HELPER METHODS
    # ----------------------------------------------------------------------
    def get_rrule_params(self):
        """
        Return the (freq, interval) tuple needed to construct an rrule.
        """
        freq_map = {
            'daily': rrule.DAILY,
            'weekly': rrule.WEEKLY,
            'biweekly': rrule.WEEKLY,  # 'biweekly' also uses WEEKLY
            'monthly': rrule.MONTHLY,
        }
        freq = freq_map.get(self.frequency, rrule.DAILY)

        # If 'biweekly', interval is forced to 2 (set in clean() as well)
        effective_interval = 2 if self.frequency == 'biweekly' else self.interval

        return freq, effective_interval

    def get_next_occurrences(self, count=1, lookahead_days=1):
        """
        Retrieve the next `count` occurrences within `lookahead_days` days from now.
        """

        now = timezone.now()

        # For a one-time schedule, if it's in the future, return [start_date], else []
        if self.frequency == 'once':
            return [self.start_date] if self.start_date > now else []

        freq, effective_interval = self.get_rrule_params()
        rule = rrule.rrule(
            freq,
            dtstart=self.start_date,
            interval=effective_interval,
            until=self.recurring_end
        )

        occurrences = rule.between(now, now + timedelta(days=lookahead_days), inc=True)
        return occurrences[:count]

    def compute_next_occurrence(self):
        """
        Calculate the very next occurrence for this schedule.
        """
        now = timezone.now()

        if self.frequency == 'once':
            return self.start_date if self.start_date > now else None

        freq, effective_interval = self.get_rrule_params()
        rule = rrule.rrule(
            freq,
            dtstart=self.start_date,
            interval=effective_interval,
            until=self.recurring_end
        )

        # Look up to 5 years ahead for the next occurrence
        next_occurrences = rule.between(now, now + timedelta(days=365 * 5), inc=False)
        return next_occurrences[0] if next_occurrences else None

    def save(self, *args, **kwargs):
        """
        Override save() to update self.next_occurrence right before saving.
        """
        self.next_occurrence = self.compute_next_occurrence()
        super().save(*args, **kwargs)