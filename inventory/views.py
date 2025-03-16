# inventory/views.py

import logging
from django.db.models import F, Value, CharField, Case, When, Sum
from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend, CharFilter, FilterSet
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi



# Local imports
from accounts.permissions import IsAdminOrSuperAdmin
from .models import Item
from .serializers import (
    ItemReadSerializer, ItemWriteSerializer,
)

# Configure logger
logger = logging.getLogger(__name__)






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
                logger.info(f"User {request.user.email} created inventory item: '{item_instance.name}' (Code: {item_instance.item_code})")

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
        logger.info(f"User {user.email} deleted item: '{instance.name}' (Code: {instance.item_code})")
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
            logger.info(f"User {request.user.email} updated item: '{instance.name}' (Code: {instance.item_code})")
                        
        return response



class TotalInventoryView(APIView):
    """
    Retrieve total inventory information.
    
    Returns:
      - total_items: The number of inventory records.
      - total_stock: The sum of the 'quantity' field across all items.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Inventory'],
        operation_description="Get total inventory count and total stock quantity.",
        responses={
            200: openapi.Response(
                description="Total inventory retrieved successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "total_items": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="Total number of inventory items."
                        ),
                        "total_stock": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="Total sum of item quantities."
                        )
                    }
                ),
                examples={
                    "application/json": {
                        "total_items": 15,
                        "total_stock": 320
                    }
                }
            ),
            401: openapi.Response(
                description="Unauthorized access.",
                examples={"application/json": {"detail": "Authentication credentials were not provided."}}
            )
        }
    )
    def get(self, request, format=None):
        total_items = Item.objects.count()
        # Sum up the quantity field. If no items exist, default to 0.
        total_stock = Item.objects.aggregate(total=Sum('quantity'))['total'] or 0

        return Response({
            "total_items": total_items,
            "total_stock": total_stock
        })
