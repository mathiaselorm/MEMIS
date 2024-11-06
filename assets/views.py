from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from rest_framework.exceptions import ValidationError

from .models import Asset, Department
from auditlog.models import LogEntry
from .serializers import DepartmentSerializer, AssetSerializer, LogEntrySerializer
from .utils import get_object_by_id_or_slug
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from accounts.permissions import IsAdminOrSuperAdmin



class DepartmentList(generics.ListCreateAPIView):
    """
    List all departments or create a new department.
    """
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    queryset = Department.objects.all()

    def get_permissions(self):
        if self.request.method == "POST":
            self.permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]
        return super().get_permissions()

    @swagger_auto_schema(
        operation_description="Retrieve a list of all departments. Only authenticated users can view the list.",
        responses={
            200: openapi.Response(
                description="List of all departments.",
                schema=DepartmentSerializer(many=True),
                examples={
                    "application/json": [
                        {
                            "id": 1,
                            "name": "Finance Department",
                            "slug": "finance-department",
                            "head": 3,
                            "head_name": "John Doe",
                            "contact_phone": "+123456789",
                            "contact_email": "finance@example.com",
                            "total_assets": 10,
                            "active_assets": 5,
                            "archive_assets": 2,
                            "assets_under_maintenance": 1,
                            "total_commissioned_assets": 8,
                            "total_decommissioned_assets": 1,
                            "is_draft": False,
                            "status": "published"
                        }
                    ]
                }
            ),
            401: openapi.Response(
                description="Unauthorized access.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Error message"
                        )
                    }
                ),
                examples={
                    "application/json": {"detail": "Authentication credentials were not provided."}
                }
            )
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new department. Only staff users have permission to create.",
        request_body=DepartmentSerializer,
        responses={
            201: openapi.Response(
                description="Department successfully created.",
                schema=DepartmentSerializer,
                examples={
                    "application/json": {
                        "id": 2,
                        "name": "HR Department",
                        "slug": "hr-department",
                        "head": 4,
                        "head_name": "Jane Smith",
                        "contact_phone": "+987654321",
                        "contact_email": "hr@example.com",
                        "total_assets": 5,
                        "active_assets": 3,
                        "archive_assets": 1,
                        "assets_under_maintenance": 0,
                        "total_commissioned_assets": 4,
                        "total_decommissioned_assets": 0,
                        "is_draft": False,
                        "status": "published"
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request - Invalid data submitted.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    additional_properties=openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING)
                    )
                ),
                examples={
                    "application/json": {
                        "name": ["This field is required."]
                    }
                }
            ),
            403: openapi.Response(
                description="Permission denied - Only staff users can create departments.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Error message"
                        )
                    }
                ),
                examples={
                    "application/json": {"detail": "You do not have permission to perform this action."}
                }
            ),
            401: openapi.Response(
                description="Unauthorized - User is not authenticated.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Error message"
                        )
                    }
                ),
                examples={
                    "application/json": {"detail": "Authentication credentials were not provided."}
                }
            ),
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

    def get_object(self):
        """
        Override to get the department by ID or slug.
        """
        identifier = self.kwargs['identifier']
        return get_object_by_id_or_slug(Department, identifier, id_field='id', slug_field='slug')

    @swagger_auto_schema(
        operation_description="Retrieve a department by its ID or slug.",
        responses={
            200: openapi.Response(
                description="Department details retrieved successfully.",
                schema=DepartmentSerializer,
                examples={
                    "application/json": {
                        "id": 1,
                        "name": "Finance Department",
                        "slug": "finance-department",
                        "head": 3,
                        "head_name": "John Doe",
                        "contact_phone": "+123456789",
                        "contact_email": "finance@example.com",
                        "total_assets": 10,
                        "active_assets": 5,
                        "archive_assets": 2,
                        "assets_under_maintenance": 1,
                        "total_commissioned_assets": 8,
                        "total_decommissioned_assets": 1,
                        "is_draft": False,
                        "status": "published"
                    }
                }
            ),
            404: openapi.Response(
                description="Department not found.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Error message"
                        )
                    }
                ),
                examples={
                    "application/json": {"detail": "Not found."}
                }
            ),
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
            200: openapi.Response(
                description="Department successfully updated.",
                schema=DepartmentSerializer,
                examples={
                    "application/json": {
                        "id": 1,
                        "name": "Finance Department",
                        "slug": "finance-department",
                        "head": 3,
                        "head_name": "John Doe",
                        "contact_phone": "+123456789",
                        "contact_email": "finance@example.com",
                        "total_assets": 10,
                        "active_assets": 5,
                        "archive_assets": 2,
                        "assets_under_maintenance": 1,
                        "total_commissioned_assets": 8,
                        "total_decommissioned_assets": 1,
                        "is_draft": False,
                        "status": "published"
                    }
                }
            ),
            400: openapi.Response(
                description="Invalid data provided.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    additional_properties=openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING)
                    )
                ),
                examples={
                    "application/json": {
                        "name": ["This field may not be blank."]
                    }
                }
            ),
            404: openapi.Response(
                description="Department not found.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Error message"
                        )
                    }
                ),
                examples={
                    "application/json": {"detail": "Not found."}
                }
            )
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
        partial = True  # Enable partial updates
        return self.update(request, *args, **kwargs, partial=partial)

    @swagger_auto_schema(
        operation_description="Delete a department by its ID or slug.",
        responses={
            204: openapi.Response(
                description="Department successfully deleted."
            ),
            404: openapi.Response(
                description="Department not found.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Error message"
                        )
                    }
                ),
                examples={
                    "application/json": {"detail": "Not found."}
                }
            )
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


class TotalDepartmentsView(generics.GenericAPIView):
    """
    View to return the total number of departments in the system.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve the total number of departments in the system.",
        responses={
            200: openapi.Response(
                description="Total count of departments.",
                examples={
                    'application/json': {'total_departments': 5}
                },
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
            401: openapi.Response(
                description="Unauthorized - user must be authenticated.",
                examples={
                    "application/json": {"detail": "Authentication credentials were not provided."}
                }
            ),
            500: openapi.Response(
                description="Server error."
            )
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
        responses={
            200: openapi.Response(
                description="List of all assets.",
                schema=AssetSerializer(many=True),
            ),
            401: openapi.Response(
                description="Unauthorized access.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
                examples={
                    "application/json": {"detail": "Authentication credentials were not provided."}
                }
            )
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new asset.",
        request_body=AssetSerializer,
        responses={
            201: openapi.Response(
                description="Asset successfully created.",
                schema=AssetSerializer,
            ),
            400: openapi.Response(
                description="Bad request - Invalid data submitted.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    additional_properties=openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING)
                    )
                ),
            ),
            401: openapi.Response(
                description="Unauthorized - User is not authenticated.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
                examples={
                    "application/json": {"detail": "Authentication credentials were not provided."}
                }
            ),
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
    lookup_field = 'pk'

    @swagger_auto_schema(
        operation_description="Retrieve an asset by its primary key.",
        responses={
            200: openapi.Response(
                description="Asset retrieved successfully.",
                schema=AssetSerializer,
            ),
            404: openapi.Response(
                description="Asset not found.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
                examples={
                    "application/json": {"detail": "Not found."}
                }
            ),
        },
        manual_parameters=[
            openapi.Parameter(
                'pk', openapi.IN_PATH,
                description="Primary key of the asset",
                type=openapi.TYPE_INTEGER, required=True
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update an asset by its primary key.",
        request_body=AssetSerializer,
        responses={
            200: openapi.Response(
                description="Asset updated successfully.",
                schema=AssetSerializer,
            ),
            400: openapi.Response(
                description="Invalid data provided.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    additional_properties=openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING)
                    )
                ),
            ),
            404: openapi.Response(
                description="Asset not found.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
                examples={
                    "application/json": {"detail": "Not found."}
                }
            )
        },
        manual_parameters=[
            openapi.Parameter(
                'pk', openapi.IN_PATH,
                description="Primary key of the asset",
                type=openapi.TYPE_INTEGER, required=True
            )
        ]
    )
    def put(self, request, *args, **kwargs):
        partial = True  # Enable partial updates
        return self.update(request, *args, **kwargs, partial=partial)

    @swagger_auto_schema(
        operation_description="Partially update an asset by its primary key.",
        request_body=AssetSerializer(partial=True),
        responses={
            200: openapi.Response(
                description="Asset partially updated successfully.",
                schema=AssetSerializer,
            ),
            400: openapi.Response(
                description="Invalid data provided.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    additional_properties=openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING)
                    )
                ),
            ),
            404: openapi.Response(
                description="Asset not found.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
                examples={
                    "application/json": {"detail": "Not found."}
                }
            )
        },
        manual_parameters=[
            openapi.Parameter(
                'pk', openapi.IN_PATH,
                description="Primary key of the asset",
                type=openapi.TYPE_INTEGER, required=True
            )
        ]
    )
    def patch(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete an asset by its primary key.",
        responses={
            204: openapi.Response(
                description="Asset deleted successfully."
            ),
            404: openapi.Response(
                description="Asset not found.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
                examples={
                    "application/json": {"detail": "Not found."}
                }
            )
        },
        manual_parameters=[
            openapi.Parameter(
                'pk', openapi.IN_PATH,
                description="Primary key of the asset",
                type=openapi.TYPE_INTEGER, required=True
            )
        ]
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


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
            200: openapi.Response(
                description="List of assets matching the specified operational status.",
                schema=AssetSerializer(many=True),
            ),
            400: openapi.Response(
                description="Invalid operational status provided.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
                examples={
                    "application/json": {"error": "Invalid operational status provided."}
                }
            ),
            401: openapi.Response(
                description="Unauthorized access.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
                examples={
                    "application/json": {"detail": "Authentication credentials were not provided."}
                }
            ),
        },
        manual_parameters=[
            openapi.Parameter(
                'operational_status',
                openapi.IN_QUERY,
                description="The operational status to filter assets by",
                type=openapi.TYPE_STRING,
                required=True,
                enum=[choice[0] for choice in Asset.OPERATIONAL_STATUS]  # Corrected line
            )
        ]
    )
    def get(self, request, format=None):
        # Retrieve the operational status from the query parameters
        status_query = request.query_params.get('operational_status')

        # Validate the operational status
        valid_statuses = [choice[0] for choice in Asset.OPERATIONAL_STATUS]
        if status_query not in valid_statuses:
            return Response({'error': 'Invalid operational status provided.'}, status=status.HTTP_400_BAD_REQUEST)

        # Filter assets based on the operational status
        assets = Asset.objects.filter(operational_status=status_query, is_removed=False)
        serializer = AssetSerializer(assets, many=True)
        return Response(serializer.data)




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


