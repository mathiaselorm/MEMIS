import logging
from django.contrib.auth import get_user_model, password_validation
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import AuditLog
from django_rest_passwordreset.models import ResetPasswordToken
from django_rest_passwordreset.signals import reset_password_token_created



logger = logging.getLogger(__name__)

# Retrieve the custom user model
User = get_user_model()



class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the user model.
    Provides additional validation and excludes superusers from updates.
    """
    user_role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'phone_number',
            'user_role', 'date_joined', 'last_login'
        )
        read_only_fields = ('date_joined', 'last_login')
        extra_kwargs = {
            'first_name': {'label': _("First Name")},
            'last_name': {'label': _("Last Name")},
            'phone_number': {'label': _("Phone Number")},
            'email': {'label': _("Email Address")}
        }

    def get_user_role(self, obj):
        """Return the display name of the user's role."""
        return obj.get_user_role_display()

    def validate_email(self, value):
        """
        Ensure the email is unique among non-superuser users.
        """
        if User.objects.filter(email=value).exclude(id=self.instance.id).exclude(is_superuser=True).exists():
            raise ValidationError(_("This email is already in use by another account."))
        return value

    def update(self, instance, validated_data):
        """
        Update and return an existing `User` instance, given the validated data.
        Excludes changes to superuser status and sensitive fields.
        """
        uneditable_fields = {'password', 'is_superuser'}
        validated_data = {k: v for k, v in validated_data.items() if k not in uneditable_fields}

        # Map display string to internal role value if `user_role` is updated
        if 'user_role' in validated_data:
            new_role_display = validated_data.pop('user_role')
            new_role_value = next(
                (role.value for role in User.UseRole if role.label == new_role_display), 
                None
            )
            if new_role_value is None:
                raise ValidationError({"user_role": _("Invalid role provided.")})
            instance.user_role = new_role_value

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Log updates
        updated_fields = ', '.join(validated_data.keys())
        logger.info(f"User {instance.email} updated fields: {updated_fields} successfully.")

        return instance




class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    user_role = serializers.CharField(label=_("User Role"))

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'user_role')

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise ValidationError(_("This email is already in use."))
        return value.lower()

    def validate_user_role(self, value):
        """
        Custom validation for `user_role`.
        Accepts role as a string and converts it to the corresponding integer value.
        """
        if isinstance(value, str):
            for role in User.UserRole:
                if value.strip().lower() == role.label.lower():
                    return role.value  # Return the integer value
            raise ValidationError({"user_role": _("Invalid role: %(value)s") % {'value': value}})
        raise ValidationError({"user_role": _("Invalid type for user_role: %(type)s") % {'type': type(value).__name__}})

    def validate(self, data):
        # Role-based validation
        request_user = self.context['request'].user

        # Superadmin can create any account type
        if request_user.user_role == User.UserRole.SUPERADMIN:
            return data

        # Admin can create Admin and Technician accounts
        if request_user.user_role == User.UserRole.ADMIN:
            if data.get('user_role') == User.UserRole.SUPERADMIN.value:
                raise ValidationError({"user_role": _("Admins cannot create Superadmin accounts.")})
            return data

        # Technicians cannot create any accounts
        raise ValidationError({"user_role": _("You do not have permission to create accounts.")})

    def create(self, validated_data):
        user_role_value = validated_data.pop('user_role')
        validated_data['user_role'] = user_role_value

        # Create the user without a password
        user = User.objects.create_user(**validated_data)
        user.set_unusable_password()
        user.save()
        logger.info(f"User created successfully: {user.email}")

        # Trigger the password reset process
        token = ResetPasswordToken.objects.create(
            user=user,
            user_agent=self.context['request'].META.get('HTTP_USER_AGENT', ''),
            ip_address=self.context['request'].META.get('REMOTE_ADDR', ''),
        )

        # Send the reset password token created signal with additional context
        reset_password_token_created.send(
            sender=self.__class__,
            instance=self,
            reset_password_token=token,
            created_via='registration'
        )

        return user





class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['email'] = user.email
        token['user_role'] = user.get_user_role_display()  # Include role display
        
        return token
    

class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(style={'input_type': 'password'}, write_only=True, label=_("Old Password"))
    new_password = serializers.CharField(style={'input_type': 'password'}, write_only=True, label=_("New Password"))

    def validate(self, data):
        user = self.context['request'].user

        # Check if the old password is correct
        if not user.check_password(data['old_password']):
            raise serializers.ValidationError({"old_password": _("The old password is incorrect.")})

        # Validate the new password
        password_validation.validate_password(data['new_password'], user)

        return data

    def save(self, **kwargs):
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        logger.info(f"User {user.email} changed their password.")
        return user
    

# Serializer for Role Assignment (Admin Only)
class RoleAssignmentSerializer(serializers.ModelSerializer):
    """
    Serializer to assign or change user roles.
    """
    new_role = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'user_role', 'new_role')
        read_only_fields = ('email', 'first_name', 'last_name', 'user_role')

    def validate_new_role(self, value):
        """
        Custom validation for `new_role`.
        """
        if isinstance(value, str):
            for role in User.UserRole:
                if value.strip().lower() == role.label.lower():
                    role_value = role.value
                    break
            else:
                raise ValidationError({"new_role": _("Invalid role: %(value)s") % {'value': value}})
        else:
            raise ValidationError({"new_role": _("Invalid type for new_role: %(type)s") % {'type': type(value).__name__}})

        request_user = self.context['request'].user

        # Permission-based validation
        if request_user.user_role == User.UserRole.SUPERADMIN:
            return role_value

        if request_user.user_role == User.UserRole.ADMIN:
            if role_value == User.UserRole.SUPERADMIN:
                raise ValidationError(_("Admins cannot assign the Superadmin role."))
            return role_value

        # Technicians cannot assign roles
        raise ValidationError(_("You do not have permission to assign roles."))

    def update(self, instance, validated_data):
        new_role = validated_data.get('new_role')
        instance.user_role = new_role
        instance.save()

        # Log the role change
        AuditLog.objects.create(
            user=self.context['request'].user,
            action=AuditLog.ActionChoices.ASSIGN_ROLE,
            target_user=instance,
            details=f"Changed role to {instance.get_user_role_display()}."
        )

        return instance




# AuditLog Serializer
class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for AuditLog model, to track user actions.
    """
    user = serializers.SerializerMethodField()
    target_user = serializers.SerializerMethodField()
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'action', 'action_display', 'target_user', 'timestamp', 'details']
        read_only_fields = ['id', 'user', 'action', 'action_display', 'target_user', 'timestamp', 'details']

    def get_user(self, obj):
        if obj.user:
            return obj.user.get_full_name()
        return _("System")

    def get_target_user(self, obj):
        if obj.target_user:
            return obj.target_user.get_full_name()
        return None
