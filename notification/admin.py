from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_read', 'created', 'modified')
    list_filter = ('is_read',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'message')
    readonly_fields = ('created', 'modified')
    fieldsets = (
        (None, {
            'fields': ('user', 'message', 'link', 'is_read')
        }),
        ('Timestamps', {
            'fields': ('created', 'modified')
        }),
    )