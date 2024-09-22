from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions,  DjangoModelPermissionsOrAnonReadOnly
from .models import Asset, Department, AssetStatus, ActionLog
from auditlog.models import LogEntry
from .serializers import DepartmentSerializer, AssetSerializer, LogEntrySerializer, ActionLogSerializer
from .utils import get_object_by_id_or_slug
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi





class DepartmentList(APIView):
    """
    List all departments or create a new department.
    """
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access this view

    @swagger_auto_schema(
        operation_description="Get a list of all departments",
        responses={
            200: openapi.Response('List of departments', DepartmentSerializer(many=True)),
            401: 'Unauthorized'
        }
    )
    def get(self, request, format=None):
        departments = Department.objects.all()
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Create a new department",
        request_body=DepartmentSerializer,
        responses={
            201: openapi.Response('Department created', DepartmentSerializer),
            400: 'Bad Request - Invalid Data',
            401: 'Unauthorized'
        }
    )
    def post(self, request, format=None):
        if not request.user.is_staff:
            return Response({"detail": "You do not have permission to perform this action."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = DepartmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class DepartmentDetail(APIView):
    """
    Retrieve, update, or delete a department using either an ID or a slug.
    """
    permission_classes = [IsAuthenticated, DjangoModelPermissions]  # Apply model-level permissions
    
    def get_queryset(self):
        return Department.objects.all()

    def get_object(self, identifier):
        """
        Use the get_object_by_id_or_slug utility to handle both IDs and slugs.
        """
        return get_object_by_id_or_slug(Department, identifier, id_field='id', slug_field='slug')
    
    @swagger_auto_schema(
        operation_description="Retrieve a department by its ID or slug",
        responses={
            200: openapi.Response('Successfully retrieved', DepartmentSerializer),
            404: 'Not Found'
        },
        manual_parameters=[
            openapi.Parameter('identifier', openapi.IN_PATH, description="ID or Slug of the department", type=openapi.TYPE_STRING, required=True)
        ]
    )
    def get(self, request, identifier, format=None):
        department = self.get_object(identifier)
        serializer = DepartmentSerializer(department)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Update a department by its ID or slug",
        request_body=DepartmentSerializer,
        responses={
            200: openapi.Response('Successfully updated', DepartmentSerializer),
            400: 'Invalid input data',
            404: 'Department not found'
        },
        manual_parameters=[
            openapi.Parameter('identifier', openapi.IN_PATH, description="ID or Slug of the department", type=openapi.TYPE_STRING, required=True)
        ]
    )
    def put(self, request, identifier, format=None):
        department = self.get_object(identifier)
        serializer = DepartmentSerializer(department, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Delete a department by its ID or slug",
        responses={
            204: 'Successfully deleted',
            404: 'Department not found'
        },
        manual_parameters=[
            openapi.Parameter('identifier', openapi.IN_PATH, description="ID or Slug of the department", type=openapi.TYPE_STRING, required=True)
        ]
    )
    def delete(self, request, identifier, format=None):
        department = self.get_object(identifier)
        department.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)




class TotalDepartmentsView(APIView):
    """
    View to return the total number of departments in the system.
    """

    @swagger_auto_schema(
        operation_description="Get the total number of departments in the system",
        responses={
            200: openapi.Response(
                description="Successfully retrieved the total number of departments",
                examples={
                    'application/json': {
                        'total_departments': 5  # Example count of departments
                    }
                },
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total_departments': openapi.Schema(type=openapi.TYPE_INTEGER, description="Total number of departments")
                    }
                )
            ),
            500: 'Internal Server Error'
        }
    )
    def get(self, request, format=None):
        total_departments = Department.objects.count()
        return Response({'total_departments': total_departments})



class AssetList(APIView):
    """
    List all assets or create a new asset.
    """
    permission_classes = [IsAuthenticated, DjangoModelPermissionsOrAnonReadOnly]  # Control access based on user permissions

    @swagger_auto_schema(
        operation_description="Retrieve a list of all assets",
        responses={
            200: openapi.Response('Successfully retrieved', AssetSerializer(many=True)),
            401: 'Unauthorized - Authentication credentials were not provided.'
        }
    )
    def get(self, request, format=None):
        assets = Asset.objects.all()
        serializer = AssetSerializer(assets, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Create a new asset",
        request_body=AssetSerializer,
        responses={
            201: openapi.Response('Asset created successfully', AssetSerializer),
            400: 'Bad request due to invalid input',
            401: 'Unauthorized - Authentication credentials were not provided.'
        }
    )
    def post(self, request, format=None):
        serializer = AssetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class TrackingByDepartmentView(APIView):
    """
    View to return all assets under a specific department.
    """
    permission_classes = [IsAuthenticated]  # Ensure that only authenticated users can access this view.

    @swagger_auto_schema(
        operation_description="Retrieve all assets belonging to a specific department.",
        responses={
            200: openapi.Response(
                description="List of assets in the department",
                schema=AssetSerializer(many=True)
            ),
            404: "Department not found"
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
        # Use the utility function to fetch the department by ID or slug
        department = get_object_by_id_or_slug(Department, identifier)
        
        # Filter assets by the department
        assets = Asset.objects.filter(department=department)
        serializer = AssetSerializer(assets, many=True)
        
        return Response(serializer.data)



class TrackingByStatusView(APIView):
    """
    View to return all assets filtered by a given status.
    """
    
    @swagger_auto_schema(
        operation_description="Retrieve all assets filtered by a specific status.",
        responses={
            200: openapi.Response(
                description="List of assets matching the specified status",
                schema=AssetSerializer(many=True)
            ),
            400: "Invalid status provided."
        },
        manual_parameters=[
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="The status to filter assets by",
                type=openapi.TYPE_STRING,
                required=True
            )
        ]
    )
    def get(self, request, format=None):
        # Retrieve the status from the query parameters
        status_query = request.query_params.get('status')

        # Validate the status
        if status_query not in AssetStatus.values:
            return Response({'error': 'Invalid status provided.'}, status=status.HTTP_400_BAD_REQUEST)

        # Filter assets based on the status
        assets = Asset.objects.filter(status=status_query)
        serializer = AssetSerializer(assets, many=True)
        
        return Response(serializer.data)


class AssetDetail(APIView):
    """
    Retrieve, update, or delete an asset.
    """
    def get_object(self, pk):
        try:
            return Asset.objects.get(pk=pk)
        except Asset.DoesNotExist:
            raise Http404
    
    @swagger_auto_schema(
        operation_description="Retrieve an asset by its primary key.",
        responses={
            200: openapi.Response(
                description="Asset found and returned successfully.",
                schema=AssetSerializer()
            ),
            404: "Asset not found."
        }
    )
    def get(self, request, pk, format=None):
        asset = self.get_object(pk)
        serializer = AssetSerializer(asset)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Update an asset by its primary key.",
        request_body=AssetSerializer(),
        responses={
            200: openapi.Response(
                description="Asset updated successfully.",
                schema=AssetSerializer()
            ),
            400: "Invalid data provided.",
            404: "Asset not found."
        }
    )
    def put(self, request, pk, format=None):
        asset = self.get_object(pk)
        serializer = AssetSerializer(asset, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Delete an asset by its primary key.",
        responses={
            204: "Asset deleted successfully.",
            404: "Asset not found."
        }
    )
    def delete(self, request, pk, format=None):
        asset = self.get_object(pk)
        asset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TotalAssetsView(APIView):
    """
    View to return the total number of assets in the system.
    """
    
    @swagger_auto_schema(
        operation_description="Get the total number of assets currently registered in the system.",
        responses={
            200: openapi.Response(
                description="Total number of assets successfully retrieved.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total_assets': openapi.Schema(type=openapi.TYPE_INTEGER, description="Total count of assets")
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
                            description="Total count of assets under maintenance status"
                        )
                    }
                )
            )
        }
    )
    def get(self, request, format=None):
        # Using the AssetStatus.REPAIR to filter assets under maintenance
        assets_under_maintenance_count = Asset.objects.filter(status=AssetStatus.REPAIR).count()
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
            200: openapi.Response('List of audit logs', LogEntrySerializer(many=True)),
            403: "Forbidden - User is not authorized to access this endpoint"
        }
    )
    def get(self, request, format=None):
        asset_id = request.query_params.get('asset_id')
        asset_name = request.query_params.get('asset_name')

        queryset = LogEntry.objects.all()

        # Filter by asset ID or asset name if provided
        if asset_id:
            queryset = queryset.filter(object_pk=asset_id)
        elif asset_name:
            queryset = queryset.filter(object_repr__icontains=asset_name)

        serializer = LogEntrySerializer(queryset, many=True)
        return Response(serializer.data)


class ActionLogView(APIView):
    """
    API endpoint that returns a list of all action logs from custom ActionLog.
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Retrieve all custom ActionLog entries",
        operation_description="Returns a list of all action log entries from the custom ActionLog model, detailing specific user actions on assets.",
        responses={
            200: openapi.Response('List of action logs', ActionLogSerializer(many=True)),
            403: "Forbidden - User is not authorized to access this endpoint"
        }
    )
    def get(self, request, format=None):
        logs = ActionLog.objects.all().order_by('-timestamp')
        serializer = ActionLogSerializer(logs, many=True)
        return Response(serializer.data)