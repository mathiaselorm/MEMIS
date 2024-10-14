from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import Category, Item, Supplier

# Base Admin for models with soft deletion and historical records
class SoftDeletionAdmin(SimpleHistoryAdmin):
    list_display = ('__str__', 'is_deleted', 'deleted_at', 'created_at', 'updated_at')
    list_filter = ('is_deleted', 'created_at', 'updated_at')
    search_fields = ('name', 'descriptive_name', 'batch_number')
    actions = ['really_delete_selected', 'restore_selected']

    def get_queryset(self, request):
        """
        Override to filter out soft-deleted objects unless requested.
        """
        qs = super().get_queryset(request)
        if request.GET.get('is_deleted__exact') is not None:
            return qs  # Include both deleted and non-deleted if filter is explicitly set
        return qs.filter(is_deleted=False)  # Default to only showing non-deleted objects

    def really_delete_selected(self, request, queryset):
        """
        Permanently delete selected objects (bypass soft delete).
        """
        queryset.delete()

    really_delete_selected.short_description = "Permanently delete selected items"

    def restore_selected(self, request, queryset):
        """
        Restore soft-deleted objects.
        """
        queryset.update(is_deleted=False, deleted_at=None)

    restore_selected.short_description = "Restore selected items"


# Custom Category Admin
@admin.register(Category)
class CategoryAdmin(SoftDeletionAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at', 'is_deleted')
    search_fields = ['name', 'description']
    list_filter = SoftDeletionAdmin.list_filter + ('name',)
    actions = SoftDeletionAdmin.actions

    def get_queryset(self, request):
        """
        Override to include all objects (including deleted) for this model.
        """
        return super().get_queryset(request)


# Custom Supplier Admin
@admin.register(Supplier)
class SupplierAdmin(SoftDeletionAdmin):
    list_display = ('name', 'contact_info', 'created_at', 'updated_at', 'is_deleted')
    search_fields = ['name', 'contact_info']
    list_filter = SoftDeletionAdmin.list_filter + ('name',)
    actions = SoftDeletionAdmin.actions

    def get_queryset(self, request):
        """
        Override to include all objects (including deleted) for this model.
        """
        return super().get_queryset(request)


# Custom Item Admin
@admin.register(Item)
class ItemAdmin(SoftDeletionAdmin):
    list_display = ('item_id', 'descriptive_name', 'category', 'current_stock', 'stock_status', 'location', 'supplier', 'created_at', 'updated_at', 'is_deleted')
    list_filter = SoftDeletionAdmin.list_filter + ('category', 'supplier', 'location')
    search_fields = ['descriptive_name', 'batch_number', 'location']
    actions = SoftDeletionAdmin.actions + ['additional_item_specific_action']

    def additional_item_specific_action(self, request, queryset):
        """
        Define any custom item-specific actions here.
        """
        # Example action logic (e.g., mass update, alert, etc.)
        queryset.update(current_stock=0)  # This example resets stock to 0
        self.message_user(request, "Selected items' stock has been reset to 0.")

    additional_item_specific_action.short_description = "Reset stock to 0 for selected items"
