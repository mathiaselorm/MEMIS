from django.contrib import admin
from .models import Asset, Department


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'head', 'contact_phone', 'contact_email')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}  


class AssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'device_type', 'serial_number', 'status', 'department', 'manufacturer')
    list_filter = ('status', 'device_type', 'department')
    search_fields = ('name', 'serial_number', 'embossment_id')

    # Customize form layout - Optional
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




admin.site.register(Department, DepartmentAdmin)
admin.site.register(Asset, AssetAdmin)
