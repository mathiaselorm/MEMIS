# inventory/views.py

from django.db.models import F, Value, CharField, Case, When
from rest_framework import generics, filters, status
from django_filters.rest_framework import DjangoFilterBackend, CharFilter, FilterSet
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Import django-activity-stream
from actstream import action

# Local imports
from accounts.permissions import IsAdminOrSuperAdmin
from .models import Item
from .serializers import (
    ItemReadSerializer, ItemWriteSerializer,
)







class ItemListCreateView(generics.ListCreateAPIView):
    """
    Retrieve a list of items or create a new item.
    Supports filtering, search, and sorting.
    """
    permission_classes = [IsAuthenticated]
    queryset = Item.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ItemWriteSerializer
        return ItemReadSerializer

    @swagger_auto_schema(
        tags=['Inventory Items'],
        operation_description="Retrieve a list of items.",
        responses={200: ItemReadSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    swagger_auto_schema(
        tags=['Inventory Items'],
        operation_description="Create a new item.",
        request_body=ItemWriteSerializer,
        responses={
            201: openapi.Response(
                description="Item created successfully.",
                schema=ItemReadSerializer()
            ),
            400: "Invalid input, object invalid."
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Create a new item and log the creation in the activity stream.
        """
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            item_id = response.data.get('id')
            try:
                item_instance = Item.objects.get(id=item_id)
                action.send(
                    request.user,
                    verb='created inventory item',
                    target=item_instance,
                    description=f"Item: '{item_instance.name}' (Code: {item_instance.item_code})"
                )
            except Item.DoesNotExist:
                pass
        return response



class ItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete an item instance.
    """
    permission_classes = [IsAuthenticated]
    queryset = Item.objects.all() 
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ItemWriteSerializer
        return ItemReadSerializer

    def perform_destroy(self, instance):
        """
        Permanently delete the item and log the deletion event.
        """
        user = self.request.user
        action.send(
            user,
            verb='deleted item',
            target=instance,
            description=f"Item: '{instance.name}' (Code: {instance.item_code})"
        )
        instance.delete()

    @swagger_auto_schema(
        tags=['Inventory Items'],
        operation_description="Retrieve an item by ID.",
        responses={
            200: ItemReadSerializer(),
            404: "Item not found."
        },
        manual_parameters=[
            openapi.Parameter(
                'pk', openapi.IN_PATH,
                description="Primary key of the item",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Inventory Items'],
        operation_description="Update an item by ID.",
        request_body=ItemWriteSerializer,
        responses={
            200: openapi.Response(
                description="Item updated successfully.",
                schema=ItemReadSerializer()
            ),
            400: "Invalid data provided.",
            404: "Item not found."
        }
    )
    def put(self, request, *args, **kwargs):
        """
        Update item details and log an 'updated item' event.
        """
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Inventory Items'],
        operation_description="Partially update an item by ID.",
        request_body=ItemWriteSerializer(partial=True),
        responses={
            200: openapi.Response(
                description="Item updated successfully.",
                schema=ItemReadSerializer()
            ),
            400: "Invalid data provided.",
            404: "Item not found."
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Inventory Items'],
        operation_description="Delete an item by ID.",
        responses={204: "Item deleted successfully.", 404: "Item not found."},
        manual_parameters=[
            openapi.Parameter(
                'pk', openapi.IN_PATH,
                description="Primary key of the item",
                type=openapi.TYPE_INTEGER, required=True
            )
        ]
    )
    def delete(self, request, *args, **kwargs):
        """Permanently delete the item."""
        return super().delete(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        Override update to log an 'updated item' event if successful.
        """
        response = super().update(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            instance = self.get_object()
            action.send(
                request.user,
                verb='updated item',
                target=instance,
                description=f"Item: '{instance.name}' (Code: {instance.item_code})"
            )
        return response
