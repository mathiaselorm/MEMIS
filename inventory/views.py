# inventory/views.py

from django.db.models import F, Value, CharField, Case, When
from rest_framework import generics, filters, status, permissions
from django_filters.rest_framework import DjangoFilterBackend, CharFilter, FilterSet
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Import django-activity-stream
from actstream import action

# Local imports
from accounts.permissions import IsAdminOrSuperAdmin
from .models import Category, Item
from .serializers import (
    CategoryReadSerializer, CategoryWriteSerializer,
    ItemReadSerializer, ItemWriteSerializer,
)
from .utils import get_object_by_id_or_slug


# --------- CATEGORY VIEWS --------- #

class CategoryListCreateView(generics.ListCreateAPIView):
    """
    Retrieve a list of categories or create a new category.
    Returns all categories, including soft-deleted and with any status.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created', 'modified']
    ordering = ['name']

    def get_queryset(self):
        queryset = Category.all_objects.all()
        status_param = self.request.query_params.get('status')
        is_removed_param = self.request.query_params.get('is_removed')
        if status_param:
            queryset = queryset.filter(status=status_param)
        if is_removed_param is not None:
            is_removed = is_removed_param.lower() == 'true'
            queryset = queryset.filter(is_removed=is_removed)
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CategoryWriteSerializer
        return CategoryReadSerializer

    @swagger_auto_schema(
        tags=['Categories'],
        operation_description="Retrieve a list of categories.",
        responses={200: CategoryReadSerializer(many=True)},
        manual_parameters=[
            openapi.Parameter(
                'status', openapi.IN_QUERY,
                description="Filter categories by status ('draft' or 'published')",
                type=openapi.TYPE_STRING,
                required=False,
                enum=['draft', 'published']
            ),
            openapi.Parameter(
                'is_removed', openapi.IN_QUERY,
                description="Filter categories by soft delete status ('true' or 'false')",
                type=openapi.TYPE_STRING,
                required=False,
                enum=['true', 'false']
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Categories'],
        operation_description="Create a new category.",
        request_body=CategoryWriteSerializer,
        responses={
            201: openapi.Response(
                description="Category created successfully.",
                schema=CategoryReadSerializer()
            ),
            400: "Invalid input, object invalid."
        }
    )
    def post(self, request, *args, **kwargs):
        """Create a new category, then log the event via django-activity-stream."""
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            # The serializer returns the created category data
            category_id = response.data.get('id')
            # Retrieve the saved category instance (re-fetch from DB)
            try:
                category_instance = Category.all_objects.get(id=category_id)
                # Record creation in the activity stream
                action.send(
                    request.user,
                    verb='created category',
                    target=category_instance,
                    description=f"Category named '{category_instance.name}'"
                )
            except Category.DoesNotExist:
                pass
        return response


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a category instance.
    Supports both slug and ID for identification.
    """
    permission_classes = [IsAuthenticated]
    lookup_field = 'identifier'

    def get_object(self):
        identifier = self.kwargs.get("identifier")
        category = get_object_by_id_or_slug(
            Category, identifier,
            id_field="id", slug_field="slug",
            all_objects=True
        )
        return category

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CategoryWriteSerializer
        else:
            return CategoryReadSerializer

    def perform_destroy(self, instance):
        user = self.request.user
        if instance.is_removed:
            # If user is Admin or SuperAdmin, permanently delete
            if IsAdminOrSuperAdmin().has_permission(self.request, self):
                # Log permanent deletion
                action.send(
                    user,
                    verb='permanently deleted category',
                    target=instance,
                    description=f"Category: '{instance.name}'"
                )
                instance.delete()
            else:
                raise PermissionDenied("You do not have permission to permanently delete this category.")
        else:
            # Soft delete
            instance.is_removed = True
            instance.save()
            action.send(
                user,
                verb='soft-deleted category',
                target=instance,
                description=f"Category: '{instance.name}'"
            )

    @swagger_auto_schema(
        tags=['Categories'],
        operation_description="Retrieve a category by ID or slug.",
        responses={
            200: CategoryReadSerializer(),
            404: "Category not found."
        },
        manual_parameters=[
            openapi.Parameter(
                'identifier', openapi.IN_PATH,
                description="ID or Slug of the category",
                type=openapi.TYPE_STRING, required=True
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        """Retrieve category."""
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Categories'],
        operation_description="Update a category by ID or slug.",
        request_body=CategoryWriteSerializer,
        responses={
            200: openapi.Response(
                description="Category updated successfully.",
                schema=CategoryReadSerializer()
            ),
            400: "Invalid data provided.",
            404: "Category not found."
        }
    )
    def put(self, request, *args, **kwargs):
        """Fully update category (partial updates also allowed)."""
        # We'll log the "updated" activity in post-update
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Categories'],
        operation_description="Partially update a category by ID or slug.",
        request_body=CategoryWriteSerializer(partial=True),
        responses={
            200: openapi.Response(
                description="Category updated successfully.",
                schema=CategoryReadSerializer()
            ),
            400: "Invalid data provided.",
            404: "Category not found."
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Categories'],
        operation_description="Delete a category by ID or slug.",
        responses={204: "Category deleted successfully.", 404: "Category not found."}
    )
    def delete(self, request, *args, **kwargs):
        """Soft-delete or permanent-delete a category."""
        return super().delete(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Override update to log a 'updated category' event."""
        response = super().update(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            instance = self.get_object()
            action.send(
                request.user,
                verb='updated category',
                target=instance,
                description=f"Category: '{instance.name}'"
            )
        return response


# --------- ITEM FILTER / VIEWS --------- #

class ItemFilterSet(FilterSet):
    stock_status = CharFilter(method='filter_by_stock_status')

    class Meta:
        model = Item
        fields = ['location', 'category', 'status', 'is_removed', 'stock_status']

    def filter_by_stock_status(self, queryset, name, value):
        value = value.lower()
        if value not in ['in stock', 'out of stock', 'archived']:
            return queryset.none()
        # Annotate the queryset with stock_status
        queryset = queryset.annotate(
            stock_status=Case(
                When(is_removed=True, then=Value('Archived')),
                When(current_stock=0, then=Value('Out of Stock')),
                default=Value('In Stock'),
                output_field=CharField(),
            )
        )
        return queryset.filter(stock_status__iexact=value)


class ItemListCreateView(generics.ListCreateAPIView):
    """
    Retrieve a list of items or create a new item.
    Supports filtering, search, and sorting.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ItemFilterSet
    search_fields = ['descriptive_name', 'serial_number']
    ordering_fields = ['current_stock', 'descriptive_name', 'created']
    ordering = ['descriptive_name']

    def get_queryset(self):
        queryset = Item.all_objects.all()
        status_param = self.request.query_params.get('status')
        is_removed_param = self.request.query_params.get('is_removed')
        if status_param:
            queryset = queryset.filter(status=status_param)
        if is_removed_param is not None:
            is_removed = is_removed_param.lower() == 'true'
            queryset = queryset.filter(is_removed=is_removed)
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ItemWriteSerializer
        return ItemReadSerializer

    @swagger_auto_schema(
        tags=['Inventory Items'],
        operation_description="Retrieve a list of items.",
        responses={200: ItemReadSerializer(many=True)},
        manual_parameters=[
            openapi.Parameter(
                'status', openapi.IN_QUERY,
                description="Filter items by status ('draft' or 'published')",
                type=openapi.TYPE_STRING,
                required=False,
                enum=['draft', 'published']
            ),
            openapi.Parameter(
                'is_removed', openapi.IN_QUERY,
                description="Filter items by soft delete status ('true' or 'false')",
                type=openapi.TYPE_STRING,
                required=False,
                enum=['true', 'false']
            ),
            openapi.Parameter(
                'location', openapi.IN_QUERY,
                description="Filter items by location",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'category', openapi.IN_QUERY,
                description="Filter items by category ID",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'stock_status', openapi.IN_QUERY,
                description="Filter items by stock status ('In Stock', 'Out of Stock', 'Archived')",
                type=openapi.TYPE_STRING,
                required=False,
                enum=['In Stock', 'Out of Stock', 'Archived']
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
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
        Create a new item and log the creation in activity stream.
        """
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            item_id = response.data.get('id')
            try:
                item_instance = Item.all_objects.get(id=item_id)
                action.send(
                    request.user,
                    verb='created item',
                    target=item_instance,
                    description=f"Item: '{item_instance.descriptive_name}' (Serial: {item_instance.serial_number})"
                )
            except Item.DoesNotExist:
                pass
        return response


class ItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete an item instance.
    """
    permission_classes = [IsAuthenticated]
    queryset = Item.all_objects.all()
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ItemWriteSerializer
        return ItemReadSerializer

    def perform_destroy(self, instance):
        user = self.request.user
        if instance.is_removed:
            # Permanently delete if user is admin
            if IsAdminOrSuperAdmin().has_permission(self.request, self):
                action.send(
                    user,
                    verb='permanently deleted item',
                    target=instance,
                    description=f"Item: '{instance.descriptive_name}'"
                )
                instance.delete()
            else:
                raise PermissionDenied("You do not have permission to permanently delete this item.")
        else:
            # Soft delete
            instance.is_removed = True
            instance.save()
            action.send(
                user,
                verb='soft-deleted item',
                target=instance,
                description=f"Item: '{instance.descriptive_name}'"
            )

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
        Update item details and log 'updated item'.
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
        """Soft-delete or permanently delete the item."""
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
                description=f"Item: '{instance.descriptive_name}'"
            )
        return response


# --------- CATEGORY ITEM LIST VIEW --------- #
class CategoryItemsListView(generics.ListAPIView):
    """
    Retrieve all items within a category, identified by slug or ID.
    """
    serializer_class = ItemReadSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['descriptive_name', 'serial_number']
    filterset_fields = ['location', 'status']
    ordering_fields = ['current_stock', 'descriptive_name', 'created']
    ordering = ['created']

    def get_queryset(self):
        identifier = self.kwargs.get('identifier')
        category = get_object_by_id_or_slug(Category, identifier, id_field='id', slug_field='slug')
        return Item.objects.filter(category=category, is_removed=False)

    @swagger_auto_schema(
        tags=['Inventory Items'],
        operation_description="List all items within a specific category by slug or ID.",
        manual_parameters=[
            openapi.Parameter(
                'identifier',
                openapi.IN_PATH,
                description="ID or slug of the category",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={200: openapi.Response(description="A list of items within the category.", schema=ItemReadSerializer(many=True))}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
