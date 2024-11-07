from rest_framework import serializers
from .models import Category, Item
from auditlog.models import LogEntry



class ItemMinimalSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for item representation in nested lists.
    """
    category_name = serializers.ReadOnlyField(source='category.name')
    stock_status = serializers.ReadOnlyField()

    class Meta:
        model = Item
        fields = ['id', 'descriptive_name', 'category_name', 'current_stock', 'stock_status']


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model, including draft/published status and soft deletion support.
    """
    is_draft = serializers.BooleanField(write_only=True, default=False)  # New field to control draft status
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'slug', 'name', 'description', 'created', 'modified', 'is_removed', 'status', 'is_draft']
        read_only_fields = ['id', 'slug', 'created', 'modified', 'is_removed', 'status']

    def validate_name(self, value):
        """
        Validate that the category name is unique when the status is published.
        """
        if self.instance and self.instance.status == Category.STATUS.published:
            if Category.objects.filter(name=value, status=Category.STATUS.published).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("A published category with this name already exists.")
        return value

    def create(self, validated_data):
        is_draft = validated_data.pop('is_draft', False)
        category = Category.objects.create(**validated_data)

        if is_draft:
            category.status = Category.STATUS.draft
        else:
            category.publish()

        return category

    def update(self, instance, validated_data):
        is_draft = validated_data.pop('is_draft', False)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if is_draft:
            instance.status = Category.STATUS.draft
        else:
            instance.publish()

        instance.save()
        return instance



class ItemSerializer(serializers.ModelSerializer):
    """
    Serializer for Item model, including stock status, category information, and soft deletion support.
    """
    category = serializers.PrimaryKeyRelatedField(queryset=Category.published.all())  # Only allow published categories
    category_name = serializers.ReadOnlyField(source='category.name')
    stock_status = serializers.SerializerMethodField()
    is_draft = serializers.BooleanField(write_only=True, default=False)  # New field to control draft status
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Item
        fields = ['id', 'category', 'category_name', 'descriptive_name', 'manufacturer', 'model_number',
                  'serial_number', 'current_stock', 'location', 'is_removed', 'created', 'modified', 'stock_status', 'status', 'is_draft']
        read_only_fields = ['is_removed', 'created', 'modified', 'stock_status', 'category_name', 'status']

    def get_stock_status(self, obj):
        """
        Returns the stock status based on current stock and soft deletion state.
        """
        return obj.stock_status

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
        if self.instance and self.instance.status == Item.STATUS.published:
            if Item.objects.filter(serial_number=value, status=Item.STATUS.published).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("A published item with this serial number already exists.")
        return value

    def create(self, validated_data):
        is_draft = validated_data.pop('is_draft', False)
        item = Item.objects.create(**validated_data)

        if is_draft:
            item.status = Item.STATUS.draft
        else:
            item.publish()

        return item

    def update(self, instance, validated_data):
        is_draft = validated_data.pop('is_draft', False)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if is_draft:
            instance.status = Item.STATUS.draft
        else:
            instance.publish()

        instance.save()
        return instance





class InventoryLogEntrySerializer(serializers.ModelSerializer):
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
