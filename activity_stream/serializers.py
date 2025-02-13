from rest_framework import serializers
from actstream.models import Action

class ActionSerializer(serializers.ModelSerializer):
    """
    Serializer for django-activity-stream's Action model.
    Exposes basic fields, plus some human-readable fields.
    """

    actor_name = serializers.SerializerMethodField()
    target_name = serializers.SerializerMethodField()

    class Meta:
        model = Action
        # Adjust the fields you want to expose
        fields = [
            'id',
            'verb',
            'description',
            'timestamp',
            'actor_content_type',
            'actor_object_id',
            'target_content_type',
            'target_object_id',
            'actor_name',
            'target_name',
        ]

    def get_actor_name(self, obj):
        if obj.actor:
            return str(obj.actor)
        return None

    def get_target_name(self, obj):
        if obj.target:
            return str(obj.target)
        return None
