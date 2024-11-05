from django.http import Http404
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from django.shortcuts import get_object_or_404

from .models import Asset, Department
from auditlog.models import LogEntry
from .serializers import DepartmentSerializer, AssetSerializer, LogEntrySerializer
from .utils import get_object_by_id_or_slug
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from accounts.permissions import IsAdminOrSuperAdmin

# Removed imports related to ActionLog and AssetStatus since they no longer exist in models.py

class DepartmentList(generics.ListCreateAPIView):
    """
    List all departments or create a new department.
    """
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    queryset = Department.objects.all()

    def get_permissions(self):
        """
        Allow authenticated users to view the list; only staff can create.
        """
        if self.request.method == "POST":
            self.permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]
        return super().get_permissions()

    @swagger_auto_schema(
        operation_description="Retrieve a list of all departments. Only authenticated users can view the list.",
        responses={
            200: DepartmentSerializer(many=True),
            401: "Unauthorized access."
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new department. Only staff users have permission to create.",
        request_body=DepartmentSerializer,
        responses={
            201: DepartmentSerializer,
            400: "Bad request - Invalid data submitted.",
            403: "Permission denied - Only staff users can create departments.",
            401: "Unauthorized - User is not authenticated."
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class DepartmentDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a department using either an ID or a slug.
    """
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    queryset = Department.objects.all()
    lookup_field = 'identifier'

    def get_object(self):
        """
        Override to get the department by ID or slug.
        """
        identifier = self.kwargs['identifier']
        return get_object_by_id_or_slug(Department, identifier, id_field='id', slug_field='slug')

    @swagger_auto_schema(
        operation_description="Retrieve a department by its ID or slug.",
        responses={
            200: DepartmentSerializer,
            404: "Department not found."
        },
        manual_parameters=[
            openapi.Parameter(
                'identifier', openapi.IN_PATH,
                description="ID or Slug of the department",
                type=openapi.TYPE_STRING, required=True
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update a department by its ID or slug. Supports partial updates.",
        request_body=DepartmentSerializer(partial=True),
        responses={
            200: DepartmentSerializer,
            400: "Invalid data provided.",
            404: "Department not found."
        },
        manual_parameters=[
            openapi.Parameter(
                'identifier', openapi.IN_PATH,
                description="ID or Slug of the department",
                type=openapi.TYPE_STRING, required=True
            )
        ]
    )
    def put(self, request, *args, **kwargs):
        """
        Allows partial updates on the department object.
        """
        partial = True  # Enable partial updates
        return self.update(request, *args, **kwargs, partial=partial)

    @swagger_auto_schema(
        operation_description="Delete a department by its ID or slug.",
        responses={
            204: "Department successfully deleted.",
            404: "Department not found."
        },
        manual_parameters=[
            openapi.Parameter(
                'identifier', openapi.IN_PATH,
                description="ID or Slug of the department",
                type=openapi.TYPE_STRING, required=True
            )
        ]
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class TotalDepartmentsView(APIView):
    """
    View to return the total number of departments in the system.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve the total number of departments in the system.",
        responses={
            200: openapi.Response(
                description="Total count of departments.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total_departments': openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="Total number of departments"
                        )
                    }
                )
            ),
            401: "Unauthorized - user must be authenticated.",
            500: "Server error."
        }
    )
    def get(self, request, *args, **kwargs):
        total_departments = Department.objects.count()
        return Response({'total_departments': total_departments})


class AssetList(generics.ListCreateAPIView):
    """
    List all assets or create a new asset.
    """
    serializer_class = AssetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Override the queryset to only retrieve non-deleted assets.
        """
        return Asset.objects.filter(is_removed=False)

    @swagger_auto_schema(
        operation_description="Retrieve a list of all assets.",
        responses={200: AssetSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new asset.",
        request_body=AssetSerializer,
        responses={
            201: AssetSerializer,
            400: "Bad request - Invalid data submitted.",
            401: "Unauthorized - User is not authenticated."
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class AssetDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete an asset.
    """
    serializer_class = AssetSerializer
    permission_classes = [IsAuthenticated]
    queryset = Asset.objects.filter(is_removed=False)

    @swagger_auto_schema(
        operation_description="Retrieve an asset by its primary key.",
        responses={
            200: AssetSerializer,
            404: "Asset not found."
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update an asset by its primary key.",
        request_body=AssetSerializer,
        responses={
            200: AssetSerializer,
            400: "Invalid data provided.",
            404: "Asset not found."
        }
    )
    def put(self, request, *args, **kwargs):
        """
        Allows partial updates on the asset object.
        """
        partial = True  # Enable partial updates
        return self.update(request, *args, **kwargs, partial=partial)

    @swagger_auto_schema(
        operation_description="Partially update an asset by its primary key.",
        request_body=AssetSerializer(partial=True),
        responses={
            200: AssetSerializer,
            400: "Invalid data provided.",
            404: "Asset not found."
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete an asset by its primary key.",
        responses={
            204: "Asset deleted successfully.",
            404: "Asset not found."
        }
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class TrackingByDepartmentView(APIView):
    """
    View to return all assets under a specific department.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve all assets belonging to a specific department.",
        responses={
            200: AssetSerializer(many=True),
            404: "Department not found."
        },
        manual_parameters=[
            openapi.Parameter(
                'identifier',
                openapi.IN_PATH,
                description="ID or slug of the department to fetch assets for",
                type=openapi.TYPE_STRING,
                required=True
            )
        ]
    )
    def get(self, request, identifier, format=None):
        department = get_object_by_id_or_slug(Department, identifier, id_field='id', slug_field='slug')
        assets = Asset.objects.filter(department=department, is_removed=False)
        serializer = AssetSerializer(assets, many=True)
        return Response(serializer.data)


class TrackingByOperationalStatusView(APIView):
    """
    View to return all assets filtered by a given operational status.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve all assets filtered by a specific operational status.",
        responses={
            200: AssetSerializer(many=True),
            400: "Invalid operational status provided."
        },
        manual_parameters=[
            openapi.Parameter(
                'operational_status',
                openapi.IN_QUERY,
                description="The operational status to filter assets by",
                type=openapi.TYPE_STRING,
                required=True,
                enum=Asset.OPERATIONAL_STATUS
            )
        ]
    )
    def get(self, request, format=None):
        # Retrieve the operational status from the query parameters
        status_query = request.query_params.get('operational_status')

        # Validate the operational status
        if status_query not in Asset.OPERATIONAL_STATUS:
            return Response({'error': 'Invalid operational status provided.'}, status=status.HTTP_400_BAD_REQUEST)

        # Filter assets based on the operational status
        assets = Asset.objects.filter(operational_status=status_query, is_removed=False)
        serializer = AssetSerializer(assets, many=True)
        return Response(serializer.data)


class TotalAssetsView(APIView):
    """
    View to return the total number of assets in the system.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get the total number of assets currently registered in the system.",
        responses={
            200: openapi.Response(
                description="Total number of assets successfully retrieved.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total_assets': openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="Total count of assets"
                        )
                    }
                )
            )
        }
    )
    def get(self, request, format=None):
        total_assets = Asset.objects.filter(is_removed=False).count()
        return Response({'total_assets': total_assets})


class TotalAssetsUnderMaintenanceView(APIView):
    """
    View to return the total number of assets currently under maintenance.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get the total number of assets currently under maintenance.",
        responses={
            200: openapi.Response(
                description="Total number of assets under maintenance successfully retrieved.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'assets_under_maintenance': openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="Total count of assets under maintenance"
                        )
                    }
                )
            )
        }
    )
    def get(self, request, format=None):
        # filter assets under maintenance
        assets_under_maintenance_count = Asset.objects.filter(
            operational_status=Asset.OPERATIONAL_STATUS.under_maintenance,
            is_removed=False
        ).count()
        return Response({'assets_under_maintenance': assets_under_maintenance_count})


class AuditLogView(APIView):
    """
    API endpoint that returns a list of all audit logs from Django-Auditlog.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Retrieve all Django-Auditlog entries",
        operation_description="Returns a list of all audit log entries recorded by Django-Auditlog, ordered by most recent.",
        responses={
            200: LogEntrySerializer(many=True),
            403: "Forbidden - User is not authorized to access this endpoint."
        },
        manual_parameters=[
            openapi.Parameter(
                'asset_id',
                openapi.IN_QUERY,
                description="Filter logs by asset ID",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'asset_name',
                openapi.IN_QUERY,
                description="Filter logs by asset name",
                type=openapi.TYPE_STRING,
                required=False
            )
        ]
    )
    def get(self, request, format=None):
        asset_id = request.query_params.get('asset_id')
        asset_name = request.query_params.get('asset_name')

        queryset = LogEntry.objects.all().order_by('-timestamp')

        # Filter by asset ID or asset name if provided
        if asset_id:
            queryset = queryset.filter(object_pk=asset_id)
        elif asset_name:
            queryset = queryset.filter(object_repr__icontains=asset_name)

        serializer = LogEntrySerializer(queryset, many=True)
        return Response(serializer.data)


