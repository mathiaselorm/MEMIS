from django.contrib import admin
from .models import Asset, Department, AssetActivity, MaintenanceSchedule
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'head', 'status', 'contact_phone', 'contact_email', 'is_removed')
    search_fields = ('name',)
    readonly_fields = ('slug',)

    def get_queryset(self, request):
        # Include soft-deleted items
        return self.model.all_objects.all()

class AssetActivityInline(admin.TabularInline):
    model = AssetActivity
    extra = 0
    readonly_fields = ('technician_name',)
    fields = (
        'activity_type', 'date_time', 'technician', 'technician_name',
        'pre_status', 'post_status', 'notes'
    )

class AssetAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'device_type', 'serial_number', 'status',
        'operational_status', 'department', 'manufacturer', 'is_removed'
    )
    list_filter = ('status', 'operational_status', 'device_type', 'department', 'is_removed')
    search_fields = ('name', 'serial_number', 'embossment_id')
    readonly_fields = ('created', 'modified', 'added_by', 'added_by_name')
    fieldsets = (
        (None, {
            'fields': ('name', 'device_type', 'serial_number', 'embossment_id', 'quantity', 'image')
        }),
        ('Availability', {
            'fields': ('status', 'operational_status', 'department', 'is_removed', 'added_by', 'added_by_name')
        }),
        ('Details', {
            'fields': (
                'manufacturer', 'model', 'description', 'embossment_date',
                'manufacturing_date', 'commission_date', 'decommission_date'
            )
        }),
    )
    inlines = [AssetActivityInline]
    
    def get_queryset(self, request):
        # Include soft-deleted items
        return self.model.all_objects.all()
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            # Set 'added_by' to the current user on creation
            obj.added_by = request.user
        # Set 'added_by_name' to preserve the user's name
        if obj.added_by:
            obj.added_by_name = obj.added_by.get_full_name()
        else:
            obj.added_by_name = 'Unknown'
        super().save_model(request, obj, form, change)

    def mark_as_active(self, request, queryset):
        queryset.update(operational_status='active')
    mark_as_active.short_description = "Mark selected assets as operationally active"

    actions = [mark_as_active]  # Custom action

class AssetActivityAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'asset', 'activity_type', 'date_time', 'technician_name',
        'pre_status', 'post_status'
    )
    list_filter = ('activity_type', 'pre_status', 'post_status', 'technician')
    search_fields = ('asset__name', 'technician__first_name', 'technician__last_name', 'notes')
    readonly_fields = ('technician_name', 'created', 'modified')
    fieldsets = (
        (None, {
            'fields': ('asset', 'activity_type', 'date_time', 'notes')
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

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            # On creation, set the technician_name
            if obj.technician:
                obj.technician_name = obj.technician.get_full_name()
            else:
                obj.technician_name = 'Unknown'
        super().save_model(request, obj, form, change)

class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_datetime', 'end_datetime', 'frequency', 'is_general', 'is_active', 'technician')
    list_filter = ('frequency', 'is_active', 'is_general', 'technician')
    search_fields = ('title', 'description', 'technician__username', 'technician__first_name', 'technician__last_name')
    readonly_fields = ('last_notification', 'created', 'modified')
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'start_datetime', 'end_datetime', 'frequency', 'interval', 'until', 'is_active')
        }),
        ('General or Asset-Specific', {
            'fields': ('is_general', 'asset')
        }),
        ('Technician Info', {
            'fields': ('technician',)
        }),
        ('Timestamps', {
            'fields': ('last_notification', 'created', 'modified')
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)



admin.site.register(Department, DepartmentAdmin)
admin.site.register(Asset, AssetAdmin)
admin.site.register(AssetActivity, AssetActivityAdmin)
admin.site.register(MaintenanceSchedule, MaintenanceScheduleAdmin)
