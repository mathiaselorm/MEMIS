import logging
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from .models import UserProfile
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


logger = logging.getLogger(__name__)

# Retrieve the custom user model
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the user model.
    """
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'date_joined', 'last_login')
        read_only_fields = ('date_joined', 'last_login')
        extra_kwargs = {
            'first_name': {'label': _("First Name")},
            'last_name': {'label': _("Last Name")},
            'phone_number': {'label': _("Phone Number")},
        }

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.save()
        return instance

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the user profile model, handling nested updates.
    """
    user = UserSerializer(read_only=False)

    class Meta:
        model = UserProfile
        fields = ('user', 'bio', 'birth_date')

    @transaction.atomic
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user_serializer = self.fields['user']
        user_serializer.update(instance.user, user_data)

        # UserProfile instance update
        instance.bio = validated_data.get('bio', instance.bio)
        instance.birth_date = validated_data.get('birth_date', instance.birth_date)
        instance.save()
        return instance
    

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration, with password confirmation logic.
    """
    password_confirm = serializers.CharField(style={'input_type': 'password'}, write_only=True, label=_("Confirm Password"))

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'password', 'password_confirm')
        extra_kwargs = {
            'password': {'write_only': True, 'label': _("Password")},
        }

    def validate(self, data):
        # Custom validation for password confirmation
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password": _("Password fields didn't match.")})

        # Enhanced password strength validation
        if len(data['password']) < 8:
            raise serializers.ValidationError({"password": _("Password must be at least 8 characters long.")})
        if not any(char.isdigit() for char in data['password']):
            raise serializers.ValidationError({"password": _("The password must include at least one number.")})
        if not any(char.isalpha() for char in data['password']):
            raise serializers.ValidationError({"password": _("The password must include at least one letter.")})

        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password')
        try:
            user = User.objects.create_user(password=password, **validated_data)
            logger.info(f"User created successfully: {user.email}")
        except ValidationError as e:
            logger.error(f"User creation failed: {e}")
            raise serializers.ValidationError({"user": _("User could not be created. Please ensure all fields are correct.")})
        except Exception as e:
            logger.error(f"Unexpected error during user creation: {e}")
            raise serializers.ValidationError({"user": _("An unexpected error occurred. Please try again.")})
        return user

    
class GoogleAuthSerializer(serializers.Serializer):
    """
    Serializer for Google OAuth2 authentication.
    """
    id_token = serializers.CharField(write_only=True, required=True)

class AppleAuthSerializer(serializers.Serializer):
    """
    Serializer for Apple OAuth2 authentication.
    """
    identity_token = serializers.CharField(write_only=True, required=True)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)

        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)

        # Add extra responses here
        data['user'] = {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'email': self.user.email,
            'phone_number': self.user.phone_number,
            'date_joined': self.user.date_joined,
            'last_login': self.user.last_login,
        }
        return data

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(label=_("Email Address"))

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            logger.error(f"Password reset requested for non-existent email: {value}")
            raise serializers.ValidationError(_("No user is associated with this email address."))
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

 
"""
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(label=_("Email"))
    password = serializers.CharField(label=_("Password"), style={'input_type': 'password'}, write_only=True)

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(_("User with this email does not exist."))
        return value
"""  