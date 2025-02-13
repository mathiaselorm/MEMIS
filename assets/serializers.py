from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import DateField
from actstream import action
from .models import Asset, Department, AssetActivity, MaintenanceSchedule


User = get_user_model()




# Department Write Serializer
class DepartmentWriteSerializer(serializers.ModelSerializer):
    head = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    status = serializers.ChoiceField(choices=Department.STATUS, default=Department.STATUS.draft)

    class Meta:
        model = Department
        fields = ['name', 'head', 'contact_phone', 'contact_email', 'status']

    def create(self, validated_data):
        department = super().create(validated_data)
        # Record the activity
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            action.send(
                request.user,
                verb='created department',
                target=department
            )
        return department
    
    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        # Record the activity
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            action.send(
                request.user,
                verb='updated department',
                target=instance
            )
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
            'status', 'added_by'
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['added_by'] = request.user
        else:
            raise ValidationError("User must be authenticated to add assets.")

        asset = super().create(validated_data)
        # Record the activity
        if request and request.user.is_authenticated:
            action.send(
                request.user,
                verb='created asset',
                target=asset
            )
        return asset

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        # Record the activity
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            action.send(
                request.user,
                verb='updated asset',
                target=instance
            )
        return instance

    def validate(self, data):
        if data.get('commission_date') and data.get('decommission_date'):
            if data['commission_date'] > data['decommission_date']:
                raise ValidationError("Commission date cannot be after decommission date.")
        return data



# Asset Read Serializer
class AssetReadSerializer(serializers.ModelSerializer):
    department_name = serializers.SerializerMethodField()
    added_by_name = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)
    is_removed = serializers.BooleanField(read_only=True)
    added_by = serializers.SerializerMethodField() 
    embossment_date = DateField()
    manufacturing_date = DateField()
    commission_date = DateField()
    decommission_date = DateField(allow_null=True)
    

    class Meta:
        model = Asset
        fields = [
            'id', 'name', 'device_type', 'embossment_id', 'serial_number', 'operational_status',
            'department_name', 'quantity', 'manufacturer', 'model', 'description', 'image',
            'embossment_date', 'manufacturing_date', 'commission_date', 'decommission_date',
            'status', 'added_by', 'added_by_name', 'created', 'modified', 'is_removed'
        ]

    def get_department_name(self, obj):
        return obj.department.name if obj.department else None
    
    def get_added_by(self, obj):
        return obj.added_by.get_full_name() if obj.added_by else "Unknown"
    
    def get_added_by_name(self, obj):
        return obj.added_by.get_full_name() if obj.added_by else "Unknown"


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
    
    def __init__(self, *args, **kwargs):
        super(AssetActivityWriteSerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.method == 'POST':
            asset_id = self.context['view'].kwargs.get('asset_id')
            if asset_id:  # If asset_id is present in the URL, remove the asset field as it's not needed.
                self.fields.pop('asset', None)
            else:
                self.fields['asset'].required = True  # Ensure the field is required if not provided in the URL.

    def validate_asset(self, value):
        if not self.instance and not self.initial_data.get('asset') and not self.context['view'].kwargs.get('asset_id'):
            raise ValidationError("This field is required.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        activity = super().create(validated_data)
        # Update the asset's operational status based on post_status if it differs
        if activity.post_status and activity.asset.operational_status != activity.post_status:
            activity.asset.operational_status = activity.post_status
            activity.asset.save()
            
        #  record an action
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            action.send(
                request.user,
                verb='created asset activity',
                target=activity
            )
        return activity

    @transaction.atomic
    def update(self, instance, validated_data):
        activity = super().update(instance, validated_data)
        # Update the asset's operational status based on post_status if it differs
        if activity.post_status and activity.asset.operational_status != activity.post_status:
            activity.asset.operational_status = activity.post_status
            activity.asset.save()
        
        # Record an action
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            action.send(
                request.user,
                verb='updated asset activity',
                target=activity
            )
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
            'end_datetime', 'frequency', 'interval', 'until', 'is_active', 'next_occurrence'
        ]
        read_only_fields = ['id', 'next_occurrence']
        
    def validate(self, data):
        """
        Validate that end_datetime is after start_datetime, recurring events have an 'until' date,
        and 'asset' field is handled correctly based on 'is_general'.
        """
        # Check if end_datetime is after start_datetime
        start_datetime = data['start_datetime']
        end_datetime = data['end_datetime']
        if end_datetime <= start_datetime:
            raise serializers.ValidationError("End datetime must be after start datetime.")
        
        # Check that recurring schedules have an 'until' date
        frequency = data['frequency']
        if frequency != 'once' and not data.get('until'):
            raise serializers.ValidationError("Recurring schedules must have an 'until' date.")

        # Validate general vs specific schedules
        is_general = data['is_general']
        asset = data.get('asset')
        if is_general and asset is not None:
            raise serializers.ValidationError(
                "General maintenance schedules should not be associated with a specific asset."
            )
        if not is_general and asset is None:
            raise serializers.ValidationError(
                "Asset is required for non-general maintenance schedules."
            )
        
        # Check for overlapping schedules
        technician = data['technician']
        overlapping_schedules = MaintenanceSchedule.objects.filter(
            is_general=is_general,
            technician=technician,
            start_datetime__lt=end_datetime,
            end_datetime__gt=start_datetime
        )
        if not is_general:
            overlapping_schedules = overlapping_schedules.filter(asset=asset)
        
        # Exclude the current instance if updating
        if self.instance:
            overlapping_schedules = overlapping_schedules.exclude(id=self.instance.id)

        if overlapping_schedules.exists():
            raise serializers.ValidationError(
                "This schedule overlaps with another existing schedule. "
                "Please check for conflicts with the same technician or asset."
            )

        return data
    
    def create(self, validated_data):
        if validated_data['frequency'] == 'once':
            validated_data['interval'] = None
            validated_data['until'] = None
        schedule = super().create(validated_data)

        # Record creation activity
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            action.send(
                request.user,
                verb='created maintenance schedule',
                target=schedule
            )
        return schedule

    def update(self, instance, validated_data):
        if validated_data.get('frequency') == 'once':
            validated_data['interval'] = None
            validated_data['until'] = None
        schedule = super().update(instance, validated_data)

        # Record update activity
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            action.send(
                request.user,
                verb='updated maintenance schedule',
                target=schedule
            )
        return schedule

    

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
            'start_datetime', 'end_datetime', 'frequency', 'interval', 'until', 'is_active', 'next_occurrence',
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



