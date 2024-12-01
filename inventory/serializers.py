from rest_framework import serializers
from .models import Category, Item
from auditlog.models import LogEntry

# --------- CATEGORY SERIALIZERS --------- #

class CategoryReadSerializer(serializers.ModelSerializer):
    """
    Serializer for reading Category instances.
    """
    class Meta:
        model = Category
        fields = ['id', 'slug', 'name', 'description', 'created', 'modified', 'is_removed', 'status']


class CategoryWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating Category instances.
    """
    status = serializers.ChoiceField(choices=Category.STATUS, default=Category.STATUS.draft)

    class Meta:
        model = Category
        fields = ['name', 'description', 'status']

    def validate_name(self, value):
        """
        Validate that the category name is unique when the status is published.
        """
        status = self.initial_data.get('status', self.instance.status if self.instance else None)
        if status == Category.STATUS.published:
            qs = Category.objects.filter(name=value, status=Category.STATUS.published)
            if self.instance:
                qs = qs.exclude(id=self.instance.id)
            if qs.exists():
                raise serializers.ValidationError("A published category with this name already exists.")
        return value

    def create(self, validated_data):
        return Category.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

# --------- ITEM SERIALIZERS --------- #

class ItemReadSerializer(serializers.ModelSerializer):
    """
    Serializer for reading Item instances.
    """
    category_name = serializers.ReadOnlyField(source='category.name')
    stock_status = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = ['id', 'category_name', 'descriptive_name', 'manufacturer', 'model_number',
                  'serial_number', 'current_stock', 'location', 'is_removed', 'created', 'modified', 'stock_status', 'status']

    def get_stock_status(self, obj):
        """
        Returns the stock status based on current stock and soft deletion state.
        """
        return obj.stock_status


class ItemWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating Item instances.
    """
    category = serializers.PrimaryKeyRelatedField(queryset=Category.all_objects.all())
    status = serializers.ChoiceField(choices=Item.STATUS, default=Item.STATUS.draft)

    class Meta:
        model = Item
        fields = ['category', 'descriptive_name', 'manufacturer', 'model_number',
                  'serial_number', 'current_stock', 'location', 'status']

    def validate_current_stock(self, value):
        """
        Ensure current stock is never less than zero.
        """
        if value < 0:
            raise serializers.ValidationError("Current stock cannot be negative.")
        return value

    def validate_serial_number(self, value):
        """
        Validate that the serial number is unique when the status is published.
        """
        status = self.initial_data.get('status', self.instance.status if self.instance else None)
        if status == Item.STATUS.published:
            qs = Item.objects.filter(serial_number=value, status=Item.STATUS.published)
            if self.instance:
                qs = qs.exclude(id=self.instance.id)
            if qs.exists():
                raise serializers.ValidationError("A published item with this serial number already exists.")
        return value

    def create(self, validated_data):
        return Item.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

# --------- INVENTORY LOG SERIALIZER --------- #

class InventoryLogEntrySerializer(serializers.ModelSerializer):
    """
    Serializer for audit log entries.
    """
    actor = serializers.SerializerMethodField()
    changes = serializers.SerializerMethodField()

    class Meta:
        model = LogEntry
        fields = ['action', 'timestamp', 'object_repr', 'changes', 'actor']

    def get_changes(self, obj):
        changes = obj.changes_dict or {}
        change_messages = []

        for field, values in changes.items():
            if isinstance(values, list) and len(values) == 2:
                old_value, new_value = values
                change_messages.append(f"{field} changed from '{old_value}' to '{new_value}'")

        return "; ".join(change_messages) if change_messages else "No changes recorded."

    def get_actor(self, obj):
        if obj.actor:
            return obj.actor.get_full_name()
        return "Unknown User"
