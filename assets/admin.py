from django.contrib import admin
from .models import Asset,  MaintenanceReport, Department


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
            'fields': ('name', 'device_type', 'serial_number', 'embossment_id', 'quantity', )
        }),
        ('Availability', {
            'fields': ('status', 'department', 'is_archived', 'added_by')
        }),
        ('Details', {
            'fields': ('manufacturer', 'model', 'description', 'embossment_date', 'manufacturing_date', 'commission_date', 'decommission_date',)
        }),

    )



class MaintenanceReportAdmin(admin.ModelAdmin):
    list_display = ('asset', 'maintenance_type', 'date_performed', 'added_by')
    list_filter = ('maintenance_type', 'date_performed', 'asset__department')
    search_fields = ('asset__name', 'details')

    def get_department(self, obj):
        return obj.asset.department.name
    get_department.admin_order_field = 'asset__department'  # Allows sorting
    get_department.short_description = 'Department'



admin.site.register(Department, DepartmentAdmin)
admin.site.register(Asset, AssetAdmin)
admin.site.register(MaintenanceReport, MaintenanceReportAdmin)
