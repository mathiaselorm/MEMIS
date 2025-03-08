from django.db import models
from model_utils.models import TimeStampedModel



class Item(TimeStampedModel):
    """
    Represents an item with inventory details.
    """
    CATEGORY_CHOICES = [
        ('replacement', 'Replacement Part'),
        ('maintenance', 'Maintenance Tool'),
        ('critical', 'Critical Component'),
        ('consumable', 'Consumables & Accessories'),
    ]
    name = models.CharField(max_length=255, db_index=True)
    item_code = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)    
    quantity = models.PositiveIntegerField(default=0)
    location = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"

    @property
    def stock_status(self):
        if self.quantity == 0:
            return "Out of Stock"
        elif self.quantity <= 2:
            return "Low Stock"
        else:
            return "In Stock"


