from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, AuditLog  # Include CustomUser and AuditLog
from .forms import CustomUserCreationForm, CustomUserChangeForm


class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm  # For adding new users
    form = CustomUserChangeForm  # For updating existing users
    model = CustomUser

    # Fields displayed in the list view
    list_display = ('id', 'first_name', 'last_name', 'email', 'phone_number', 'user_role', 'is_staff', 'is_active')
    list_filter = ('user_role', 'is_staff', 'is_active', 'is_superuser')
    list_display_links = ('id', 'email')

    # Fields displayed when viewing/editing a user
    fieldsets = (
        (None, {'fields': ('first_name', 'last_name', 'email', 'password', 'phone_number', 'user_role')}),  # Include user_role
        (_('Permissions'), {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),  # Handle permissions
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    # Fields displayed when adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'email', 'phone_number', 'password1', 'password2', 'user_role', 'is_staff', 'is_active', 'is_superuser'),
        }),
    )

    # Search functionality
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    ordering = ('email',)
    readonly_fields = ('last_login', 'date_joined')

    # Enable the "delete selected users" action
    actions = ['delete_selected']

    def get_actions(self, request):
        actions = super().get_actions(request)
        # Ensure delete action is enabled
        if 'delete_selected' not in actions:
            actions['delete_selected'] = (self.delete_selected, 'delete_selected', _('Delete selected users'))
        return actions

    def delete_selected(self, request, queryset):
        """Custom logic if you want to do something extra before deletion"""
        queryset.delete()


# Register the CustomUser model with the custom admin interface
admin.site.register(CustomUser, CustomUserAdmin)


# Register the AuditLog model
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'target_user', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__email', 'target_user__email', 'action', 'details')


admin.site.register(AuditLog, AuditLogAdmin)
