
from rest_framework import generics, permissions
from rest_framework.response import Response
from actstream.models import Action

from .serializers import ActionSerializer

class ActivityStreamView(generics.ListAPIView):
    """
    Lists all recent actions recorded by django-activity-stream.
    You can add filtering, pagination, or permission logic as needed.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ActionSerializer

    def get_queryset(self):
        """
        Return all actions, ordered by most recent first.
        You can add filters here if you only want certain events (e.g., only the user's events).
        """
        return Action.objects.order_by('-timestamp')

    def list(self, request, *args, **kwargs):
        """
        Optionally override list() if you want custom response structure.
        Otherwise, DRF's default list implementation is fine.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)



# def get_queryset(self):
#     user = self.request.user
#     return Action.objects.filter(
#         actor_object_id=user.id
#     ).order_by('-timestamp')
