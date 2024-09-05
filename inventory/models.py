from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, ValidationError
from simple_history.models import HistoricalRecords
from django.utils import timezone
from django.utils.text import slugify

User = get_user_model()

class TimeStampedModel(models.Model):
    """
    Abstract base model that provides self-updating 'created_at' and 'updated_at' fields.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class SoftDeletionManager(models.Manager):
    """
    Manager to filter out soft-deleted objects by default.
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class SoftDeletionModel(TimeStampedModel):
    """
    Abstract base model that adds soft deletion functionality with 'is_deleted' and 'deleted_at' fields.
    """
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def delete(self, using=None, keep_parents=False):
        """ Mark the instance as deleted instead of deleting it from the database. """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    class Meta:
        abstract = True

class Category(SoftDeletionModel):
    """
    Represents a category for items. Includes a name and an optional description.
    """
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    history = HistoricalRecords()

    objects = SoftDeletionManager()  # Exclude soft-deleted categories by default
    
    def save(self, *args, **kwargs):
        if not self.slug:  # Only set the slug when it's not provided.
            self.slug = slugify(self.name)
        super(Category, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

class Supplier(SoftDeletionModel):
    """
    Represents a supplier with a name and contact information.
    """
    name = models.CharField(max_length=255)
    contact_info = models.CharField(max_length=255)
    history = HistoricalRecords()

    objects = SoftDeletionManager()  # Exclude soft-deleted suppliers by default

    def __str__(self):
        return self.name

class Item(SoftDeletionModel):
    """
    Represents an item with inventory details, linked to a category and a supplier.
    """
    item_id = models.AutoField(primary_key=True)    
    category = models.ForeignKey(Category, related_name='items', on_delete=models.CASCADE, null=True, db_index=True)
    descriptive_name = models.CharField(max_length=255, db_index=True)
    batch_number = models.CharField(max_length=100, blank=True, null=True)
    current_stock = models.IntegerField(validators=[MinValueValidator(0)])
    reorder_threshold = models.IntegerField(validators=[MinValueValidator(0)])
    location = models.CharField(max_length=255)
    supplier = models.ForeignKey(Supplier, related_name='items', on_delete=models.SET_NULL, null=True)
    history = HistoricalRecords()

    def clean(self):
        """
        Ensures the reorder threshold does not exceed the current stock.
        """
        if self.reorder_threshold > self.current_stock:
            raise ValidationError({'reorder_threshold': 'Reorder threshold cannot exceed current stock.'})
        
    def save(self, *args, **kwargs):
        """ Ensure the item is fully validated before saving. """
        self.full_clean()  # Call the full_clean method before saving to run clean method
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.descriptive_name} - Stock: {self.current_stock} - Batch: {self.batch_number or 'N/A'}"

    @property
    def stock_status(self):
        """ Returns the stock status based on current stock and archived state. """
        if self.is_deleted:
            return "Archived"
        elif self.current_stock <= self.reorder_threshold:
            return "Out of Stock"
        else:
            return "In Stock"

    class Meta:
        verbose_name_plural = "items"
