from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'message', 'link', 'is_read', 'created', 'modified', 'user'
        ]
        read_only_fields = ['id', 'created', 'modified', 'user']
