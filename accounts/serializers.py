import logging
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import AuditLog
from .tasks import send_welcome_email

import traceback
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator




logger = logging.getLogger(__name__)

# Retrieve the custom user model
User = get_user_model()



class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the user model.
    """
    user_role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'phone_number', 'user_role', 'date_joined', 'last_login')
        read_only_fields = ('date_joined', 'last_login', 'user_role')
        extra_kwargs = {
            'first_name': {'label': _("First Name")},
            'last_name': {'label': _("Last Name")},
            'phone_number': {'label': _("Phone Number")},
        }

    def get_user_role(self, obj):
        return obj.get_user_role_display()  # Align with `choices` field in model
    
    def update(self, instance, validated_data):
        validated_data.pop('email', None)  # Prevent email from being updated
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.save()
        logger.info(f"User {instance.first_name} updated their profile successfully.")
        
        return instance



class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration, with password confirmation logic.
    """
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True, label=_("Password"))
    user_role = serializers.ChoiceField(choices=User.UseRole.choices, label=_("User Role"))


    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'password', 'user_role')
        extra_kwargs = {
            'password': {'write_only': True, 'label': _("Password")},
        }
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(_("This email is already in use."))
        return value

    def validate(self, data):
        # Password strength validation
        if len(data['password']) < 8:
            raise serializers.ValidationError({"password": _("Password must be at least 8 characters long.")})
        if not any(char.isdigit() for char in data['password']):
            raise serializers.ValidationError({"password": _("The password must include at least one number.")})
        if not any(char.isalpha() for char in data['password']):
            raise serializers.ValidationError({"password": _("The password must include at least one letter.")})

        # Role-based validation
        request_user = self.context['request'].user
        
        # Superadmin can create any account type
        if request_user.user_role == User.UseRole.SUPERADMIN:
            return data

        # Admin can create both Admin and Technician accounts
        if request_user.user_role == User.UseRole.ADMIN:
            if data.get('user_role') == User.UseRole.SUPERADMIN:
                raise serializers.ValidationError({"user_role": _("Admins cannot create Superadmin accounts.")})
            return data

        # Technicians cannot create any accounts
        if request_user.user_role == User.UseRole.TECHNICIAN:
            raise serializers.ValidationError({"user_role": _("Technicians cannot create any accounts.")})

        return data

    def create(self, validated_data):
        password = validated_data.pop('password')

        try:
            # Create the user
            user = User.objects.create_user(password=password, **validated_data)
            logger.info(f"User created successfully: {user.email}")

            # Send email to the newly created user to set/change their password
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = self.context['request'].build_absolute_uri(
                reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )

            # Trigger email to set up the password
            send_welcome_email(user.email, user.pk, reset_url)
            
        except ValidationError as e:
            logger.error(f"User creation failed due to validation error: {e}")
            raise serializers.ValidationError({"user": _("User could not be created. Please ensure all fields are correct.")})
        
        except Exception as e:
            # Log the full traceback for debugging
            logger.error(f"Unexpected error during user creation: {traceback.format_exc()}")
            raise serializers.ValidationError({"error": "An unexpected error occurred. Please try again."})

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
        token['phone_number'] = user.phone_number

        return token



class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(label=_("Email Address"))
    frontend_url = serializers.URLField() 

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            logger.error(f"Password reset requested for non-existent email: {value}")
            raise serializers.ValidationError(_("No user is associated with this email address."))
        return value

class PasswordResetSerializer(serializers.Serializer):
    new_password = serializers.CharField(style={'input_type': 'password'}, write_only=True, label=_("New Password"))

    def validate(self, data):
        if len(data['new_password']) < 8:
            raise serializers.ValidationError({"new_password": _("The password must be at least 8 characters long.")})
        if not any(char.isdigit() for char in data['new_password']):
            raise serializers.ValidationError({"new_password": _("The password must include at least one numeral.")})
        if not any(char.isalpha() for char in data['new_password']):
            raise serializers.ValidationError({"new_password": _("The password must include at least one letter.")})
        return data


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(style={'input_type': 'password'}, write_only=True, label=_("Old Password"))
    new_password = serializers.CharField(style={'input_type': 'password'}, write_only=True, label=_("New Password"))

    def validate(self, data):
        user = self.context['request'].user

        # Check if the old password is correct
        if not user.check_password(data['old_password']):
            raise serializers.ValidationError({"old_password": _("The old password is incorrect.")})

        # Additional password strength validation
        if len(data['new_password']) < 8:
            raise serializers.ValidationError({"new_password": _("The password must be at least 8 characters long.")})
        if not any(char.isdigit() for char in data['new_password']):
            raise serializers.ValidationError({"new_password": _("The password must include at least one numeral.")})
        if not any(char.isalpha() for char in data['new_password']):
            raise serializers.ValidationError({"new_password": _("The password must include at least one letter.")})

        return data
    

# Serializer for Role Assignment (Admin Only)
class RoleAssignmentSerializer(serializers.Serializer):
    """
    Serializer to assign or change user roles.
    Admins can change the role of other users based on their first name.
    """
    first_name = serializers.CharField(max_length=150)  # Field to accept user's first name
    new_role = serializers.ChoiceField(choices=[(role.name, role.label) for role in User.UseRole])

    def update(self, instance, validated_data):
        # Fetch the user by first name (for simplicity, assumes unique first names)
        try:
            user = User.objects.get(first_name=validated_data['first_name'])
        except User.DoesNotExist:
            raise serializers.ValidationError({"first_name": _("User with the given first name does not exist.")})

        new_role_name = validated_data['new_role']

        # Map the role name to its corresponding integer value
        new_role = next(role.value for role in User.UseRole if role.name == new_role_name)

        # Check if the request user is an admin or superuser
        request_user = self.context['request'].user
        if not request_user.is_superuser and request_user.user_role != User.UseRole.ADMIN:
            raise serializers.ValidationError("You do not have permission to assign roles.")
        
        # Ensure Admins cannot assign Superadmin role
        if request_user.user_role == User.UseRole.ADMIN and new_role == User.UseRole.SUPERADMIN:
            raise serializers.ValidationError("Admins cannot assign the Superadmin role.")

        # Update the user's role
        user.user_role = new_role
        user.save()

        # Log the role change
        from .signals import log_role_assignment
        log_role_assignment(request_user, user, new_role)

        return user



# AuditLog Serializer
class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for AuditLog model, to track user actions.
    """
    user = serializers.SerializerMethodField()  # Use full name for user
    target_user = serializers.SerializerMethodField()  # Use full name for target_user

    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'action', 'target_user', 'timestamp', 'details']
        read_only_fields = ['id', 'user', 'action', 'target_user', 'timestamp', 'details']

    def get_user(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"  # Full name for user
    
    def get_target_user(self, obj):
        if obj.target_user:
            return f"{obj.target_user.first_name} {obj.target_user.last_name}"  # Full name for target_user
        return None

        
        






# Custom validation for password confirmation
# if data['password'] != data['password_confirm']:
#     raise serializers.ValidationError({"password": _("Password fields didn't match.")})     

#if not any(char in '!@#$%^&*()' for char in data['new_password']):
    # raise serializers.ValidationError({"new_password": _("The password must include at least one special character (!@#$%^&*()).")})