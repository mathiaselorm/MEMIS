from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from model_utils.models import StatusModel, SoftDeletableModel, TimeStampedModel
from model_utils import Choices
from model_utils.managers import QueryManager
from autoslug import AutoSlugField
from auditlog.registry import auditlog
from django.db.models import Q, UniqueConstraint

User = get_user_model()

class ConditionalValidationMixin:
    def save(self, *args, **kwargs):
        if self.status != self.STATUS.draft:
            self.full_clean()
        super().save(*args, **kwargs)

class Category(ConditionalValidationMixin, StatusModel, SoftDeletableModel, TimeStampedModel):
    """
    Represents a category for items. Includes a name and an optional description.
    """
    name = models.CharField(max_length=255, unique=True)
    slug = AutoSlugField(populate_from='name', unique=True, max_length=255)
    description = models.TextField(blank=True, null=True)
    STATUS = Choices('draft', 'published')

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['name'],
                condition=Q(status='published'),
                name='unique_category_name_when_published'
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
        return self.name
    
    

class Item(ConditionalValidationMixin, StatusModel, SoftDeletableModel, TimeStampedModel):
    """
    Represents an item with inventory details, linked to a category.
    """
    category = models.ForeignKey(
        Category,
        related_name='items',
        on_delete=models.CASCADE,
        null=True,
        db_index=True
    )
    descriptive_name = models.CharField(max_length=255, db_index=True)
    manufacturer = models.CharField(max_length=100, blank=True, null=True)
    model_number = models.CharField(max_length=100, blank=True, null=True)
    serial_number = models.CharField(max_length=100, unique=True)
    current_stock = models.IntegerField(validators=[MinValueValidator(0)])
    location = models.CharField(max_length=255)
    STATUS = Choices('draft', 'published')
    
    class Meta:
        verbose_name_plural = "items"
        constraints = [
            UniqueConstraint(
                fields=['serial_number'],
                condition=Q(status='published'),
                name='unique_item_serial_number_when_published'  # Updated constraint name
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
        return f"{self.descriptive_name}"

    @property
    def stock_status(self):
        """
        Returns the stock status based on current stock and deleted state.
        """
        if self.is_removed:
            return "Archived"
        elif self.current_stock == 0:
            return "Out of Stock"
        else:
            return "In Stock"



# Register models with auditlog
auditlog.register(Item)
auditlog.register(Category)
