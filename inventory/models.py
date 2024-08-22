from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    
    
    def __str__(self):
        return self.name
    
class Item(models.Model):
    ategory = models.ForeignKey(Category, related_name='items', on_delete=models.CASCADE)
    model = models.CharField(max_length=100)
    part_number = models.CharField(max_length=100, blank=True, null=True)
    stock_quantity = models.IntegerField()
    reorder_threshold = models.IntegerField()
    supplier = models.ForeignKey('Supplier', related_name='items', on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.name} ({self.model}) - {self.department.name}"


class Supplier(models.Model):
    name = models.CharField(max_length=255)
    contact_info = models.CharField(max_length=255)

    def __str__(self):
        return self.name