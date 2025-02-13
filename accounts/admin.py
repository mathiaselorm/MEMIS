from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm

# Import django-activity-stream for logging deletions
from actstream import action

class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm  # For adding new users
    form = CustomUserChangeForm        # For updating existing users
    model = CustomUser

    list_display = (
        'id', 'first_name', 'last_name', 'email', 'phone_number',
        'get_user_role_display', 'is_staff', 'is_active'
    )
    list_filter = ('user_role', 'is_staff', 'is_active', 'is_superuser')
    list_display_links = ('id', 'email')

    fieldsets = (
        (None, {'fields': (
            'first_name', 'last_name', 'email', 'password', 'phone_number', 'user_role'
        )}),
        (_('Permissions'), {'fields': (
            'is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions'
        )}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

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

    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    ordering = ('email',)
    readonly_fields = ('last_login', 'date_joined')

    def delete_model(self, request, obj):
        """
        Delete a single user instance, then record the event in django-activity-stream.
        """
        user_full_name = obj.get_full_name()
        
        # Actually delete the user
        obj.delete()
        
        # Record the deletion in django-activity-stream
        action.send(
            request.user,
            verb='deleted user',
            target=obj,
            description=f"User deleted: {user_full_name}"
        )
        
        messages.success(
            request,
            _("User '%(full_name)s' was deleted successfully.") % {'full_name': user_full_name}
        )

    def delete_queryset(self, request, queryset):
        """
        Delete multiple user instances, then record each event in django-activity-stream.
        """
        for obj in queryset:
            user_full_name = obj.get_full_name()
            obj.delete()
            # Log each deletion
            action.send(
                request.user,
                verb='deleted user',
                target=obj,
                description=f"User deleted: {user_full_name}"
            )

        messages.success(request, _("Selected users were deleted successfully."))

    def get_user_role_display(self, obj):
        return obj.get_user_role_display()
    get_user_role_display.short_description = 'User Role'


admin.site.register(CustomUser, CustomUserAdmin)
