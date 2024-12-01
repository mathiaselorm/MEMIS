from django.contrib.auth import get_user_model

from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from auditlog.models import LogEntry

from .models import Asset, Department, AssetActivity, Notification, MaintenanceSchedule

User = get_user_model()

# Department Write Serializer
class DepartmentWriteSerializer(serializers.ModelSerializer):
    head = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    status = serializers.ChoiceField(choices=Department.STATUS, default=Department.STATUS.draft)

    class Meta:
        model = Department
        fields = ['name', 'head', 'contact_phone', 'contact_email', 'status']

    def create(self, validated_data):
        return Department.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
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
    is_removed = serializers.BooleanField(read_only=True)

    class Meta:
        model = Department
        fields = [
            'id', 'name', 'slug', 'head_name', 'contact_phone', 'contact_email', 'status',
            'total_assets', 'active_assets', 'archive_assets', 'assets_under_maintenance',
            'total_commissioned_assets', 'total_decommissioned_assets', 'created', 'modified', 
            'is_removed'
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
    status = serializers.ChoiceField(choices=Asset.STATUS, default=Asset.STATUS.draft)

    class Meta:
        model = Asset
        fields = [
            'name', 'device_type', 'embossment_id', 'serial_number', 'operational_status',
            'department', 'quantity', 'manufacturer', 'model', 'description', 'image',
            'embossment_date', 'manufacturing_date', 'commission_date', 'decommission_date',
            'status'
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['added_by'] = request.user
        else:
            raise ValidationError("User must be authenticated to add assets.")
        return Asset.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
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
    added_by_name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    is_removed = serializers.BooleanField(read_only=True)

    class Meta:
        model = Asset
        fields = [
            'id', 'name', 'device_type', 'embossment_id', 'serial_number', 'operational_status',
            'department_name', 'quantity', 'manufacturer', 'model', 'description', 'image',
            'embossment_date', 'manufacturing_date', 'commission_date', 'decommission_date',
            'status', 'added_by_name', 'created', 'modified', 'is_removed'
        ]

    def get_department_name(self, obj):
        return obj.department.name if obj.department else None


class AssetActivityWriteSerializer(serializers.ModelSerializer):
    technician = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = AssetActivity
        fields = [
            'id', 'asset', 'activity_type', 'date_time', 'technician',
            'pre_status', 'post_status', 'notes'
        ]

    def validate(self, data):
        asset = data.get('asset')
        pre_status = data.get('pre_status')
        if asset and pre_status and asset.operational_status != pre_status:
            raise serializers.ValidationError("Pre-status does not match the asset's current operational status.")
        return data

    def validate_date_time(self, value):
        if value > timezone.now():
            raise serializers.ValidationError("The date and time cannot be in the future.")
        return value

    
    def create(self, validated_data):
        activity = super().create(validated_data)
        # Optionally update the asset's operational status based on post_status
        if activity.post_status:
            activity.asset.operational_status = activity.post_status
            activity.asset.save()
        return activity

    def update(self, instance, validated_data):
        activity = super().update(instance, validated_data)
        # Optionally update the asset's operational status based on post_status
        if activity.post_status:
            activity.asset.operational_status = activity.post_status
            activity.asset.save()
        return activity


class AssetActivityReadSerializer(serializers.ModelSerializer):
    technician_name = serializers.CharField(read_only=True)
    asset_name = serializers.CharField(source='asset.name')
    asset = serializers.PrimaryKeyRelatedField(read_only=True)
    technician = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = AssetActivity
        fields = [
            'id', 'asset', 'asset_name', 'activity_type', 'date_time',
            'technician', 'technician_name', 'pre_status', 'post_status', 'notes',
            'created', 'modified', 'is_removed'
        ]


class MaintenanceScheduleWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating maintenance schedules.
    """
    technician = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    
    class Meta:
        model = MaintenanceSchedule
        fields = [
            'id', 'asset', 'is_general', 'technician', 'title', 'description', 'start_datetime',
            'end_datetime', 'frequency', 'interval', 'until', 'is_active'
        ]
        read_only_fields = ['id']
        

    def validate(self, data):
        """
        Validate that end_datetime is after start_datetime, recurring events have an 'until' date,
        and 'asset' field is handled correctly based on 'is_general'.
        """
        start_datetime = data.get('start_datetime')
        end_datetime = data.get('end_datetime')
        if start_datetime and end_datetime:
            if end_datetime <= start_datetime:
                raise serializers.ValidationError("End datetime must be after start datetime.")
        frequency = data.get('frequency', 'once')
        until = data.get('until')
        if frequency != 'once' and not until:
            raise serializers.ValidationError("Recurring schedules must have an 'until' date.")

        is_general = data.get('is_general', False)
        asset = data.get('asset')
        if is_general and asset is not None:
            raise serializers.ValidationError("General maintenance schedules should not be associated with a specific asset.")
        if not is_general and asset is None:
            raise serializers.ValidationError("Asset is required for non-general maintenance schedules.")
        return data

    

class MaintenanceScheduleReadSerializer(serializers.ModelSerializer):
    """
    Serializer for reading maintenance schedules, including asset and technician names.
    """
    asset_name = serializers.SerializerMethodField()
    technician_name = serializers.SerializerMethodField()

    class Meta:
        model = MaintenanceSchedule
        fields = [
            'id', 'asset', 'asset_name', 'is_general', 'technician', 'technician_name', 'title', 'description',
            'start_datetime', 'end_datetime', 'frequency', 'interval', 'until', 'is_active'
        ]

    def get_asset_name(self, obj):
        """
        Get the name of the asset, or 'General' if it's a general schedule.
        """
        if obj.asset:
            return obj.asset.name
        elif obj.is_general:
            return "General"
        else:
            return None

    def get_technician_name(self, obj):
        """
        Get the full name of the technician.
        """
        if obj.technician:
            return obj.technician.get_full_name()
        else:
            return None


              

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'message', 'link', 'is_read', 'created', 'modified', 'user']
        read_only_fields = ['id', 'created', 'user']



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

