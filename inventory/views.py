from rest_framework.views import APIView
from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework import status
from .models import Category, Supplier, Item
from .serializers import CategorySerializer, SupplierSerializer, ItemSerializer
from django.http import Http404
from django.shortcuts import get_object_or_404
from .utils import get_object_by_id_or_slug
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


# --------- CATEGORY VIEWS --------- #
class CategoryList(APIView):
    """
    List all categories or create a new category.
    Only non-deleted categories are listed.
    """

    @swagger_auto_schema(
        operation_description="Retrieve a list of all non-deleted categories.",
        responses={
            200: openapi.Response(
                description="A list of categories retrieved successfully.",
                schema=CategorySerializer(many=True)
            )
        }
    )
    def get(self, request, format=None):
        categories = Category.objects.filter(is_deleted=False)
        serializer = CategorySerializer(categories, many=True, context={'request': request})
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Create a new category.",
        request_body=CategorySerializer(),
        responses={
            201: openapi.Response(
                description="Category created successfully.",
                schema=CategorySerializer()
            ),
            400: "Invalid input, object invalid."
        }
    )
    def post(self, request, format=None):
        serializer = CategorySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryDetail(APIView):
    """
    Retrieve, update, or delete a category instance. Supports both slug and ID for identification.
    """

    def get_object(self, identifier):
        """
        Fetch category using either ID or slug.
        """
        return get_object_by_id_or_slug(Category, identifier, id_field='id', slug_field='slug')

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
    def get(self, request, identifier, format=None):
        category = self.get_object(identifier)
        serializer = CategorySerializer(category, context={'request': request})
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Update a category by ID or slug.",
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
    def put(self, request, identifier, format=None):
        category = self.get_object(identifier)
        serializer = CategorySerializer(category, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Soft delete a category by ID or slug.",
        responses={204: "Category soft-deleted successfully.", 404: "Category not found."}
    )
    def delete(self, request, identifier, format=None):
        category = self.get_object(identifier)
        category.delete()  # Soft delete
        return Response(status=status.HTTP_204_NO_CONTENT)


# --------- ITEM VIEWS --------- #
class ItemList(generics.ListCreateAPIView):
    """
    List all items or create a new item.
    Supports filtering, search, and sorting. Only non-deleted items are listed.
    """
    serializer_class = ItemSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['descriptive_name', 'part_number']  # Fields to search by
    filterset_fields = ['location', 'supplier', 'category']  # Fields to filter by
    ordering_fields = ['current_stock', 'descriptive_name', 'created_at']  # Fields to order by
    ordering = ['descriptive_name']  # Default ordering

    def get_queryset(self):
        queryset = Item.objects.filter(is_deleted=False)
        stock_status = self.request.query_params.get('stock_status')
        if stock_status:
            return queryset.filter(stock_status=stock_status)
        return queryset

    @swagger_auto_schema(
        operation_description="List all non-deleted items with options for filtering, search, and sorting.",
        manual_parameters=[
            openapi.Parameter('stock_status', in_=openapi.IN_QUERY, description="Filter items by stock status.", type=openapi.TYPE_STRING)
        ],
        responses={200: openapi.Response(description="List of items", schema=ItemSerializer(many=True))}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new item.",
        request_body=ItemSerializer(),
        responses={
            201: openapi.Response(description="Item created successfully.", schema=ItemSerializer()),
            400: "Invalid data provided."
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ItemDetail(APIView):
    """
    Retrieve, update, or delete an item instance. Soft-deleted items are not retrievable.
    """

    def get_object(self, pk):
        try:
            return Item.objects.get(pk=pk, is_deleted=False)
        except Item.DoesNotExist:
            raise Http404

    @swagger_auto_schema(
        operation_description="Retrieve a specific item by its ID.",
        responses={
            200: openapi.Response(description="Item retrieved successfully.", schema=ItemSerializer()),
            404: "Item not found."
        }
    )
    def get(self, request, pk, format=None):
        item = self.get_object(pk)
        serializer = ItemSerializer(item, context={'request': request})
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Update an item by its ID.",
        request_body=ItemSerializer(),
        responses={
            200: openapi.Response(description="Item updated successfully.", schema=ItemSerializer()),
            400: "Invalid data provided.",
            404: "Item not found."
        }
    )
    def put(self, request, pk, format=None):
        item = self.get_object(pk)
        serializer = ItemSerializer(item, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Delete an item by its ID, triggering a soft-delete mechanism.",
        responses={204: "Item deleted successfully.", 404: "Item not found."}
    )
    def delete(self, request, pk, format=None):
        item = self.get_object(pk)
        item.delete()  # This triggers the soft-delete mechanism
        return Response(status=status.HTTP_204_NO_CONTENT)


# --------- CATEGORY ITEM VIEWS --------- #
class CategoryItemsList(generics.ListAPIView):
    """
    List all items within a category. Supports both slug and ID to identify the category.
    """
    serializer_class = ItemSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['descriptive_name', 'item_id', 'part_number']  # Fields to search by
    filterset_fields = ['location', 'supplier', 'category']  # Fields to filter by
    ordering_fields = ['current_stock', 'descriptive_name', 'created_at']  # Fields to order by
    ordering = ['created_at']  # Default ordering

    def get_queryset(self):
        identifier = self.kwargs['identifier']
        category = get_object_by_id_or_slug(Category, identifier, id_field='id', slug_field='slug')
        return Item.objects.filter(category=category, is_deleted=False)

    @swagger_auto_schema(
        operation_description="List all items within a specific category identified by slug or ID.",
        manual_parameters=[
            openapi.Parameter('identifier', openapi.IN_PATH, description="ID or slug of the category", type=openapi.TYPE_STRING, required=True)
        ],
        responses={200: openapi.Response(description="A list of items within the category.", schema=ItemSerializer(many=True))}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# --------- SUPPLIER VIEWS --------- #
class SupplierList(APIView):
    """
    List all suppliers or create a new supplier.
    Only non-deleted suppliers are listed.
    """

    def get(self, request, format=None):
        suppliers = Supplier.objects.filter(is_deleted=False)
        serializer = SupplierSerializer(suppliers, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = SupplierSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SupplierDetail(APIView):
    """
    Retrieve, update, or delete a supplier instance. Soft deleted suppliers are not retrievable.
    """

    def get_object(self, pk):
        try:
            return Supplier.objects.get(pk=pk, is_deleted=False)
        except Supplier.DoesNotExist:
            raise Http404

    @swagger_auto_schema(
        operation_description="Retrieve a supplier along with all items supplied by them.",
        responses={
            200: openapi.Response(description="Supplier details retrieved successfully.", schema=SupplierSerializer()),
            404: "Supplier not found."
        }
    )
    def get(self, request, pk, format=None):
        supplier = self.get_object(pk)
        serializer = SupplierSerializer(supplier, context={'request': request})
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Update a supplier's details.",
        request_body=SupplierSerializer(),
        responses={
            200: openapi.Response(description="Supplier updated successfully.", schema=SupplierSerializer()),
            400: "Invalid data provided.",
            404: "Supplier not found."
        }
    )
    def put(self, request, pk, format=None):
        supplier = self.get_object(pk)
        serializer = SupplierSerializer(supplier, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Soft delete a supplier instance.",
        responses={204: "Supplier soft-deleted successfully.", 404: "Supplier not found."}
    )
    def delete(self, request, pk, format=None):
        supplier = self.get_object(pk)
        supplier.delete()  # This triggers the soft delete mechanism
        return Response(status=status.HTTP_204_NO_CONTENT)
