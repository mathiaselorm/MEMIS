from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from auditlog.models import LogEntry

from .models import Asset, Department

User = get_user_model()

# Department Write Serializer
class DepartmentWriteSerializer(serializers.ModelSerializer):
    head = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    is_draft = serializers.BooleanField(write_only=True, default=False)

    class Meta:
        model = Department
        fields = ['name', 'head', 'contact_phone', 'contact_email', 'is_draft']

    def create(self, validated_data):
        is_draft = validated_data.pop('is_draft', False)
        department = Department.objects.create(**validated_data)

        if is_draft:
            department.status = department.STATUS.draft
        else:
            department.publish()

        return department

    def update(self, instance, validated_data):
        is_draft = validated_data.pop('is_draft', False)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if is_draft:
            instance.status = instance.STATUS.draft
        else:
            instance.publish()

        instance.save()
        return instance

# Department Read Serializer
class DepartmentReadSerializer(serializers.ModelSerializer):
    head_name = serializers.SerializerMethodField()
    total_assets = serializers.ReadOnlyField()
    active_assets = serializers.ReadOnlyField(source='total_active_assets')
    archive_assets = serializers.ReadOnlyField(source='total_archive_assets')
    assets_under_maintenance = serializers.ReadOnlyField(source='total_assets_under_maintenance')
    total_commissioned_assets = serializers.ReadOnlyField()
    total_decommissioned_assets = serializers.ReadOnlyField()
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Department
        fields = [
            'id', 'name', 'slug', 'head_name', 'contact_phone', 'contact_email', 'status',
            'total_assets', 'active_assets', 'archive_assets', 'assets_under_maintenance',
            'total_commissioned_assets', 'total_decommissioned_assets'
        ]

    def get_head_name(self, obj):
        if obj.head:
            return obj.head.get_full_name()
        return None

# Asset Write Serializer
class AssetWriteSerializer(serializers.ModelSerializer):
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all())
    image = serializers.ImageField(
        max_length=None, allow_empty_file=True, use_url=True, required=False, allow_null=True
    )
    is_draft = serializers.BooleanField(write_only=True, default=False)

    class Meta:
        model = Asset
        fields = [
            'name', 'device_type', 'embossment_id', 'serial_number', 'operational_status',
            'department', 'quantity', 'manufacturer', 'model', 'description', 'image',
            'embossment_date', 'manufacturing_date', 'commission_date', 'decommission_date',
            'is_draft'
        ]

    def create(self, validated_data):
        is_draft = validated_data.pop('is_draft', False)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['added_by'] = request.user
        else:
            raise ValidationError("User must be authenticated to add assets.")

        asset = Asset.objects.create(**validated_data)

        if is_draft:
            asset.status = asset.STATUS.draft
        else:
            asset.publish()

        return asset

    def update(self, instance, validated_data):
        is_draft = validated_data.pop('is_draft', False)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if is_draft:
            instance.status = instance.STATUS.draft
        else:
            instance.publish()

        instance.save()
        return instance

    def validate(self, data):
        if data.get('commission_date') and data.get('decommission_date'):
            if data['commission_date'] > data['decommission_date']:
                raise ValidationError("Commission date cannot be after decommission date.")
        return data

# Asset Read Serializer
class AssetReadSerializer(serializers.ModelSerializer):
    department_name = serializers.SerializerMethodField()
    added_by = serializers.StringRelatedField(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Asset
        fields = [
            'id', 'name', 'device_type', 'embossment_id', 'serial_number', 'operational_status',
            'department_name', 'quantity', 'manufacturer', 'model', 'description', 'image',
            'embossment_date', 'manufacturing_date', 'commission_date', 'decommission_date',
            'status', 'added_by', 'created', 'modified', 'is_removed'
        ]

    def get_department_name(self, obj):
        return obj.department.name if obj.department else None


class AssetsLogEntrySerializer(serializers.ModelSerializer):
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
















# class AssetMinimalSerializer(serializers.ModelSerializer):
#     department_name = serializers.ReadOnlyField(source='department.name')

#     class Meta:
#         model = Asset
#         fields = ['id', 'name', 'device_type', 'embossment_id', 'department_name']