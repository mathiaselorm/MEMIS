from rest_framework import generics, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import api_view, permission_classes

from .models import (
    Asset, Department, AssetActivity,
    MaintenanceSchedule
    )
from auditlog.models import LogEntry
from .serializers import(
    DepartmentWriteSerializer, DepartmentReadSerializer,
    AssetWriteSerializer, AssetReadSerializer,
     AssetActivityReadSerializer, AssetActivityWriteSerializer,
    AssetsLogEntrySerializer, MaintenanceScheduleWriteSerializer, 
    MaintenanceScheduleReadSerializer
    )
from .utils import get_object_by_id_or_slug
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from accounts.permissions import IsAdminOrSuperAdmin
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied, ValidationError

import logging

logger = logging.getLogger(__name__)



class DepartmentList(generics.ListCreateAPIView):
    """
    List all departments or create a new department.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Retrieve departments, optionally filtered by 'status' and 'is_removed' query parameters.
        """
        queryset = Department.all_objects.all()
        status_param = self.request.query_params.get('status')
        is_removed_param = self.request.query_params.get('is_removed')

        if status_param:
            queryset = queryset.filter(status=status_param)
        if is_removed_param is not None:
            is_removed = is_removed_param.lower() == 'true'
            queryset = queryset.filter(is_removed=is_removed)
        return queryset

    def get_permissions(self):
        if self.request.method == "POST":
            self.permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DepartmentWriteSerializer
        return DepartmentReadSerializer
    
    @swagger_auto_schema(
        tags=['Departments'],
        operation_description="Retrieve a list of departments. Optionally filter by status.",
        manual_parameters=[
            openapi.Parameter(
                'status', openapi.IN_QUERY,
                description="Filter departments by status ('draft' or 'published')",
                type=openapi.TYPE_STRING,
                required=False,
                enum=['draft', 'published']
            ),
        ],
        responses={200: DepartmentReadSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Departments'],
        operation_description="Create a new department. Only staff users have permission to create.",
        request_body=DepartmentWriteSerializer,
        responses={
            201: openapi.Response(
                description="Department successfully created.",
                schema=DepartmentWriteSerializer,
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
    permission_classes = [IsAuthenticated]
    queryset = Department.all_objects.all()

    def get_object(self):
        """
        Override to get the department by ID or slug.
        """
        identifier = self.kwargs['identifier']
        return get_object_by_id_or_slug(Department, identifier, id_field='id', slug_field='slug')

    def get_serializer_class(self):
        if self.request.method in ['GET']:
            return DepartmentReadSerializer
        else:
            return DepartmentWriteSerializer

    def perform_destroy(self, instance):
        if instance.is_removed:
            # If user is Admin or SuperAdmin, permanently delete
            if IsAdminOrSuperAdmin().has_permission(self.request, self):
                instance.delete()
            else:
                raise PermissionDenied("You do not have permission to permanently delete this department.")
        else:
            # Set is_removed to True (soft delete)
            instance.is_removed = True
            instance.save()

    @swagger_auto_schema(
        tags=['Departments'],
        operation_description="Retrieve a department by its ID or slug.",
        responses={
            200: openapi.Response(
                description="Department details retrieved successfully.",
                schema=DepartmentReadSerializer,
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
        """
        Retrieve a department by its ID or slug.
        """
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Departments'],
        operation_description="Update a department by its ID or slug. Supports partial updates.",
        request_body=DepartmentWriteSerializer,
        responses={
            200: openapi.Response(
                description="Department successfully updated.",
                schema=DepartmentWriteSerializer,
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
        """
        Update a department by its ID or slug.
        """
        partial = True  # Enable partial updates
        return self.update(request, *args, **kwargs, partial=partial)

    @swagger_auto_schema(
        tags=['Departments'],
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
        """
        Delete a department by its ID or slug.
        """
        return super().delete(request, *args, **kwargs)


class TotalDepartmentsView(generics.GenericAPIView):
    """
    View to return the total number of departments in the system.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Departments'],
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
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retrieve assets, optionally filtered by 'status' and 'is_removed' query parameters.
        """
        queryset = Asset.all_objects.all()  # Includes soft-deleted assets
        status_param = self.request.query_params.get('status')
        is_removed_param = self.request.query_params.get('is_removed')

        if status_param:
            queryset = queryset.filter(status=status_param)
        if is_removed_param is not None:
            # Convert is_removed_param to boolean
            is_removed = is_removed_param.lower() == 'true'
            queryset = queryset.filter(is_removed=is_removed)
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AssetWriteSerializer
        return AssetReadSerializer

    @swagger_auto_schema(
        tags=['Assets'],
        operation_description="Retrieve a list of assets. Optionally filter by status.",
        manual_parameters=[
            openapi.Parameter(
                'status', openapi.IN_QUERY,
                description="Filter assets by status ('draft' or 'published')",
                type=openapi.TYPE_STRING,
                required=False,
                enum=['draft', 'published']
            ),
        ],
        responses={
            200: AssetReadSerializer(many=True),
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
        """
        Retrieve a list of all assets.
        """
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Assets'],
        operation_description="Create a new asset.",
        request_body=AssetWriteSerializer,
        responses={
            201: openapi.Response(
                description="Asset successfully created.",
                schema=AssetWriteSerializer,
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
        """
        Create a new asset.
        """
        return super().post(request, *args, **kwargs)


class AssetDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete an asset.
    """
    permission_classes = [IsAuthenticated]
    queryset = Asset.all_objects.all()
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.request.method in ['GET']:
            return AssetReadSerializer
        else:
            return AssetWriteSerializer

    def perform_destroy(self, instance):
        if instance.is_removed:
            # Permanently delete if admin or superadmin
            if IsAdminOrSuperAdmin().has_permission(self.request, self):
                Asset.all_objects.filter(pk=instance.pk).delete()
                return "permanent_delete"
            else:
                raise PermissionDenied("You do not have permission to permanently delete this asset.")
        else:
            # Soft delete
            instance.is_removed = True
            instance.save()
            return "soft_delete"

    @swagger_auto_schema(
        tags=['Assets'],
        operation_description="Retrieve an asset by its primary key.",
        responses={
            200: openapi.Response(
                description="Asset retrieved successfully.",
                schema=AssetReadSerializer,
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
        """
        Retrieve an asset by its primary key.
        """
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Assets'],
        operation_description="Update an asset by its primary key.",
        request_body=AssetWriteSerializer,
        responses={
            200: openapi.Response(
                description="Asset updated successfully.",
                schema=AssetWriteSerializer,
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
        """
        Update an asset by its primary key.
        """
        partial = True  # Enable partial updates
        return self.update(request, *args, **kwargs, partial=partial)

    @swagger_auto_schema(
        tags=['Assets'],
        operation_description="Partially update an asset by its primary key.",
        request_body=AssetWriteSerializer(partial=True),
        responses={
            200: openapi.Response(
                description="Asset partially updated successfully.",
                schema=AssetWriteSerializer,
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
        """
        Partially update an asset by its primary key.
        """
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Assets'],
        operation_description="Delete an asset by its primary key. If the asset is not soft-deleted, it will be soft-deleted. If it is already soft-deleted, it will be permanently deleted (only for Admin or SuperAdmin).",
        responses={
            204: openapi.Response(
                description="Asset deleted successfully."
            ),
            403: openapi.Response(
                description="Permission denied.",
                examples={
                    "application/json": {"detail": "You do not have permission to permanently delete this asset."}
                }
            ),
            404: openapi.Response(
                description="Asset not found.",
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
        instance = self.get_object()  # Retrieve the instance
        deletion_status = self.perform_destroy(instance)  # Delegate logic to `perform_destroy`
        
        # Customize the response based on the deletion state
        if deletion_status == "permanent_delete":
            return Response(
                {"detail": "Asset permanently deleted."},
                status=status.HTTP_204_NO_CONTENT
            )
        elif deletion_status == "soft_delete":
            return Response(
                {"detail": "Asset soft-deleted successfully."},
                status=status.HTTP_204_NO_CONTENT
            )

class TotalAssetsView(APIView):
    """
    View to return the total number of assets in the system.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Assets'],
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
        total_assets = Asset.objects.count()
        return Response({'total_assets': total_assets})


class TotalAssetsUnderMaintenanceView(APIView):
    """
    View to return the total number of assets currently under maintenance.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Assets'],
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


# class TrackingByDepartmentView(APIView):
#     """
#     View to return all assets under a specific department.
#     """
#     permission_classes = [IsAuthenticated]

#     @swagger_auto_schema(
#         tags=['Assets'],
#         operation_description="Retrieve all assets belonging to a specific department.",
#         responses={
#             200: AssetReadSerializer(many=True),
#             404: "Department not found."
#         },
#         manual_parameters=[
#             openapi.Parameter(
#                 'identifier',
#                 openapi.IN_PATH,
#                 description="ID or slug of the department to fetch assets for",
#                 type=openapi.TYPE_STRING,
#                 required=True
#             )
#         ]
#     )
#     def get(self, request, identifier, format=None):
#         department = get_object_by_id_or_slug(Department, identifier, id_field='id', slug_field='slug')
#         assets = Asset.objects.filter(department=department, is_removed=False)
#         serializer = AssetReadSerializer(assets, many=True)
#         return Response(serializer.data)


# class TrackingByOperationalStatusView(APIView):
#     """
#     View to return all assets filtered by a given operational status.
#     """
#     permission_classes = [IsAuthenticated]

#     @swagger_auto_schema(
#         tags=['Assets'],
#         operation_description="Retrieve all assets filtered by a specific operational status.",
#         responses={
#             200: openapi.Response(
#                 description="List of assets matching the specified operational status.",
#                 schema=AssetReadSerializer(many=True),
#             ),
#             400: openapi.Response(
#                 description="Invalid operational status provided.",
#                 schema=openapi.Schema(
#                     type=openapi.TYPE_OBJECT,
#                     properties={
#                         "error": openapi.Schema(type=openapi.TYPE_STRING)
#                     }
#                 ),
#                 examples={
#                     "application/json": {"error": "Invalid operational status provided."}
#                 }
#             ),
#             401: openapi.Response(
#                 description="Unauthorized access.",
#                 schema=openapi.Schema(
#                     type=openapi.TYPE_OBJECT,
#                     properties={
#                         "detail": openapi.Schema(type=openapi.TYPE_STRING)
#                     }
#                 ),
#                 examples={
#                     "application/json": {"detail": "Authentication credentials were not provided."}
#                 }
#             ),
#         },
#         manual_parameters=[
#             openapi.Parameter(
#                 'operational_status',
#                 openapi.IN_QUERY,
#                 description="The operational status to filter assets by",
#                 type=openapi.TYPE_STRING,
#                 required=True,
#                 enum=[choice[0] for choice in Asset.OPERATIONAL_STATUS]  # Corrected line
#             )
#         ]
#     )
#     def get(self, request, format=None):
#         # Retrieve the operational status from the query parameters
#         status_query = request.query_params.get('operational_status')

#         # Validate the operational status
#         valid_statuses = [choice[0] for choice in Asset.OPERATIONAL_STATUS]
#         if status_query not in valid_statuses:
#             return Response({'error': 'Invalid operational status provided.'}, status=status.HTTP_400_BAD_REQUEST)

#         # Filter assets based on the operational status
#         assets = Asset.objects.filter(operational_status=status_query, is_removed=False)
#         serializer = AssetReadSerializer(assets, many=True)
#         return Response(serializer.data)



# class SoftDeletedAssetsView(APIView):
#     """
#     View to list all soft-deleted assets.
#     """
#     permission_classes = [IsAuthenticated]

#     @swagger_auto_schema(
#         operation_description="Retrieve a list of all soft-deleted assets.",
#         responses={
#             200: openapi.Response(
#                 description="List of soft-deleted assets.",
#                 schema=AssetReadSerializer(many=True),
#             ),
#             401: openapi.Response(
#                 description="Unauthorized access.",
#                 examples={
#                     "application/json": {"detail": "Authentication credentials were not provided."}
#                 }
#             ),
#         }
#     )
#     def get(self, request, format=None):
#         """
#         Retrieve all soft-deleted assets.
#         """
#         assets = Asset.all_objects.filter(is_removed=True)
#         serializer = AssetReadSerializer(assets, many=True)
#         return Response(serializer.data)


@swagger_auto_schema(
    method='post',
    operation_description="Restore a soft-deleted asset.",
    responses={
        200: openapi.Response(
            description="Asset restored successfully.",
            examples={
                "application/json": {"detail": "Asset restored successfully."}
            }
        ),
        404: openapi.Response(
            description="Asset not found or not soft-deleted.",
            examples={
                "application/json": {"detail": "Asset not found or not soft-deleted."}
            }
        ),
    },
    manual_parameters=[
        openapi.Parameter(
            'pk', openapi.IN_PATH,
            description="Primary key of the asset to restore",
            type=openapi.TYPE_INTEGER,
            required=True,
        )
    ]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def restore_asset(request, pk):
    """
    Restore a soft-deleted asset by its primary key.

    Parameters:
    - pk (int): Primary key of the asset to restore.

    Returns:
    - 200 OK: Asset restored successfully.
    - 404 Not Found: Asset not found or not soft-deleted.
    """
    try:
        asset = Asset.all_objects.get(pk=pk, is_removed=True)
        asset.is_removed = False
        asset.save()
        return Response({'detail': 'Asset restored successfully.'}, status=status.HTTP_200_OK)
    except Asset.DoesNotExist:
        return Response({'detail': 'Asset not found or not soft-deleted.'}, status=status.HTTP_404_NOT_FOUND)
    
    
# @swagger_auto_schema(
#     method='delete',
#     operation_description="Permanently delete a soft-deleted asset.",
#     responses={
#         204: openapi.Response(
#             description="Asset permanently deleted.",
#         ),
#         404: openapi.Response(
#             description="Asset not found or not soft-deleted.",
#             examples={
#                 "application/json": {"detail": "Asset not found or not soft-deleted."}
#             }
#         ),
#     },
#     manual_parameters=[
#         openapi.Parameter(
#             'pk', openapi.IN_PATH,
#             description="Primary key of the asset to permanently delete",
#             type=openapi.TYPE_INTEGER,
#             required=True,
#         )
#     ]
# )
# @api_view(['DELETE'])
# @permission_classes([IsAuthenticated, IsAdminOrSuperAdmin])
# def permanent_delete_asset(request, pk):
#     """
#     Permanently delete a soft-deleted asset by its primary key.

#     Parameters:
#     - pk (int): Primary key of the asset to permanently delete.

#     Returns:
#     - 204 No Content: Asset permanently deleted.
#     - 404 Not Found: Asset not found or not soft-deleted.
#     """
#     try:
#         asset = Asset.all_objects.get(pk=pk, is_removed=True)
#         asset.delete()
#         return Response({'detail': 'Asset permanently deleted.'}, status=status.HTTP_204_NO_CONTENT)
#     except Asset.DoesNotExist:
#         return Response({'detail': 'Asset not found or not soft-deleted.'}, status=status.HTTP_404_NOT_FOUND)



class  AssetActivitiesByAssetView(generics.ListCreateAPIView):
    """
    List all activities for a specific asset or create a new activity.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['technician', 'activity_type']

    def get_queryset(self):
        asset_id = self.kwargs.get('asset_id')
        queryset = (
            AssetActivity.objects
            .filter(asset_id=asset_id)
            .select_related('asset', 'technician')
        )
        
        # Filtering by technician and activity_type
        technician = self.request.query_params.get('technician')
        activity_type = self.request.query_params.get('activity_type')

        if technician:
            queryset = queryset.filter(technician_id=technician)
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
        
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AssetActivityWriteSerializer
        return AssetActivityReadSerializer

    def perform_create(self, serializer):
        asset_id = self.kwargs.get('asset_id')
        asset = get_object_or_404(Asset, id=asset_id)
        serializer.save(asset=asset)

    @swagger_auto_schema(
        tags=['Asset Activities'],
        operation_description="Retrieve all activities for a specific asset with optional filtering.",
        manual_parameters=[
            openapi.Parameter(
                'asset_id', openapi.IN_PATH,
                description="ID of the asset",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'technician', openapi.IN_QUERY,
                description="Filter by technician ID",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'activity_type', openapi.IN_QUERY,
                description="Filter by activity type (maintenance, repair, calibration)",
                type=openapi.TYPE_STRING,
                enum=['maintenance', 'repair', 'calibration'],
                required=False
            ),
        ],
        responses={
            200: AssetActivityReadSerializer(many=True),
            401: openapi.Response(
                description="Unauthorized access.",
                examples={"application/json": {"detail": "Authentication credentials were not provided."}}
            )
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve all activities for a specific asset with optional filtering.
        """
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Asset Activities'],
        operation_description="Create a new activity for a specific asset.",
        request_body=AssetActivityWriteSerializer,
        responses={
            201: AssetActivityReadSerializer,
            400: openapi.Response(
                description="Invalid data provided.",
                examples={"application/json": {"detail": "Validation error details."}}
            ),
            401: openapi.Response(
                description="Unauthorized access.",
                examples={"application/json": {"detail": "Authentication credentials were not provided."}}
            )
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Create a new activity for a specific asset.
        """
        return super().post(request, *args, **kwargs)


class AssetActivityDetailByAssetView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete an activity for a specific asset.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        asset_id = self.kwargs.get('asset_id')
        return AssetActivity.objects.filter(asset_id=asset_id)

    def get_object(self):
        queryset = self.get_queryset()
        activity_id = self.kwargs.get('activity_id')
        obj = get_object_or_404(queryset, id=activity_id)
        return obj

    def get_serializer_class(self):
        return AssetActivityWriteSerializer  # Since PUT handles partial updates

    def put(self, request, *args, **kwargs):
        """
        Update an activity for a specific asset. Supports partial updates.
        """
        kwargs['partial'] = True  # Allow partial updates
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Asset Activities'],
        operation_description="Retrieve an activity for a specific asset.",
        manual_parameters=[
            openapi.Parameter(
                'asset_id', openapi.IN_PATH,
                description="ID of the asset",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'activity_id', openapi.IN_PATH,
                description="ID of the activity",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
        ],
        responses={
            200: AssetActivityReadSerializer,
            404: openapi.Response(
                description="Activity not found.",
                examples={"application/json": {"detail": "Not found."}}
            ),
            401: openapi.Response(
                description="Unauthorized access.",
                examples={"application/json": {"detail": "Authentication credentials were not provided."}}
            )
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve an activity for a specific asset.
        """
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Asset Activities'],
        operation_description="Update an activity for a specific asset. Supports partial updates.",
        request_body=AssetActivityWriteSerializer,
        responses={
            200: AssetActivityReadSerializer,
            400: openapi.Response(
                description="Invalid data provided.",
                examples={"application/json": {"detail": "Validation error details."}}
            ),
            404: openapi.Response(
                description="Activity not found.",
                examples={"application/json": {"detail": "Not found."}}
            ),
            401: openapi.Response(
                description="Unauthorized access.",
                examples={"application/json": {"detail": "Authentication credentials were not provided."}}
            )
        }
    )
    def put(self, request, *args, **kwargs):
        """
        Update an activity for a specific asset. Supports partial updates.
        """
        kwargs['partial'] = True  # Allow partial updates
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Asset Activities'],
        operation_description="Delete an activity for a specific asset.",
        responses={
            204: openapi.Response(description="Activity deleted successfully."),
            404: openapi.Response(
                description="Activity not found.",
                examples={"application/json": {"detail": "Not found."}}
            ),
            401: openapi.Response(
                description="Unauthorized access.",
                examples={"application/json": {"detail": "Authentication credentials were not provided."}}
            )
        }
    )
    def delete(self, request, *args, **kwargs):
        """
        Delete an activity for a specific asset.
        """
        return super().delete(request, *args, **kwargs)



class AssetActivityListCreateView(generics.ListCreateAPIView):
    """
    List all asset activities or create a new activity.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        include_deleted = self.request.query_params.get('include_deleted', 'false').lower()
        if include_deleted == 'true':
            queryset = AssetActivity.all_objects.all()
        else:
            queryset = AssetActivity.objects.all()
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AssetActivityWriteSerializer
        return AssetActivityReadSerializer

    @swagger_auto_schema(
        tags=['Asset Activities'],
        operation_description="Retrieve a list of all asset activities.",
        manual_parameters=[
            openapi.Parameter(
                'include_deleted', openapi.IN_QUERY,
                description="Include soft-deleted activities (true/false). Default is false.",
                type=openapi.TYPE_BOOLEAN,
                required=False
            ),
        ],
        responses={
            200: AssetActivityReadSerializer(many=True),
            401: openapi.Response(
                description="Unauthorized access.",
                examples={
                    "application/json": {"detail": "Authentication credentials were not provided."}
                }
            )
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve a list of all asset activities.
        """
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Asset Activities'],
        operation_description="Create a new asset activity.",
        request_body=AssetActivityWriteSerializer,
        responses={
            201: AssetActivityReadSerializer,
            400: openapi.Response(
                description="Invalid data provided.",
                examples={
                    "application/json": {"detail": "Validation error details."}
                }
            ),
            401: openapi.Response(
                description="Unauthorized access.",
                examples={
                    "application/json": {"detail": "Authentication credentials were not provided."}
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Create a new asset activity.
        """
        return super().post(request, *args, **kwargs)


class AssetActivityDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete an asset activity.
    """
    lookup_field = 'pk'

    def get_permissions(self):
        if self.request.method == 'DELETE':
            self.permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def get_queryset(self):
        include_deleted = self.request.query_params.get('include_deleted', 'false').lower()
        if include_deleted == 'true':
            queryset = AssetActivity.all_objects.all()
        else:
            queryset = AssetActivity.objects.all()
        return queryset

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return AssetActivityWriteSerializer
        return AssetActivityReadSerializer

    @swagger_auto_schema(
        tags=['Asset Activities'],
        operation_description="Retrieve an asset activity by its primary key.",
        manual_parameters=[
            openapi.Parameter(
                'include_deleted', openapi.IN_QUERY,
                description="Include soft-deleted activity (true/false). Default is false.",
                type=openapi.TYPE_BOOLEAN,
                required=False
            ),
            openapi.Parameter(
                'pk', openapi.IN_PATH,
                description="Primary key of the asset activity",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: AssetActivityReadSerializer,
            404: openapi.Response(
                description="Asset activity not found.",
                examples={
                    "application/json": {"detail": "Not found."}
                }
            ),
            401: openapi.Response(
                description="Unauthorized access.",
                examples={
                    "application/json": {"detail": "Authentication credentials were not provided."}
                }
            )
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve an asset activity by its primary key.
        """
        return super().get(request, *args, **kwargs)



class MaintenanceScheduleListCreateView(generics.ListCreateAPIView):
    """
    List all maintenance schedules or create a new one.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['frequency', 'is_active']
    search_fields = ['title', 'description', 'asset__name']
    ordering_fields = ['start_datetime', 'end_datetime']

    def get_queryset(self):
        """
        Return maintenance schedules accessible to the user.
        """
        user = self.request.user
        if IsAdminOrSuperAdmin().has_permission(self.request, self):
            return MaintenanceSchedule.objects.all()
        else:
            return MaintenanceSchedule.objects.filter(Q(technician=user) | Q(is_general=True))

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MaintenanceScheduleWriteSerializer
        return MaintenanceScheduleReadSerializer

    @swagger_auto_schema(
        tags=['Maintenance Schedules'],
        operation_description="Retrieve a list of maintenance schedules.",
        responses={
            200: MaintenanceScheduleReadSerializer(many=True),
            401: openapi.Response(
                description="Unauthorized",
                examples={"application/json": {"detail": "Authentication credentials were not provided."}}
            )
        }
    )
    def get(self, request, *args, **kwargs):
        """
        List all maintenance schedules.
        """
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Maintenance Schedules'],
        operation_description="Create a new maintenance schedule.",
        request_body=MaintenanceScheduleWriteSerializer,
        responses={
            201: MaintenanceScheduleReadSerializer,
            400: openapi.Response(
                description="Invalid input",
                examples={"application/json": {"detail": "Validation error details."}}
            ),
            401: openapi.Response(
                description="Unauthorized",
                examples={"application/json": {"detail": "Authentication credentials were not provided."}}
            )
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Create a new maintenance schedule.
        """
        return super().post(request, *args, **kwargs)
    

class MaintenanceScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a maintenance schedule.
    """
    lookup_field = 'pk'
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return maintenance schedules accessible to the user.
        """
        user = self.request.user
        if IsAdminOrSuperAdmin().has_permission(self.request, self):
            return MaintenanceSchedule.objects.all()
        else:
            return MaintenanceSchedule.objects.filter(Q(technician=user) | Q(is_general=True))


    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return MaintenanceScheduleWriteSerializer
        return MaintenanceScheduleReadSerializer

    @swagger_auto_schema(
        tags=['Maintenance Schedules'],
        operation_description="Retrieve a maintenance schedule.",
        responses={
            200: MaintenanceScheduleReadSerializer,
            404: openapi.Response(
                description="Not found",
                examples={"application/json": {"detail": "Not found."}}
            ),
            401: openapi.Response(
                description="Unauthorized",
                examples={"application/json": {"detail": "Authentication credentials were not provided."}}
            )
        },
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID of the maintenance schedule", type=openapi.TYPE_INTEGER)
        ]
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve a maintenance schedule.
        """
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Maintenance Schedules'],
        operation_description="Update a maintenance schedule.",
        request_body=MaintenanceScheduleWriteSerializer,
        responses={
            200: MaintenanceScheduleReadSerializer,
            400: openapi.Response(
                description="Invalid input",
                examples={"application/json": {"detail": "Validation error details."}}
            ),
            404: openapi.Response(
                description="Not found",
                examples={"application/json": {"detail": "Not found."}}
            ),
            401: openapi.Response(
                description="Unauthorized",
                examples={"application/json": {"detail": "Authentication credentials were not provided."}}
            )
        }
    )
    def put(self, request, *args, **kwargs):
        """
        Update a maintenance schedule.
        """
        kwargs['partial'] = True  # Allow partial updates
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Maintenance Schedules'],
        operation_description="Delete a maintenance schedule.",
        responses={
            204: openapi.Response(description="No content"),
            404: openapi.Response(
                description="Not found",
                examples={"application/json": {"detail": "Not found."}}
            ),
            401: openapi.Response(
                description="Unauthorized",
                examples={"application/json": {"detail": "Authentication credentials were not provided."}}
            )
        },
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID of the maintenance schedule", type=openapi.TYPE_INTEGER)
        ]
    )
    def delete(self, request, *args, **kwargs):
        """
        Delete a maintenance schedule.
        """
        return super().delete(request, *args, **kwargs)


@swagger_auto_schema(
    method='post',
    operation_description="Deactivate a maintenance schedule by setting is_active=False.",
    responses={200: "Schedule deactivated successfully."}
)
@api_view(['POST'])
def deactivate_schedule(request, pk):
    schedule = get_object_or_404(MaintenanceSchedule, pk=pk)
    if schedule.technician != request.user:
        return Response({'detail': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)
    schedule.is_active = False
    schedule.save()
    return Response({'detail': 'Schedule deactivated.'}, status=status.HTTP_200_OK)




class AuditLogView(APIView):
    """
    API endpoint that returns a list of all audit logs from Django-Auditlog.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Audit Logs'],
        operation_summary="Retrieve all Django-Auditlog entries",
        operation_description="Returns a list of all audit log entries recorded by Django-Auditlog, ordered by most recent.",
        responses={
            200: AssetsLogEntrySerializer(many=True),
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

        serializer = AssetsLogEntrySerializer(queryset, many=True)
        return Response(serializer.data)


