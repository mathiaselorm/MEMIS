from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from .models import CustomUser, AuditLog
from .forms import CustomUserCreationForm, CustomUserChangeForm

class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm  # For adding new users
    form = CustomUserChangeForm        # For updating existing users
    model = CustomUser

    # Fields displayed in the list view
    list_display = (
        'id', 'first_name', 'last_name', 'email', 'phone_number',
        'get_user_role_display', 'is_staff', 'is_active'
    )
    list_filter = ('user_role', 'is_staff', 'is_active', 'is_superuser')
    list_display_links = ('id', 'email')

    # Fields displayed when viewing/editing a user
    fieldsets = (
        (None, {'fields': (
            'first_name', 'last_name', 'email', 'password', 'phone_number', 'user_role'
        )}),
        (_('Permissions'), {'fields': (
            'is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions'
        )}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    # Fields displayed when adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'first_name', 'last_name', 'email', 'phone_number',
                'password1', 'password2', 'user_role',
                'is_staff', 'is_active', 'is_superuser'
            ),
        }),
    )

    # Search functionality
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    ordering = ('email',)
    readonly_fields = ('last_login', 'date_joined')

    # Override methods to log deletions
    def delete_model(self, request, obj):
        """
        Delete a single model instance and log the deletion.
        """
        user_full_name = obj.get_full_name()
        obj.delete()
        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.ActionChoices.DELETE,
            target_user=obj,
            details=_('User deleted: %(full_name)s') % {'full_name': user_full_name}
        )
        messages.success(request, _("User '%(full_name)s' was deleted successfully.") % {'full_name': user_full_name})

    def delete_queryset(self, request, queryset):
        """
        Delete multiple model instances and log each deletion.
        """
        for obj in queryset:
            user_full_name = obj.get_full_name()
            obj.delete()
            AuditLog.objects.create(
                user=request.user,
                action=AuditLog.ActionChoices.DELETE,
                target_user=obj,
                details=_('User deleted: %(full_name)s') % {'full_name': user_full_name}
            )
        messages.success(request, _("Selected users were deleted successfully."))

    # Display the user role as human-readable text
    def get_user_role_display(self, obj):
        return obj.get_user_role_display()
    get_user_role_display.short_description = 'User Role'

class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user_full_name', 'action', 'target_user_full_name', 'details')
    list_filter = ('action', 'timestamp')
    search_fields = (
        'user__email', 'user__first_name', 'user__last_name',
        'target_user__email', 'target_user__first_name', 'target_user__last_name',
        'action', 'details'
    )
    ordering = ('-timestamp',)
    readonly_fields = ('user', 'action', 'target_user', 'details', 'timestamp')

    def user_full_name(self, obj):
        if obj.user:
            return obj.user.get_full_name()
        return 'N/A'  
    user_full_name.short_description = 'User'

    def target_user_full_name(self, obj):
        if obj.target_user:
            return obj.target_user.get_full_name()
        return 'N/A'
    target_user_full_name.short_description = 'Target User'
    

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(AuditLog, AuditLogAdmin)
