import logging
from django.contrib.auth import get_user_model, password_validation
from django.utils.translation import gettext_lazy as _
from django.utils.crypto import get_random_string
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django_rest_passwordreset.models import ResetPasswordToken
from django_rest_passwordreset.signals import reset_password_token_created
from datetime import timedelta



logger = logging.getLogger(__name__)

User = get_user_model()



import logging
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from accounts.models import CustomUser

User = CustomUser  # or use get_user_model() if preferred
logger = logging.getLogger(__name__)



class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.
    Allows updating user_role using human-readable strings.
    Excludes password and is_superuser from being updated.
    """
    user_role = serializers.CharField(label=_("User Role"))

    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'phone_number',
            'user_role', 'date_joined', 'last_login'
        )
        read_only_fields = ('id', 'date_joined', 'last_login')
        extra_kwargs = {
            'first_name': {'label': _("First Name")},
            'last_name': {'label': _("Last Name")},
            'phone_number': {'label': _("Phone Number")},
            'email': {'label': _("Email Address")}
        }

    def to_representation(self, instance):
        """
        Override to_representation to display user_role as its display string.
        """
        representation = super().to_representation(instance)
        representation['user_role'] = instance.get_user_role_display()
        return representation

    def validate_email(self, value):
        """
        Ensure the email is unique among non-superuser users.
        """
        if self.instance:
            if User.objects.filter(email=value).exclude(id=self.instance.id).exclude(is_superuser=True).exists():
                raise ValidationError(_("This email is already in use by another account."))
        else:
            if User.objects.filter(email=value).exclude(is_superuser=True).exists():
                raise ValidationError(_("This email is already in use by another account."))
        return value

    def validate_user_role(self, value):
        """
        Validate and map the human-readable role to internal value.
        Now, all authenticated users can assign user roles.
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise ValidationError(_("Authentication credentials were not provided."))

        # Map display string to internal value
        for role in User.UserRole:
            if value.strip().lower() == role.label.lower():
                return role.value
        raise ValidationError(_("Invalid role: %(value)s") % {'value': value})

    def update(self, instance, validated_data):
        """
        Update and return an existing `User` instance, given the validated data.
        Excludes changes to superuser status and sensitive fields.
        """
        # Define uneditable fields
        uneditable_fields = {'password', 'is_superuser'}
        validated_data = {k: v for k, v in validated_data.items() if k not in uneditable_fields}

        # Update user_role if provided
        if 'user_role' in validated_data:
            instance.user_role = validated_data.pop('user_role')

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

        # Generate a random default password
        default_password = get_random_string(length=8)

        # Create the user with the generated password
        user = User.objects.create_user(**validated_data)
        user.set_password(default_password)
        user.save()
        logger.info(f"User created successfully: {user.email}")

        # Trigger the password reset process
        token = ResetPasswordToken.objects.create(
            user=user,
            user_agent=self.context['request'].META.get('HTTP_USER_AGENT', ''),
            ip_address=self.context['request'].META.get('REMOTE_ADDR', ''),
        )

        # Send the password reset token via signal
        reset_password_token_created.send(
            sender=self.__class__,
            instance=self,
            reset_password_token=token,
            created_via='registration'
        )

        return user
    



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer to include user data.
    """
    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)

        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)

        # Add extra responses here
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'user_role': self.user.get_user_role_display(),}
        return data
    

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

        request_user = self.context['request'].user

        return instance

