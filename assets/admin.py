from django.contrib import admin
from .models import Asset, Department

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'head', 'status', 'contact_phone', 'contact_email')
    search_fields = ('name',)
    readonly_fields = ('slug',)

class AssetAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'device_type', 'serial_number', 'status',
        'operational_status', 'department', 'manufacturer'
    )
    list_filter = ('status', 'operational_status', 'device_type', 'department')
    search_fields = ('name', 'serial_number', 'embossment_id')
    readonly_fields = ('created', 'modified', 'added_by')  # Read-only fields
    fieldsets = (
        (None, {
            'fields': ('name', 'device_type', 'serial_number', 'embossment_id', 'quantity', 'image')
        }),
        ('Availability', {
            'fields': ('status', 'operational_status', 'department', 'is_removed', 'added_by')
        }),
        ('Details', {
            'fields': (
                'manufacturer', 'model', 'description', 'embossment_date',
                'manufacturing_date', 'commission_date', 'decommission_date'
            )
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            # Set 'added_by' to the current user on creation
            obj.added_by = request.user
        super().save_model(request, obj, form, change)

    def mark_as_active(self, request, queryset):
        queryset.update(operational_status='active')
    mark_as_active.short_description = "Mark selected assets as operationally active"

    actions = [mark_as_active]  # Custom action

admin.site.register(Department, DepartmentAdmin)
admin.site.register(Asset, AssetAdmin)
