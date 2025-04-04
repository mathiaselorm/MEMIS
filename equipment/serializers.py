from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Equipment, EquipmentMaintenanceActivity, MaintenanceSchedule, Supplier

User = get_user_model()


# -------------------------------
# SUPPLIER SERIALIZERS
# -------------------------------
class SupplierWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['company_name', 'company_email', 'contact', 'website']

    def validate_company_name(self, value):
        if Supplier.objects.filter(company_name=value).exists():
            raise serializers.ValidationError("A supplier with this company name already exists.")
        return value


class SupplierReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            'id',
            'company_name',
            'company_email',
            'contact',
            'website',
            'created',
            'modified'
        ]


# -------------------------------
# EQUIPMENT SERIALIZERS
# -------------------------------
class EquipmentWriteSerializer(serializers.ModelSerializer):
    supplier = serializers.PrimaryKeyRelatedField(queryset=Supplier.objects.all())
    image = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    manual = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = Equipment
        fields = [
            'name',
            'device_type',
            'equipment_id',
            'department',
            'operational_status',
            'serial_number',
            'manufacturer',
            'model',
            'supplier',
            'location',
            'description',
            'image',
            'manual',
            'manufacturing_date',
        ]
        read_only_fields = [
            'added_by',
            'decommission_date',
            'equipment_id',
            'created',
            'modified'
        ]
        
    def validate(self, data):
        """
        Remove 'image/upload/' prefix if present.
        """
        if "image" in data:
            data["image"] = data["image"].replace("image/upload/", "") if data["image"] else None
        if "manual" in data:
            data["manual"] = data["manual"].replace("image/upload/", "") if data["manual"] else None
        return data
    
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['added_by'] = request.user
        else:
            raise ValidationError("User must be authenticated to add equipment.")

        if validated_data.get('operational_status') == 'decommissioned':
            validated_data['decommission_date'] = timezone.now()

        equipment = super().create(validated_data)
        return equipment

    def update(self, instance, validated_data):
        new_status = validated_data.get('operational_status', instance.operational_status)
        if new_status == 'decommissioned' and instance.operational_status != 'decommissioned':
            instance.decommission_date = timezone.now()
        instance = super().update(instance, validated_data)
        return instance


class EquipmentReadSerializer(serializers.ModelSerializer):
    added_by_name = serializers.SerializerMethodField()
    supplier_name = serializers.SerializerMethodField()

    class Meta:
        model = Equipment
        fields = [
            'id',
            'name',
            'device_type',
            'equipment_id',
            'serial_number',
            'operational_status',
            'department',
            'manufacturer',
            'model',
            'supplier',
            'supplier_name',
            'location',
            'description',
            'image',
            'manual',
            'manufacturing_date',
            'decommission_date',
            'added_by',
            'added_by_name',
            'created',
            'modified'
        ]

    def get_supplier_name(self, obj):
        # Now using company_name from Supplier
        return obj.supplier.company_name if obj.supplier else None

    def get_added_by_name(self, obj):
        return obj.added_by.get_full_name() if obj.added_by else "Unknown"


# -------------------------------
# EQUIPMENT MAINTENANCE ACTIVITY SERIALIZERS
# -------------------------------
class EquipmentMaintenanceActivityWriteSerializer(serializers.ModelSerializer):
    technician = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    equipment = serializers.PrimaryKeyRelatedField(queryset=Equipment.objects.all())
    date_time = serializers.DateTimeField()

    class Meta:
        model = EquipmentMaintenanceActivity
        fields = [
            'id',
            'equipment',
            'activity_type',
            'date_time',
            'technician',
            'pre_status',
            'post_status',
            'notes'
        ]

    def validate_date_time(self, value):
        if value > timezone.now():
            raise serializers.ValidationError("The date and time cannot be in the future.")
        return value


class EquipmentMaintenanceActivityReadSerializer(serializers.ModelSerializer):
    technician_name = serializers.CharField(read_only=True)
    equipment_name = serializers.CharField(source='equipment.name')

    class Meta:
        model = EquipmentMaintenanceActivity
        fields = [
            'id', 
            'equipment',
            'equipment_name',
            'activity_type',
            'date_time',
            'technician',
            'technician_name',
            'pre_status',
            'post_status',
            'notes',
            'created',
            'modified'
        ]


# -------------------------------
# MAINTENANCE SCHEDULE SERIALIZERS
# -------------------------------
class MaintenanceScheduleWriteSerializer(serializers.ModelSerializer):
    technician = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    equipment = serializers.PrimaryKeyRelatedField(queryset=Equipment.objects.all(), required=False)
    for_all_equipment = serializers.BooleanField(default=False)
    

    class Meta:
        model = MaintenanceSchedule
        fields = [
            'id',
            'equipment',
            'for_all_equipment',
            'technician',
            'title',
            'activity_type',
            'description',
            'start_date',
            'end_date',
            'frequency',
            'interval',
            'recurring_end'
        ]

    def validate(self, data):
        """
        Validate recurring_end is after start_date and required for recurring schedules.
        """
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        recurring_end = data.get("recurring_end")

        if end_date and end_date <= start_date:
            raise serializers.ValidationError("End date must be after start date.")

        if data.get("frequency") != "once":
            if not recurring_end:
                raise serializers.ValidationError("Recurring schedules must have a 'recurring_end' date.")
            if recurring_end <= start_date:
                raise serializers.ValidationError("Recurring end date must be after start date.")

        if data.get("for_all_equipment") and data.get("equipment"):
            raise serializers.ValidationError("A schedule for all equipment cannot be linked to a specific equipment.")

        if not data.get("for_all_equipment") and not data.get("equipment"):
            raise serializers.ValidationError("Equipment is required for non-general maintenance schedules.")

        return data


class MaintenanceScheduleReadSerializer(serializers.ModelSerializer):
    equipment_name = serializers.SerializerMethodField()
    technician_name = serializers.SerializerMethodField()

    class Meta:
        model = MaintenanceSchedule
        fields = [
            'id',
            'equipment',
            'equipment_name',
            'for_all_equipment',
            'technician',
            'technician_name',
            'title',
            'activity_type',
            'description',
            'start_date',
            'end_date',
            'frequency',
            'interval',
            'recurring_end',
            'next_occurrence',
            'last_notification',
            'created',
            'modified'
        ]

    def get_equipment_name(self, obj):
        if obj.equipment:
            return obj.equipment.name
        elif obj.for_all_equipment:
            return "For All Equipment"
        return None

    def get_technician_name(self, obj):
        return obj.technician.get_full_name() if obj.technician else None
