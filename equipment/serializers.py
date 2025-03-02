from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from actstream import action
from .models import Equipment, Department, EquipmentMaintenanceActivity, MaintenanceSchedule, Supplier

User = get_user_model()


# -------------------------------
# DEPARTMENT SERIALIZERS
# -------------------------------
class DepartmentWriteSerializer(serializers.ModelSerializer):
    head = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)

    class Meta:
        model = Department
        fields = ['name', 'head', 'contact_phone', 'contact_email']

    def validate_name(self, value):
        if Department.objects.filter(name=value).exists():
            raise serializers.ValidationError("A department with this name already exists.")
        return value

    def create(self, validated_data):
        department = super().create(validated_data)
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            action.send(request.user, verb='created department', target=department)
        return department

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            action.send(request.user, verb='updated department', target=instance)
        return instance


class DepartmentReadSerializer(serializers.ModelSerializer):
    head_name = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = [
            'id',
            'name',
            'slug',
            'head_name',
            'contact_phone',
            'contact_email',
            'created',
            'modified'
        ]

    def get_head_name(self, obj):
        return obj.head.get_full_name() if obj.head else None


# -------------------------------
# SUPPLIER SERIALIZERS
# -------------------------------
class SupplierWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['name', 'email', 'contact', 'office_address', 'website']

    def validate_name(self, value):
        if Supplier.objects.filter(name=value).exists():
            raise serializers.ValidationError("A supplier with this name already exists.")
        return value


class SupplierReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            'id',
            'name',
            'email',
            'contact',
            'office_address',
            'website',
            'created',
            'modified'
        ]


# -------------------------------
# EQUIPMENT SERIALIZERS
# -------------------------------
class EquipmentWriteSerializer(serializers.ModelSerializer):
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all())
    image = serializers.ImageField(allow_empty_file=True, use_url=True, required=False, allow_null=True)

    class Meta:
        model = Equipment
        fields = [
            'name',
            'device_type',
            'embossment_id',
            'department',
            'operational_status',
            'serial_number',
            'manufacturer',
            'model',
            'supplier',
            'description',
            'image',
            'manufacturing_date',
            'decommission_date',
            'added_by'
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['added_by'] = request.user
        else:
            raise ValidationError("User must be authenticated to add equipment.")

        equipment = super().create(validated_data)
        if request and request.user.is_authenticated:
            action.send(request.user, verb='created equipment', target=equipment)
        return equipment

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            action.send(request.user, verb='updated equipment', target=instance)
        return instance


class EquipmentReadSerializer(serializers.ModelSerializer):
    department_name = serializers.SerializerMethodField()
    added_by_name = serializers.SerializerMethodField()
    supplier_name = serializers.SerializerMethodField()

    class Meta:
        model = Equipment
        fields = [
            'id',
            'name',
            'device_type',
            'embossment_id',
            'serial_number',
            'operational_status',
            'department_name',
            'manufacturer',
            'model',
            'supplier_name',
            'description',
            'image',
            'manufacturing_date',
            'decommission_date',
            'added_by_name',
            'created',
            'modified'
        ]

    def get_department_name(self, obj):
        return obj.department.name if obj.department else None

    def get_supplier_name(self, obj):
        return obj.supplier.name if obj.supplier else None

    def get_added_by_name(self, obj):
        return obj.added_by.get_full_name() if obj.added_by else "Unknown"


# -------------------------------
# EQUIPMENT MAINTENANCE ACTIVITY SERIALIZERS
# -------------------------------
class EquipmentMaintenanceActivityWriteSerializer(serializers.ModelSerializer):
    technician = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

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
            'equipment_name',
            'activity_type',
            'date_time',
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

    class Meta:
        model = MaintenanceSchedule
        fields = [
            'id',
            'equipment',
            'for_all_equipment',
            'technician',
            'title',
            'description',
            'start_date',
            'end_date',
            'frequency',
            'interval',
            'recurring_end'
        ]

    def validate(self, data):
        start_date, end_date = data['start_date'], data['end_date']
        if end_date <= start_date:
            raise serializers.ValidationError("End date must be after start date.")

        if data['frequency'] != 'once' and not data.get('recurring_end'):
            raise serializers.ValidationError("Recurring schedules must have an 'recurring_end' date.")

        if data['for_all_equipment'] and data.get('equipment'):
            raise serializers.ValidationError("General maintenance schedules should not be linked to specific equipment.")

        if not data['for_all_equipment'] and not data.get('equipment'):
            raise serializers.ValidationError("Equipment is required for non-general maintenance schedules.")

        return data


class MaintenanceScheduleReadSerializer(serializers.ModelSerializer):
    equipment_name = serializers.SerializerMethodField()
    technician_name = serializers.SerializerMethodField()

    class Meta:
        model = MaintenanceSchedule
        fields = [
            'id',
            'equipment_name',
            'for_all_equipment',
            'technician_name',
            'title',
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
