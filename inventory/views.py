from rest_framework import generics, filters, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from auditlog.models import LogEntry
from .models import Category, Item
from django.shortcuts import get_object_or_404
from .serializers import CategorySerializer, ItemSerializer, InventoryLogEntrySerializer
from .utils import get_object_by_id_or_slug
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# --------- CATEGORY VIEWS --------- #
class CategoryListCreateView(generics.ListCreateAPIView):
    """
    Retrieve a list of categories or create a new category.
    Only non-deleted categories are listed.
    """
    queryset = Category.objects.filter(is_removed=False)
    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created', 'modified']
    ordering = ['name']

    @swagger_auto_schema(
        operation_description="Retrieve a list of all non-deleted categories.",
        responses={
            200: openapi.Response(
                description="A list of categories retrieved successfully.",
                schema=CategorySerializer(many=True)
            )
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new category. Set `is_draft` to True to save as a draft.",
        request_body=CategorySerializer(),
        responses={
            201: openapi.Response(
                description="Category created successfully.",
                schema=CategorySerializer()
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
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        identifier = self.kwargs.get("identifier")
        category = get_object_by_id_or_slug(Category, identifier, id_field="id", slug_field="slug")
        if category.is_removed:
            raise NotFound("This category has been deleted.")
        return category

    @swagger_auto_schema(
        operation_description="Retrieve a category by ID or slug.",
        responses={
            200: openapi.Response(
                description="Category retrieved successfully.",
                schema=CategorySerializer()
            ),
            404: "Category not found."
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update a category by ID or slug. Set `is_draft` to True to save as a draft.",
        request_body=CategorySerializer(),
        responses={
            200: openapi.Response(
                description="Category updated successfully.",
                schema=CategorySerializer()
            ),
            400: "Invalid data provided.",
            404: "Category not found."
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Soft delete a category by ID or slug.",
        responses={204: "Category soft-deleted successfully.", 404: "Category not found."}
    )
    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        category.delete()  # Soft-delete
        return Response(status=status.HTTP_204_NO_CONTENT)


# --------- ITEM VIEWS --------- #
class ItemListCreateView(generics.ListCreateAPIView):
    """
    Retrieve a list of items or create a new item.
    Supports filtering, search, and sorting.
    """
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['descriptive_name', 'serial_number']
    filterset_fields = ['location', 'category']
    ordering_fields = ['current_stock', 'descriptive_name', 'created']
    ordering = ['descriptive_name']

    def get_queryset(self):
        queryset = Item.objects.filter(is_removed=False)
        stock_status = self.request.query_params.get('stock_status')
        if stock_status:
            queryset = queryset.filter(stock_status=stock_status)
        return queryset

    @swagger_auto_schema(
        operation_description="Retrieve a list of all non-deleted items with filtering and sorting options.",
        manual_parameters=[
            openapi.Parameter(
                'stock_status', in_=openapi.IN_QUERY, description="Filter items by stock status.", type=openapi.TYPE_STRING
            )
        ],
        responses={200: openapi.Response(description="A list of items.", schema=ItemSerializer(many=True))}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new item. Set `is_draft` to True to save as a draft.",
        request_body=ItemSerializer(),
        responses={201: openapi.Response(description="Item created successfully.", schema=ItemSerializer())}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete an item instance.
    Soft-deleted items are not retrievable.
    """
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated]
    queryset = Item.objects.filter(is_removed=False)  # Defined queryset

    @swagger_auto_schema(
        operation_description="Retrieve a specific item by its ID.",
        responses={
            200: openapi.Response(description="Item retrieved successfully.", schema=ItemSerializer()),
            404: "Item not found."
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update an item by its ID. Set `is_draft` to True to save as a draft.",
        request_body=ItemSerializer(),
        responses={
            200: openapi.Response(description="Item updated successfully.", schema=ItemSerializer()),
            400: "Invalid data provided.",
            404: "Item not found."
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete an item by its ID, triggering a soft-delete mechanism.",
        responses={204: "Item deleted successfully.", 404: "Item not found."}
    )
    def delete(self, request, *args, **kwargs):
        item = self.get_object()
        item.delete()  # Soft-delete
        return Response(status=status.HTTP_204_NO_CONTENT)


# --------- CATEGORY ITEM LIST VIEW --------- #
class CategoryItemsListView(generics.ListAPIView):
    """
    Retrieve all items within a category, identified by slug or ID.
    """
    serializer_class = ItemSerializer
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
        operation_description="List all items within a specific category by slug or ID.",
        manual_parameters=[
            openapi.Parameter('identifier', openapi.IN_PATH, description="ID or slug of the category", type=openapi.TYPE_STRING, required=True)
        ],
        responses={200: openapi.Response(description="A list of items within the category.", schema=ItemSerializer(many=True))}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


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
