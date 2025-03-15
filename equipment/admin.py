from django.contrib import admin
from django import forms
from .models import Equipment, EquipmentMaintenanceActivity, MaintenanceSchedule, Supplier




# ---------------------------
# Supplier Admin
# ---------------------------
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'company_email', 'contact', 'website', 'created', 'modified')
    search_fields = ('company_name', 'company_email', 'contact')
    readonly_fields = ('created', 'modified')
    fieldsets = (
        (None, {
            'fields': ('company_name', 'company_email', 'contact', 'website')
        }),
        ('Timestamps', {
            'fields': ('created', 'modified')
        }),
    )



# ---------------------------
# Equipment Maintenance Activity Inline
# ---------------------------
class EquipmentMaintenanceActivityInline(admin.TabularInline):
    model = EquipmentMaintenanceActivity
    extra = 0
    readonly_fields = ('technician_name',)
    fields = ('activity_type', 'date_time', 'technician', 'technician_name', 'pre_status', 'post_status', 'notes')

    def technician_name(self, obj):
        return obj.technician.get_full_name() if obj.technician else "Unknown"
    technician_name.short_description = "Technician"


# ---------------------------
# Equipment Admin
# ---------------------------
@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('equipment_id', 'name', 'device_type', 'serial_number', 'operational_status', 'department', 'supplier', 'manufacturer')
    list_filter = ('operational_status', 'device_type', 'department')
    search_fields = ('name', 'serial_number', 'equipment_id')
    readonly_fields = ('created', 'modified', 'added_by_name')
    fieldsets = (
        (None, {
            'fields': ('name', 'device_type', 'serial_number', 'equipment_id', 'image', 'manual', 'location')
        }),
        ('Ownership', {
            'fields': ('operational_status', 'department', 'added_by', 'added_by_name')
        }),
        ('Manufacturing & Lifecycle', {
            'fields': ('manufacturer', 'model', 'description', 'supplier', 'manufacturing_date', 'decommission_date')
        }),
    )
    inlines = [EquipmentMaintenanceActivityInline]
    actions = ['mark_as_active']

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.added_by = request.user
        if obj.added_by:
            obj.added_by_name = obj.added_by.get_full_name()
        else:
            obj.added_by_name = 'Unknown'
        super().save_model(request, obj, form, change)

    def mark_as_active(self, request, queryset):
        queryset.update(operational_status='functional')
    mark_as_active.short_description = "Mark selected equipment as functional"


# ---------------------------
# Equipment Maintenance Activity Admin
# ---------------------------
@admin.register(EquipmentMaintenanceActivity)
class EquipmentMaintenanceActivityAdmin(admin.ModelAdmin):
    list_display = ('id', 'equipment', 'activity_type', 'date_time', 'technician_name', 'pre_status', 'post_status')
    list_filter = ('activity_type', 'pre_status', 'post_status', 'technician')
    search_fields = ('equipment__name', 'technician__first_name', 'technician__last_name', 'notes')
    readonly_fields = ('technician_name', 'created', 'modified')
    fieldsets = (
        (None, {
            'fields': ('equipment', 'activity_type', 'date_time', 'notes')
        }),
        ('Technician Info', {
            'fields': ('technician', 'technician_name')
        }),
        ('Status Changes', {
            'fields': ('pre_status', 'post_status')
        }),
        ('Timestamps', {
            'fields': ('created', 'modified')
        }),
    )

    def technician_name(self, obj):
        return obj.technician.get_full_name() if obj.technician else "Unknown"
    technician_name.short_description = "Technician"

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.technician_name = obj.technician.get_full_name() if obj.technician else 'Unknown'
        super().save_model(request, obj, form, change)


# ---------------------------
# Maintenance Schedule Admin
# ---------------------------
@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'frequency', 'for_all_equipment')
    list_filter = ('frequency', 'for_all_equipment')
    search_fields = ('title', 'description')
    readonly_fields = ('last_notification', 'created', 'modified')
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'start_date', 'end_date', 'frequency', 'interval', 'recurring_end', 'technician')
        }),
        ('General or Equipment-Specific', {
            'fields': ('for_all_equipment', 'equipment')
        }),
        ('Timestamps', {
            'fields': ('last_notification', 'created', 'modified')
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
