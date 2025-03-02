from django.contrib import admin
from .models import Item

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'item_code', 'category', 'quantity', 'location', 'stock_status', 'created', 'modified'
    )
    search_fields = ('name', 'item_code')
    list_filter = ('category', 'location')
    readonly_fields = ('created', 'modified', 'stock_status')
    fieldsets = (
        (None, {
            'fields': ('name', 'item_code', 'category', 'description')
        }),
        ('Inventory Information', {
            'fields': ('quantity', 'location')
        }),
        ('Metadata', {
            'fields': ('created', 'modified')
        }),
    )

