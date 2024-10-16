from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

CustomUser = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    """
    A form for creating new users. Includes all the required
    fields, plus user_role and a repeated password.
    """
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'phone_number', 'user_role',)
        labels = {
            'email': _('Email Address'),
            'first_name': _('First Name'),
            'last_name': _('Last Name'),
            'phone_number': _('Phone Number'),
            'user_role': _('User Role'),
        }
        help_texts = {
            'email': _('A valid email address, please.'),
            'user_role': _('Designates whether the user is an admin or technician.'),
        }

    def clean_email(self):
        """
        Validate that the supplied email address is unique for the site.
        """
        email = self.cleaned_data['email']
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError(_("A user with that email already exists."))
        return email

    def save(self, commit=True):
        """
        Save the provided password in hashed format.
        Set user_type based on the user creating the account.
        """
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        # Automatically set `user_type` for non-superusers
        if self.cleaned_data.get('user_role') is None and not self.request.user.is_superuser:
            user.user_role = 3  # Default to technician if created by an Admin

        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    """
    A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    class Meta(UserChangeForm.Meta):
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'phone_number', 'user_role', 'is_active', 'is_staff')
        labels = {
            'email': _('Email Address'),
            'first_name': _('First Name'),
            'last_name': _('Last Name'),
            'phone_number': _('Phone Number'),
            'user_role': _('User Role'),
            'is_active': _('Active'),
            'is_staff': _('Staff Status'),
        }
        help_texts = {
            'is_active': _('Designates whether this user should be treated as active. Unselect this instead of deleting accounts.'),
            'is_staff': _('Designates whether the user can log into this admin site.'),
            'user_role': _('Designates whether the user is an admin or technician.'),
        }
