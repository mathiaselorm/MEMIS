from rest_framework import serializers
from .models import Category, Supplier, Item
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords

class ItemMinimalSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for item representation in nested lists.
    """
    category_name = serializers.ReadOnlyField(source='category.name')
    
    class Meta:
        model = Item
        fields = ['item_id', 'descriptive_name', 'category_name', 'current_stock', 'stock_status']





class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model with history and soft deletion support.
    """
    history = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'slug', 'name', 'description', 'created_at', 'modified', 'is_deleted']
        read_only_fields = ['is_deleted', 'history', 'created_at', 'updated_at']

  


class SupplierSerializer(serializers.ModelSerializer):
    """
    Serializer for Supplier model with item listing, contact details, and history.
    """
    supplied_items = serializers.SerializerMethodField()
    history = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = ['id', 'name', 'contact_info', 'created_at', 'updated_at', 'history', 'is_deleted', 'supplied_items']
        read_only_fields = ['is_deleted', 'history', 'created_at', 'updated_at']

    def get_supplied_items(self, obj):
        """
        Return all items related to the supplier without pagination.
        """
        items = obj.items.all()  # Get all items related to the supplier
        return ItemMinimalSerializer(items, many=True).data

    def get_history(self, obj):
        """
        Include history in the serialization if requested by query parameters.
        """
        request = self.context.get('request', None)
        if request and 'include_history' in request.query_params:
            history = obj.history.all()
            return HistoricalRecordSerializer(history, many=True).data
        return None


class ItemSerializer(serializers.ModelSerializer):
    """
    Serializer for Item model, including stock status, category and supplier names, and history.
    """
    category_name = serializers.ReadOnlyField(source='category.name')
    supplier_name = serializers.SerializerMethodField()
    stock_status = serializers.SerializerMethodField()  # Allow custom logic for stock status
    history = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = ['item_id', 'category', 'category_name', 'descriptive_name', 'batch_number',
                  'current_stock', 'reorder_threshold', 'location', 'supplier', 'supplier_name',
                  'is_deleted', 'deleted_at', 'created_at', 'updated_at', 'stock_status', 'history']
        read_only_fields = ['is_deleted', 'history', 'created_at', 'updated_at', 'stock_status', 'category_name', 'supplier_name']

    def get_supplier_name(self, obj):
        """
        Returns the supplier's name, or 'Unknown' if no supplier is linked.
        """
        if obj.supplier:
            return obj.supplier.name
        return "Unknown"

    def get_stock_status(self, obj):
        """
        Returns the stock status by reading the model property.
        """
        return obj.stock_status

    def validate_current_stock(self, value):
        """
        Ensure current stock is never less than zero.
        """
        if value < 0:
            raise serializers.ValidationError("Current stock cannot be negative.")
        return value

    def validate(self, data):
        """
        Additional validation to ensure reorder_threshold does not exceed current_stock.
        """
        if data['reorder_threshold'] > data.get('current_stock', 0):
            raise ValidationError("Reorder threshold cannot exceed current stock.")
        return data

    def get_history(self, obj):
        """
        Optionally include history in the serialization if requested by query parameters.
        """
        request = self.context.get('request', None)
        if request and 'include_history' in request.query_params:
            history = obj.history.all()
            return HistoricalRecordSerializer(history, many=True).data
        return None
