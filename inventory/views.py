# inventory/views.py

import logging
from django.db.models import F, Value, CharField, Case, When, Sum
from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend, CharFilter, FilterSet
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, OpenApiParameter



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
        method = getattr(self.request, 'method', None)
        if method == 'POST':
            return ItemWriteSerializer
        return ItemReadSerializer

    @extend_schema(
        summary="List Inventory Items",
        description="Retrieve a list of items.",
        responses={
            200: OpenApiResponse(
                description="List of items retrieved successfully.",
                response=ItemReadSerializer(many=True)
            )
        },
        tags=["Inventory"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Create Inventory Item",
        description="Create a new item.",
        request=ItemWriteSerializer,
        responses={
            201: OpenApiResponse(
                description="Item created successfully.",
                response=ItemReadSerializer
            ),
            400: OpenApiResponse(
                description="Invalid input, object invalid."
            )
        },
        tags=["Inventory"]
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            item_id = response.data.get('id')
            try:
                item_instance = Item.objects.get(id=item_id)
                logger.info(
                    f"User {request.user.email} created inventory item: '{item_instance.name}' "
                    f"(Code: {item_instance.item_code})"
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
        method = getattr(self.request, 'method', None)
        if method in ['PUT', 'PATCH']:
            return ItemWriteSerializer
        return ItemReadSerializer

    def perform_destroy(self, instance):
        user = self.request.user
        logger.info(
            f"User {user.email} deleted item: '{instance.name}' (Code: {instance.item_code})"
        )
        instance.delete()

    @extend_schema(
        summary="Retrieve Inventory Item",
        description="Retrieve an item by its primary key.",
        parameters=[
            OpenApiParameter(
                name="pk",
                location=OpenApiParameter.PATH,
                description="Primary key of the item",
                type=int,
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Item retrieved successfully.",
                response=ItemReadSerializer
            ),
            404: OpenApiResponse(
                description="Item not found."
            )
        },
        tags=["Inventory"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update Inventory Item",
        description="Update an item by its primary key. Partial updates are allowed.",
        request=ItemWriteSerializer,
        responses={
            200: OpenApiResponse(
                description="Item updated successfully.",
                response=ItemReadSerializer
            ),
            400: OpenApiResponse(
                description="Invalid data provided."
            ),
            404: OpenApiResponse(
                description="Item not found."
            )
        },
        tags=["Inventory"]
    )
    def put(self, request, *args, **kwargs):
        kwargs['partial'] = True  # Allow partial updates
        return self.update(request, *args, **kwargs)

    @extend_schema(
        summary="Partially Update Inventory Item",
        description="Partially update an item by its primary key.",
        request=ItemWriteSerializer,
        responses={
            200: OpenApiResponse(
                description="Item updated successfully.",
                response=ItemReadSerializer
            ),
            400: OpenApiResponse(
                description="Invalid data provided."
            ),
            404: OpenApiResponse(
                description="Item not found."
            )
        },
        tags=["Inventory"]
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        summary="Delete Inventory Item",
        description="Delete an item by its primary key.",
        parameters=[
            OpenApiParameter(
                name="pk",
                location=OpenApiParameter.PATH,
                description="Primary key of the item",
                type=int,
                required=True
            )
        ],
        responses={
            204: OpenApiResponse(
                description="Item deleted successfully."
            ),
            404: OpenApiResponse(
                description="Item not found."
            )
        },
        tags=["Inventory"]
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            instance = self.get_object()
            logger.info(
                f"User {request.user.email} updated item: '{instance.name}' (Code: {instance.item_code})"
            )
        return response



class TotalInventoryView(APIView):
    """
    Retrieve total inventory information.
    
    Returns:
      - total_items: The number of inventory records.
      - total_stock: The sum of the 'quantity' field across all items.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get Total Inventory Information",
        description="Get total inventory count and total stock quantity.",
        responses={
            200: OpenApiResponse(
                description="Total inventory retrieved successfully.",
                response={
                    "type": "object",
                    "properties": {
                        "total_items": {
                            "type": "integer",
                            "description": "Total number of inventory items."
                        },
                        "total_stock": {
                            "type": "integer",
                            "description": "Total sum of item quantities."
                        }
                    }
                },
                examples=[
                    OpenApiExample(
                        "Total Inventory Example",
                        value={"total_items": 15, "total_stock": 320},
                        response_only=True
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Unauthorized access.",
                examples=[
                    OpenApiExample(
                        "Unauthorized",
                        value={"detail": "Authentication credentials were not provided."},
                        response_only=True
                    )
                ]
            )
        },
        tags=["Inventory"]
    )
    def get(self, request, format=None):
        total_items = Item.objects.count()
        total_stock = Item.objects.aggregate(total=Sum('quantity'))['total'] or 0

        return Response({
            "total_items": total_items,
            "total_stock": total_stock
        })