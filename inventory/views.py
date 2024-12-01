from rest_framework import generics, filters, status, permissions
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsAdminOrSuperAdmin
from auditlog.models import LogEntry
from .models import Category, Item
from .serializers import (
    CategoryReadSerializer, CategoryWriteSerializer,
    ItemReadSerializer, ItemWriteSerializer,
    InventoryLogEntrySerializer
)
from .utils import get_object_by_id_or_slug
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi




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
        responses={
            200: CategoryReadSerializer(many=True),
        },
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
        return super().post(request, *args, **kwargs)


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a category instance.
    Supports both slug and ID for identification.
    """
    permission_classes = [IsAuthenticated]
    lookup_field = 'identifier'

    def get_object(self):
        identifier = self.kwargs.get("identifier")
        category = get_object_by_id_or_slug(Category, identifier, id_field="id", slug_field="slug", all_objects=True)
        return category

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CategoryWriteSerializer
        else:
            return CategoryReadSerializer

    def perform_destroy(self, instance):
        if instance.is_removed:
            # If user is Admin or SuperAdmin, permanently delete
            if IsAdminOrSuperAdmin().has_permission(self.request, self):
                instance.delete()
            else:
                raise PermissionDenied("You do not have permission to permanently delete this category.")
        else:
            # Set is_removed to True (soft delete)
            instance.is_removed = True
            instance.save()

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
        return super().put(request, *args, **kwargs)

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
        return super().delete(request, *args, **kwargs)

# --------- ITEM VIEWS --------- #

class ItemListCreateView(generics.ListCreateAPIView):
    """
    Retrieve a list of items or create a new item.
    Supports filtering, search, and sorting.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['descriptive_name', 'serial_number']
    filterset_fields = ['location', 'category', 'status', 'is_removed']
    ordering_fields = ['descriptive_name', 'id', 'created']
    ordering = ['id']

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
        responses={
            200: ItemReadSerializer(many=True),
        },
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
        return super().post(request, *args, **kwargs)


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
        else:
            return ItemReadSerializer

    def perform_destroy(self, instance):
        if instance.is_removed:
            # If user is Admin or SuperAdmin, permanently delete
            if IsAdminOrSuperAdmin().has_permission(self.request, self):
                instance.delete()
            else:
                raise PermissionDenied("You do not have permission to permanently delete this item.")
        else:
            # Set is_removed to True (soft delete)
            instance.is_removed = True
            instance.save()

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
                type=openapi.TYPE_INTEGER, required=True
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
        return super().put(request, *args, **kwargs)

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
        return super().delete(request, *args, **kwargs)
    
    
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
            openapi.Parameter('identifier', openapi.IN_PATH, description="ID or slug of the category", type=openapi.TYPE_STRING, required=True)
        ],
        responses={200: openapi.Response(description="A list of items within the category.", schema=ItemReadSerializer(many=True))}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# --------- AUDIT LOG VIEW --------- #

class AuditLogView(generics.ListAPIView):
    """
    API endpoint that returns a list of all audit logs for Items and Categories from Django-Auditlog.
    """
    serializer_class = InventoryLogEntrySerializer
    permission_classes = [IsAuthenticated]
    queryset = LogEntry.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['object_repr', 'changes']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    @swagger_auto_schema(
        tags=['Audit Logs'],
        operation_summary="Retrieve all audit log entries for Items and Categories",
        operation_description="Returns a list of audit log entries recorded by Django-Auditlog for Item and Category models, ordered by most recent.",
        responses={
            200: openapi.Response(description="A list of audit log entries.", schema=InventoryLogEntrySerializer(many=True)),
            403: "Forbidden - User is not authorized to access this endpoint."
        },
        manual_parameters=[
            openapi.Parameter(
                'item_id',
                openapi.IN_QUERY,
                description="Filter logs by Item ID",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'item_name',
                openapi.IN_QUERY,
                description="Filter logs by Item name",
                type=openapi.TYPE_STRING,
                required=False
            )
        ]
    )
    def get(self, request, format=None):
        item_id = request.query_params.get('item_id')
        item_name = request.query_params.get('item_name')

        queryset = LogEntry.objects.all().order_by('-timestamp')

        # Apply filters for Item and Category if provided
        if item_id:
            queryset = queryset.filter(object_pk=item_id, content_type__model='item')
        elif item_name:
            queryset = queryset.filter(object_repr__icontains=item_name, content_type__model='item')

        serializer = InventoryLogEntrySerializer(queryset, many=True)
        return Response(serializer.data)
