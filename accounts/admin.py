from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, UserProfile
from .forms import CustomUserCreationForm, CustomUserChangeForm

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = _('profiles')
    fk_name = 'user'
    extra = 0  # Ensures there are no extra forms

class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    inlines = [UserProfileInline,]  # Ensuring this is a list
    list_display = ('id','first_name', 'last_name', 'email', 'phone_number', 'is_staff', 'is_active',)
    list_filter = ('is_staff', 'is_active',)
    list_display_links = ('id', 'email',)
    fieldsets = (
        (None, {'fields': ('first_name', 'last_name', 'email', 'password', 'phone_number')}),
        (_('Permissions'), {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'email', 'phone_number', 'password1', 'password2', 'is_staff', 'is_active')
        }),
    )
    search_fields = ('user__email', 'user__first_name', 'user__last_name',)
    ordering = ('email',)
    readonly_fields = ('last_login', 'date_joined',)

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'birth_date',)
    list_filter = ('birth_date',)
    search_fields = ('user__email', 'user__first_name', 'user__last_name',) 
    ordering = ('user',)

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
