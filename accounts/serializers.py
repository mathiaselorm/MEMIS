import logging
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .tasks import send_welcome_email
import traceback


from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings


logger = logging.getLogger(__name__)

# Retrieve the custom user model
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the user model.
    """
    user_type = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'date_joined', 'last_login', 'user_type')
        read_only_fields = ('date_joined', 'last_login', 'user_type')
        extra_kwargs = {
            'first_name': {'label': _("First Name")},
            'last_name': {'label': _("Last Name")},
            'phone_number': {'label': _("Phone Number")},
        }

    def get_user_type(self, obj):
        return obj.get_user_type_display()
    
    def update(self, instance, validated_data):
        validated_data.pop('email', None)  # Prevent email from being updated
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.save()
        logger.info(f"User {instance.email} updated their profile successfully.")
        return instance


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration, with password confirmation logic.
    """
    password_confirm = serializers.CharField(style={'input_type': 'password'}, write_only=True, label=_("Confirm Password"))

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'password', 'password_confirm', 'user_type')
        extra_kwargs = {
            'password': {'write_only': True, 'label': _("Password")},
        }

    def validate(self, data):
        # Custom validation for password confirmation
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password": _("Password fields didn't match.")})

        # Password strength validation
        if len(data['password']) < 8:
            raise serializers.ValidationError({"password": _("Password must be at least 8 characters long.")})
        if not any(char.isdigit() for char in data['password']):
            raise serializers.ValidationError({"password": _("The password must include at least one number.")})
        if not any(char.isalpha() for char in data['password']):
            raise serializers.ValidationError({"password": _("The password must include at least one letter.")})

        # Role-based validation
        request_user = self.context['request'].user
        
        # Superuser can create any account type
        if request_user.user_type == User.UserType.SUPERADMIN:
            return data

        # Admin can only create Technician accounts
        if request_user.user_type == User.UserType.ADMIN:  # Admin user
            if data.get('user_type') == User.UserType.ADMIN:
                raise serializers.ValidationError({"user_type": _("Admins cannot create other Admin accounts.")})
             # Default to Technician if Admin is creating the account
            data['user_type'] = User.UserType.TECHNICIAN  # Admin can only create Technician accounts

        if request_user.user_type == User.UserType.TECHNICIAN:  # Technicians cannot create any accounts
            raise serializers.ValidationError({"user_type": _("Technicians cannot create any accounts.")})

        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm', None)
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
        token['user_type'] = user.user_type 
        token['phone_number'] = user.phone_number

        return token


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(label=_("Email Address"))

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            logger.error(f"Password reset requested for non-existent email: {value}")
            raise serializers.ValidationError(_("If an account exists with this email, you will receive a password reset link."))
        return value

class PasswordResetSerializer(serializers.Serializer):
    new_password = serializers.CharField(style={'input_type': 'password'}, write_only=True, label=_("New Password"))
    confirm_password = serializers.CharField(style={'input_type': 'password'}, write_only=True, label=_("Confirm New Password"))

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            logger.error("Password reset attempt with non-matching passwords.")
            raise serializers.ValidationError({"confirm_password": _("The two password fields must match.")})
        
        # Additional password strength validation can be implemented here
        if len(data['new_password']) < 8:
            raise serializers.ValidationError({"new_password": _("The password must be at least 8 characters long.")})
        if not any(char.isdigit() for char in data['new_password']):
            raise serializers.ValidationError({"new_password": _("The password must include at least one numeral.")})
        if not any(char.isalpha() for char in data['new_password']):
            raise serializers.ValidationError({"new_password": _("The password must include at least one letter.")})
        #if not any(char in '!@#$%^&*()' for char in data['new_password']):
           # raise serializers.ValidationError({"new_password": _("The password must include at least one special character (!@#$%^&*()).")})

        return data

 