from rest_framework import serializers
from .models import Asset, AssetStatus, MaintenanceReport, Department, User
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from django.db import transaction



class DepartmentSerializer(serializers.ModelSerializer):
    total_assets = serializers.ReadOnlyField()
    active_assets = serializers.ReadOnlyField(source='total_active_assets')
    archive_assets = serializers.ReadOnlyField(source='total_archive_assets')
    assets_under_maintenance = serializers.ReadOnlyField(source='total_assets_under_maintenance')
    total_commissioned_assets = serializers.ReadOnlyField()
    total_decommissioned_assets = serializers.ReadOnlyField()

    class Meta:
        model = Department
        fields = [
            'name', 'slug', 'head', 'contact_phone', 'contact_email',
            'total_assets', 'active_assets', 'archive_assets',
            'assets_under_maintenance', 'total_commissioned_assets', 'total_decommissioned_assets'
        ]


        

class AssetSerializer(serializers.ModelSerializer):
    """
    Serializer for Asset objects that handles detailed information,
    including commissioning and decommissioning of assets.
    """
    department_name = serializers.ReadOnlyField(source='department.name')

    class Meta:
        model = Asset
        fields = [
            'asset_id', 'name', 'embossment_id', 'serial_number', 'device_type', 'status',
            'department', 'department_name', 'quantity', 'manufacturer', 'model',
            'embossment_date', 'manufacturing_date', 'description', 'commission_date',
            'decommission_date', 'created_at', 'updated_at', 'is_archived', 'added_by'
        ]

    def commission(self, instance, commission_date=None):
        """
        Mark the asset as commissioned with optional date.
        If no date is provided, current time is used.
        """
        try:
            with transaction.atomic():
                instance.status = AssetStatus.ACTIVE
                instance.commission_date = commission_date or timezone.now()
                instance.save()
        except Exception as e:
            raise ValidationError({"commission": str(e)})

    def decommission(self, instance, decommission_date=None):
        """
        Mark the asset as decommissioned with optional date.
        If no date is provided, current time is used.
        """
        try:
            with transaction.atomic():
                instance.status = AssetStatus.DECOMMISSIONED
                instance.decommission_date = decommission_date or timezone.now()
                instance.save()
        except Exception as e:
            raise ValidationError({"decommission": str(e)})

    def update(self, instance, validated_data):
        """
        Custom update logic to handle commissioning and decommissioning based on request data.
        """
        commission = validated_data.pop('commission', None)
        decommission = validated_data.pop('decommission', None)

        if commission:
            self.commission(instance, commission)
        if decommission:
            self.decommission(instance, decommission)
        
        return super().update(instance, validated_data)
    
    
class AssetMinimalSerializer(serializers.ModelSerializer):
    department_name = serializers.ReadOnlyField(source='department.name')

    class Meta:
        model = Asset
        fields = [
            'asset_id', 'name', 'embossment_id', 'department'
        ]


class MaintenanceReportSerializer(serializers.ModelSerializer):
    asset_details = AssetMinimalSerializer(source='asset', read_only=True)
    added_by_user = serializers.StringRelatedField(source='added_by')

    class Meta:
        model = MaintenanceReport
        fields = [
            'id',  'asset_details', 'maintenance_type', 'date_performed',
            'details', 'added_by_user'
        ]
        read_only_fields = ['asset_details'] 

