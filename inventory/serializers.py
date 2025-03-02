from rest_framework import serializers
from .models import Item

class ItemReadSerializer(serializers.ModelSerializer):
    """
    Serializer for reading Item instances.
    """
    stock_status = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = [
            'id', 'category', 'name', 'item_code', 
            'description', 'quantity', 'location', 
            'stock_status', 'created', 'modified'
        ]

    def get_stock_status(self, obj):
        """
        Returns the stock status based on current stock.
        """
        return obj.stock_status


class ItemWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating Item instances.
    """

    class Meta:
        model = Item
        fields = ['category', 'name', 'item_code', 'description', 'quantity', 'location']

    def validate_quantity(self, value):
        """
        Ensure the quantity is never less than zero.
        """
        if value < 0:
            raise serializers.ValidationError("Current stock cannot be negative.")
        return value

    def validate_item_code(self, value):
        """
        Ensure the item code is unique.
        """
        qs = Item.objects.filter(item_code=value)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.exists():
            raise serializers.ValidationError("Item code already exists.")
        return value

    def create(self, validated_data):
        return Item.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
