from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import Category, Item, Supplier

# Admin for models with historical records and soft deletion
class SoftDeletionAdmin(SimpleHistoryAdmin):
    list_display = ('__str__', 'is_deleted', 'deleted_at', 'created_at', 'updated_at')
    list_filter = ('is_deleted', 'created_at', 'updated_at')
    search_fields = ('name', 'descriptive_name', 'batch_number')
    actions = ['really_delete_selected', 'restore_selected']

    def get_queryset(self, request):
        # Include soft-deleted items only if specifically requested
        qs = super().get_queryset(request)
        if request.GET.get('is_deleted__exact') is not None:
            return qs
        return qs.filter(is_deleted=False)

    def really_delete_selected(self, request, queryset):
        # Permanently delete selected items
        queryset.delete()

    really_delete_selected.short_description = "Permanently delete selected items"

    def restore_selected(self, request, queryset):
        # Restore soft-deleted items
        queryset.update(is_deleted=False, deleted_at=None)

    restore_selected.short_description = "Restore selected items"

# Custom admin classes
@admin.register(Category)
class CategoryAdmin(SoftDeletionAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at', 'is_deleted')
    search_fields = ['name', 'description']

@admin.register(Supplier)
class SupplierAdmin(SoftDeletionAdmin):
    list_display = ('name', 'contact_info', 'created_at', 'updated_at', 'is_deleted')
    search_fields = ['name', 'contact_info']

@admin.register(Item)
class ItemAdmin(SoftDeletionAdmin):
    list_display = ('item_id', 'descriptive_name', 'category', 'current_stock', 'stock_status', 'location', 'supplier', 'created_at', 'updated_at', 'is_deleted')
    list_filter = SoftDeletionAdmin.list_filter + ('category', 'supplier', 'location')
    search_fields = ['descriptive_name', 'batch_number', 'location']

    
"""
    actions = SoftDeletionAdmin.actions + [custom_action]
    def additional_item_specific_action(self, request, queryset):
        # Define any custom actions specific to items here
        pass
"""