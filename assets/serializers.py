from rest_framework import serializers
from .models import Asset, AssetStatus, Department, ActionLog, DepartmentStatus, ActionType
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db import transaction
from auditlog.models import LogEntry



User = get_user_model()


class DepartmentSerializer(serializers.ModelSerializer):
    head = serializers.SerializerMethodField()
    total_assets = serializers.ReadOnlyField()
    active_assets = serializers.ReadOnlyField(source='total_active_assets')
    archive_assets = serializers.ReadOnlyField(source='total_archive_assets')
    assets_under_maintenance = serializers.ReadOnlyField(source='total_assets_under_maintenance')
    total_commissioned_assets = serializers.ReadOnlyField()
    total_decommissioned_assets = serializers.ReadOnlyField()
    is_draft = serializers.BooleanField(write_only=True, default=False)  # To manage drafts

    class Meta:
        model = Department
        fields = [
            'id', 'name', 'slug', 'head', 'contact_phone', 'contact_email',
            'total_assets', 'active_assets', 'archive_assets',
            'assets_under_maintenance', 'total_commissioned_assets', 'total_decommissioned_assets',
            'is_draft'
        ]

    def get_head(self, obj):
        if obj.head:
            return f"{obj.head.first_name} {obj.head.last_name}"
        return None

    def create(self, validated_data):
        # Handle is_draft flag and assign the status accordingly
        is_draft = validated_data.pop('is_draft', False)
        department = super().create(validated_data)

        if is_draft:
            department.status = DepartmentStatus.DRAFT  # Set status to draft
        else:
            department.status = DepartmentStatus.PUBLISHED  # Set status to published

        department.save()
        return department

    def update(self, instance, validated_data):
        # Handle is_draft flag during updates
        is_draft = validated_data.pop('is_draft', False)
        department = super().update(instance, validated_data)

        if is_draft:
            department.status = DepartmentStatus.DRAFT  # Set status to draft
        else:
            department.status = DepartmentStatus.PUBLISHED  # Set status to published

        department.save()
        return department
    
     
class AssetSerializer(serializers.ModelSerializer):
    department = serializers.SerializerMethodField()  
    added_by = serializers.SerializerMethodField()

    class Meta:
        model = Asset
        fields = [
            'id', 'name', 'device_type', 'embossment_id', 'serial_number', 'status',
            'department', 'quantity', 'manufacturer', 'model',  'description', 'image',
            'embossment_date', 'manufacturing_date', 'commission_date',
            'decommission_date', 'created_at', 'updated_at', 'is_archived', 'added_by', 'is_draft'
        ]
    
    def get_department(self, obj):
        return obj.department.name if obj.department else None

    def get_added_by(self, obj):
        if obj.added_by:
            return f"{obj.added_by.first_name} {obj.added_by.last_name}"
        return None
    
    def create(self, validated_data):
        is_draft = validated_data.pop('is_draft', False)
        asset = super().create(validated_data)

        if is_draft:
            asset.status = AssetStatus.DRAFT  # Just set the status to DRAFT
        else:
            asset.status = AssetStatus.ACTIVE  # Set to active or another default status

        asset.save()
        return asset

    def update(self, instance, validated_data):
        is_draft = validated_data.pop('is_draft', False)
        asset = super().update(instance, validated_data)

        # Handle commission and decommission status changes
        commission = validated_data.pop('commission', None)
        decommission = validated_data.pop('decommission', None)

        if commission:
            self.change_asset_status(instance, AssetStatus.ACTIVE, 'commission_date', commission)
        if decommission:
            self.change_asset_status(instance, AssetStatus.DECOMMISSIONED, 'decommission_date', decommission)

        asset = super().update(instance, validated_data)

        if is_draft:
            asset.status = AssetStatus.DRAFT  # Just set the status to DRAFT
        else:
            asset.status = AssetStatus.ACTIVE  # Set to active or another status

        asset.save()
        return asset

    def validate(self, data):
        """
        Custom validation to prevent conflicting actions such as 
        commissioning and decommissioning at the same time.
        """
        if 'commission' in data and 'decommission' in data:
            raise ValidationError("Cannot commission and decommission an asset simultaneously.")
        return data

    def change_asset_status(self, instance, status, date_field_name, date=None):
        """
        Helper method to change the asset's status and set the appropriate date field.
        """
        with transaction.atomic():
            setattr(instance, 'status', status)
            setattr(instance, date_field_name, date or timezone.now())
            instance.save(update_fields=['status', date_field_name])
    

class AssetMinimalSerializer(serializers.ModelSerializer):
    department_name = serializers.ReadOnlyField(source='department.name')

    class Meta:
        model = Asset
        fields = ['asset_id', 'name', 'device_type', 'embossment_id', 'department']


class LogEntrySerializer(serializers.ModelSerializer):
    actor = serializers.StringRelatedField()  # Shows the username or a string representation of the user
    changes = serializers.SerializerMethodField()

    class Meta:
        model = LogEntry
        fields = ['action', 'timestamp', 'object_repr', 'changes', 'actor']

    def get_changes(self, obj):
        """
        Generate a user-friendly sentence form of the changes made.
        """
        changes = obj.changes_dict
        change_messages = []

        for field, values in changes.items():
            if isinstance(values, list) and len(values) == 2:
                old_value, new_value = values
                change_messages.append(f"{field} changed from '{old_value}' to '{new_value}'")

        return "; ".join(change_messages) if change_messages else "No changes recorded."

    def get_actor(self, obj):
        return obj.actor.get_full_name() if obj.actor else "Unknown User"
    

class ActionLogSerializer(serializers.ModelSerializer):
    performed_by = serializers.StringRelatedField()  # Shows the username or a string representation of the user
    action = serializers.ChoiceField(choices=ActionType.choices)  # Ensure it's serialized correctly

    class Meta:
        model = ActionLog
        fields = ['action', 'asset', 'performed_by', 'timestamp', 'changes', 'reason']