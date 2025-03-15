from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view
from .serializers import NotificationSerializer
from .models import Notification






class NotificationListView(generics.ListAPIView):
    """
    List all notifications for the authenticated user.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Detect if this is a swagger fake view or if the user is not authenticated.
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return Notification.objects.none()
        
        return Notification.objects.filter(user=self.request.user).order_by('-created')

    @swagger_auto_schema(
        tags=['Notifications'],
        operation_description="Retrieve a list of notifications for the authenticated user.",
        responses={
            200: NotificationSerializer(many=True),
            401: openapi.Response(
                description="Unauthorized",
                examples={"application/json": {"detail": "Authentication credentials were not provided."}}
            )
        }
    )
    def get(self, request, *args, **kwargs):
        """
        List all notifications for the authenticated user.
        """
        return super().get(request, *args, **kwargs)


class NotificationDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update a notification (e.g., mark as read).
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def get_queryset(self):
        # If this is a swagger fake view or the user isn't authenticated, return an empty queryset.
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return Notification.objects.none()
        return Notification.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        tags=['Notifications'],
        operation_description="Retrieve a notification.",
        responses={
            200: NotificationSerializer,
            404: openapi.Response(
                description="Not found",
                examples={"application/json": {"detail": "Not found."}}
            )
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve a notification.
        """
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Notifications'],
        operation_description="Partially update a notification (e.g., mark as read).",
        request_body=NotificationSerializer,
        responses={
            200: NotificationSerializer,
            400: openapi.Response(
                description="Bad Request",
                examples={"application/json": {"detail": "Invalid data."}}
            ),
            404: openapi.Response(
                description="Not found",
                examples={"application/json": {"detail": "Not found."}}
            )
        }
    )
    def patch(self, request, *args, **kwargs):
        """
        Partially update a notification.
        """
        return super().patch(request, *args, **kwargs)



@swagger_auto_schema(
    method='post',
    operation_description="Mark all notifications as read.",
    responses={200: "All notifications marked as read."}
)
@api_view(['POST']) 
def mark_all_notifications_read(request):
    user = request.user
    if not user.is_authenticated:
        return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
    Notification.objects.filter(user=user, is_read=False).update(is_read=True)
    return Response({'detail': 'All notifications marked as read.'}, status=status.HTTP_200_OK)

