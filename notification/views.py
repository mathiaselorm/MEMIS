from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from rest_framework.decorators import api_view, permission_classes
from .serializers import NotificationSerializer
from .models import Notification






class NotificationListView(generics.ListAPIView):
    """
    List all notifications for the authenticated user.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return an empty queryset for swagger fake view or if user is not authenticated.
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return Notification.objects.none()
        return Notification.objects.filter(user=self.request.user).order_by('-created')

    @extend_schema(
        summary="List Notifications",
        description="Retrieve a list of notifications for the authenticated user.",
        responses={
            200: OpenApiResponse(
                description="Notifications retrieved successfully.",
                response=NotificationSerializer(many=True)
            ),
            401: OpenApiResponse(
                description="Unauthorized",
                examples=[OpenApiExample(
                    "Unauthorized",
                    value={"detail": "Authentication credentials were not provided."},
                    response_only=True
                )]
            )
        },
        tags=["Notifications"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class NotificationDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update a notification (e.g., mark as read).
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def get_queryset(self):
        # Return an empty queryset for swagger fake view or if user is not authenticated.
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return Notification.objects.none()
        return Notification.objects.filter(user=self.request.user)

    @extend_schema(
        summary="Retrieve Notification",
        description="Retrieve a notification.",
        responses={
            200: OpenApiResponse(
                description="Notification retrieved successfully.",
                response=NotificationSerializer
            ),
            404: OpenApiResponse(
                description="Not found",
                examples=[OpenApiExample(
                    "Not Found",
                    value={"detail": "Not found."},
                    response_only=True
                )]
            )
        },
        tags=["Notifications"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Partially Update Notification",
        description="Partially update a notification (e.g., mark as read).",
        request=NotificationSerializer,
        responses={
            200: OpenApiResponse(
                description="Notification updated successfully.",
                response=NotificationSerializer
            ),
            400: OpenApiResponse(
                description="Bad Request",
                examples=[OpenApiExample(
                    "Bad Request",
                    value={"detail": "Invalid data."},
                    response_only=True
                )]
            ),
            404: OpenApiResponse(
                description="Not found",
                examples=[OpenApiExample(
                    "Not Found",
                    value={"detail": "Not found."},
                    response_only=True
                )]
            )
        },
        tags=["Notifications"]
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


@extend_schema(
    methods=['POST'],
    summary="Mark All Notifications as Read",
    description="Mark all notifications as read for the authenticated user.",
    responses={
        200: OpenApiResponse(
            description="All notifications marked as read successfully.",
            examples=[OpenApiExample(
                "Mark All Read",
                value={"detail": "All notifications marked as read."},
                response_only=True
            )]
        )
    },
    tags=["Notifications"]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read(request):
    user = request.user
    if not user.is_authenticated:
        return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
    Notification.objects.filter(user=user, is_read=False).update(is_read=True)
    return Response({'detail': 'All notifications marked as read.'}, status=status.HTTP_200_OK)