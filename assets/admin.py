from django.contrib import admin
from .models import Asset, Department, AssetStatus

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'head', 'contact_phone', 'contact_email')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}  

class AssetAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'device_type', 'serial_number', 'status', 'department', 'manufacturer')
    list_filter = ('status', 'device_type', 'department')
    search_fields = ('name', 'serial_number', 'embossment_id')
    readonly_fields = ('created_at', 'updated_at')  # Read-only fields
    fieldsets = (
        (None, {
            'fields': ('name', 'device_type', 'serial_number', 'embossment_id', 'quantity', 'image', )
        }),
        ('Availability', {
            'fields': ('status', 'department', 'is_archived', 'added_by')
        }),
        ('Details', {
            'fields': ('manufacturer', 'model', 'description', 'embossment_date', 'manufacturing_date', 'commission_date', 'decommission_date',)
        }),
    )

    def mark_as_active(modeladmin, request, queryset):
        queryset.update(status=AssetStatus.ACTIVE)

    mark_as_active.short_description = "Mark selected assets as active"
    
    actions = [mark_as_active]  # Custom action

admin.site.register(Department, DepartmentAdmin)
admin.site.register(Asset, AssetAdmin)
