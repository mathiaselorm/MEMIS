from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm


class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser

    # Fields displayed in the list view
    list_display = ('id', 'first_name', 'last_name', 'email', 'phone_number', 'user_type', 'is_staff', 'is_active')
    list_filter = ('user_type', 'is_staff', 'is_active')
    list_display_links = ('id', 'email')

    # Fields displayed when viewing/editing a user
    fieldsets = (
        (None, {'fields': ('first_name', 'last_name', 'email', 'password', 'phone_number')}),
        (_('Permissions'), {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    # Fields displayed when adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'email', 'phone_number', 'password1', 'password2', 'user_type', 'is_staff', 'is_active')
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
