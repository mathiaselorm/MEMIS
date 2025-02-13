from django.contrib import admin
from .models import Category, Item

class StatusAdminMixin:
    """
    Mixin to add draft/publish actions to the admin panel for models with a status field.
    """
    actions = ['mark_as_draft', 'mark_as_published']

    def mark_as_draft(self, request, queryset):
        queryset.update(status=queryset.model.STATUS.draft)
    mark_as_draft.short_description = "Mark selected items as Draft"

    def mark_as_published(self, request, queryset):
        queryset.update(status=queryset.model.STATUS.published)
    mark_as_published.short_description = "Mark selected items as Published"

class CategoryAdmin(StatusAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'slug', 'status', 'created', 'modified', 'is_removed')
    search_fields = ('name',)
    readonly_fields = ('slug', 'created', 'modified')
    list_filter = ('status', 'is_removed')

    def get_queryset(self, request):
        # Include soft-deleted items
        return Category.all_objects.all()

class ItemAdmin(StatusAdminMixin, admin.ModelAdmin):
    list_display = (
        'descriptive_name', 'category', 'manufacturer', 'model_number', 'serial_number',
        'status', 'location', 'current_stock', 'stock_status', 'is_removed'
    )
    search_fields = ('descriptive_name', 'serial_number', 'manufacturer', 'model_number')
    list_filter = ('status', 'category', 'location', 'is_removed')
    readonly_fields = ('created', 'modified', 'stock_status')
    fieldsets = (
        (None, {
            'fields': ('descriptive_name', 'category', 'manufacturer', 'model_number', 'serial_number')
        }),
        ('Stock Information', {
            'fields': ('current_stock', 'location', 'status', 'is_removed')
        }),
        ('Metadata', {
            'fields': ('created', 'modified')
        }),
    )

    def get_queryset(self, request):
        # Include soft-deleted items
        return Item.all_objects.all()

# Register the models with customized admin classes
admin.site.register(Category, CategoryAdmin)
admin.site.register(Item, ItemAdmin)
