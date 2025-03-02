from rest_framework import generics, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import api_view, permission_classes
from actstream import action

from .models import (
    Equipment, Department, Supplier, EquipmentMaintenanceActivity,
    MaintenanceSchedule
    )
from .serializers import(
    DepartmentWriteSerializer, DepartmentReadSerializer,
    SupplierWriteSerializer, SupplierReadSerializer,
    EquipmentWriteSerializer, EquipmentReadSerializer,
    EquipmentMaintenanceActivityReadSerializer, EquipmentMaintenanceActivityWriteSerializer,
    MaintenanceScheduleWriteSerializer, 
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
    queryset = Department.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DepartmentWriteSerializer
        return DepartmentReadSerializer

    @swagger_auto_schema(
        tags=['Departments'],
        operation_description="Retrieve a list of departments.",
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



class DepartmentDetail(RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a department using either an ID or a slug.
    """
    permission_classes = [IsAuthenticated]
    queryset = Department.objects.all()

    def get_object(self):
        """
        Retrieve the department by its ID or slug.
        """
        identifier = self.kwargs['identifier']
        return get_object_by_id_or_slug(Department, identifier, id_field='id', slug_field='slug')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return DepartmentReadSerializer
        return DepartmentWriteSerializer

    def perform_destroy(self, instance):
        # Perform a hard delete
        user = self.request.user if self.request.user.is_authenticated else None
        action.send(user or instance, verb='deleted department', target=instance)
        instance.delete()

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
                examples={"application/json": {"detail": "Not found."}}
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
                examples={"application/json": {"name": ["This field may not be blank."]}}
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
                examples={"application/json": {"detail": "Not found."}}
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
        kwargs['partial'] = True  # Enable partial updates
        return self.update(request, *args, **kwargs)

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
                examples={"application/json": {"detail": "Not found."}}
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




class SupplierListCreateView(generics.ListCreateAPIView):
    """
    List all suppliers or create a new supplier.
    """
    permission_classes = [IsAuthenticated]
    queryset = Supplier.objects.all() 
     

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SupplierWriteSerializer
        return SupplierReadSerializer

    @swagger_auto_schema(
        tags=['Suppliers'],
        operation_description="Retrieve a list of all suppliers.",
        responses={
            200: SupplierReadSerializer(many=True),
            401: openapi.Response(
                description="Unauthorized access.",
                examples={"application/json": {"detail": "Authentication credentials were not provided."}}
            )
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve a list of suppliers.
        """
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Suppliers'],
        operation_description="Create a new supplier.",
        request_body=SupplierWriteSerializer,
        responses={
            201: SupplierReadSerializer,
            400: openapi.Response(
                description="Invalid input.",
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
        Create a new supplier.
        """
        return super().post(request, *args, **kwargs)


class SupplierDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a supplier by its primary key.
    """
    permission_classes = [IsAuthenticated]
    queryset = Supplier.objects.all()
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return SupplierWriteSerializer
        return SupplierReadSerializer
    
    def perform_destroy(self, instance):
        # Perform a hard delete
        user = self.request.user if self.request.user.is_authenticated else None
        action.send(user or instance, verb='deleted a supplier', target=instance)
        instance.delete()

    @swagger_auto_schema(
        tags=['Suppliers'],
        operation_description="Retrieve a supplier by its primary key.",
        responses={
            200: SupplierReadSerializer,
            404: openapi.Response(
                description="Supplier not found.",
                examples={"application/json": {"detail": "Not found."}}
            ),
            401: openapi.Response(
                description="Unauthorized access.",
                examples={"application/json": {"detail": "Authentication credentials were not provided."}}
            )
        },
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="Primary key of the supplier", type=openapi.TYPE_INTEGER)
        ]
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve a supplier by its primary key.
        """
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Suppliers'],
        operation_description="Update a supplier by its primary key.",
        request_body=SupplierWriteSerializer,
        responses={
            200: SupplierReadSerializer,
            400: openapi.Response(
                description="Invalid input.",
                examples={"application/json": {"detail": "Validation error details."}}
            ),
            404: openapi.Response(
                description="Supplier not found.",
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
        Update a supplier by its primary key.
        """
        kwargs['partial'] = True  # Enable partial updates
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Suppliers'],
        operation_description="Delete a supplier by its primary key.",
        responses={
            204: openapi.Response(description="Supplier deleted successfully."),
            404: openapi.Response(
                description="Supplier not found.",
                examples={"application/json": {"detail": "Not found."}}
            ),
            401: openapi.Response(
                description="Unauthorized access.",
                examples={"application/json": {"detail": "Authentication credentials were not provided."}}
            )
        },
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="Primary key of the supplier", type=openapi.TYPE_INTEGER)
        ]
    )
    def delete(self, request, *args, **kwargs):
        """
        Delete a supplier by its primary key.
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


class EquipmentList(generics.ListCreateAPIView):
    """
    List all equipment or create a new equipment entry.
    """
    permission_classes = [IsAuthenticated]
    queryset = Equipment.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EquipmentWriteSerializer
        return EquipmentReadSerializer

    @swagger_auto_schema(
        tags=['Equipment'],
        operation_description="Retrieve a list of all equipment.",
        responses={
            200: EquipmentReadSerializer(many=True),
            401: openapi.Response(
                description="Unauthorized access.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
                examples={"application/json": {"detail": "Authentication credentials were not provided."}}
            )
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve a list of all equipment.
        """
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Equipment'],
        operation_description="Create a new equipment entry.",
        request_body=EquipmentWriteSerializer,
        responses={
            201: openapi.Response(
                description="Equipment successfully created.",
                schema=EquipmentWriteSerializer,
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
                examples={"application/json": {"detail": "Authentication credentials were not provided."}}
            ),
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Create a new equipment entry.
        """
        return super().post(request, *args, **kwargs)



class EquipmentDetail(RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete equipment.
    """
    permission_classes = [IsAuthenticated]
    queryset = Equipment.objects.all()  
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return EquipmentReadSerializer
        return EquipmentWriteSerializer

    def perform_destroy(self, instance):
        user = self.request.user if self.request.user.is_authenticated else None
        # Log deletion and perform hard delete
        action.send(user or instance, verb='deleted equipment', target=instance)
        instance.delete()

    @swagger_auto_schema(
        tags=['Equipment'],
        operation_description="Retrieve equipment by its primary key.",
        responses={
            200: openapi.Response(
                description="Equipment retrieved successfully.",
                schema=EquipmentReadSerializer,
            ),
            404: openapi.Response(
                description="Equipment not found.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
                examples={"application/json": {"detail": "Not found."}}
            ),
        },
        manual_parameters=[
            openapi.Parameter(
                'pk', openapi.IN_PATH,
                description="Primary key of the equipment",
                type=openapi.TYPE_INTEGER, required=True
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve equipment by its primary key.
        """
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Equipment'],
        operation_description="Update equipment by its primary key.",
        request_body=EquipmentWriteSerializer,
        responses={
            200: openapi.Response(
                description="Equipment updated successfully.",
                schema=EquipmentWriteSerializer,
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
                description="Equipment not found.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"detail": openapi.Schema(type=openapi.TYPE_STRING)}
                ),
                examples={"application/json": {"detail": "Not found."}}
            )
        },
        manual_parameters=[
            openapi.Parameter(
                'pk', openapi.IN_PATH,
                description="Primary key of the equipment",
                type=openapi.TYPE_INTEGER, required=True
            )
        ]
    )
    def put(self, request, *args, **kwargs):
        """
        Update equipment by its primary key.
        """
        kwargs['partial'] = True  # Enable partial updates
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Equipment'],
        operation_description="Partially update equipment by its primary key.",
        request_body=EquipmentWriteSerializer(partial=True),
        responses={
            200: openapi.Response(
                description="Equipment partially updated successfully.",
                schema=EquipmentWriteSerializer,
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
                description="Equipment not found.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"detail": openapi.Schema(type=openapi.TYPE_STRING)}
                ),
                examples={"application/json": {"detail": "Not found."}}
            )
        },
        manual_parameters=[
            openapi.Parameter(
                'pk', openapi.IN_PATH,
                description="Primary key of the equipment",
                type=openapi.TYPE_INTEGER, required=True
            )
        ]
    )
    def patch(self, request, *args, **kwargs):
        """
        Partially update equipment by its primary key.
        """
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Equipment'],
        operation_description="Delete equipment by its primary key.",
        responses={
            204: openapi.Response(description="Equipment deleted successfully."),
            404: openapi.Response(
                description="Equipment not found.",
                examples={"application/json": {"detail": "Not found."}}
            ),
            401: openapi.Response(
                description="Unauthorized access.",
                examples={"application/json": {"detail": "Authentication credentials were not provided."}}
            )
        },
        manual_parameters=[
            openapi.Parameter(
                'pk', openapi.IN_PATH,
                description="Primary key of the equipment",
                type=openapi.TYPE_INTEGER, required=True
            )
        ]
    )
    def delete(self, request, *args, **kwargs):
        """
        Delete equipment by its primary key.
        """
        self.perform_destroy(self.get_object())
        return Response({"detail": "Equipment deleted successfully."}, status=status.HTTP_204_NO_CONTENT)



class TotalEquipmentView(APIView):
    """
    View to return the total number of equipment in the system.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Equipment'],
        operation_description="Get the total number of equipment currently registered in the system.",
        responses={
            200: openapi.Response(
                description="Total number of equipment successfully retrieved.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total_equipment': openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="Total count of equipment"
                        )
                    }
                )
            )
        }
    )
    def get(self, request, format=None):
        total_equipment = Equipment.objects.count()
        return Response({'total_equipment': total_equipment})


class TotalEquipmentUnderMaintenanceView(APIView):
    """
    View to return the total number of equipment currently under maintenance.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Equipment'],
        operation_description="Get the total number of equipment currently under maintenance.",
        responses={
            200: openapi.Response(
                description="Total number of equipment under maintenance successfully retrieved.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'equipment_under_maintenance': openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="Total count of equipment under maintenance"
                        )
                    }
                )
            )
        }
    )
    def get(self, request, format=None):
        equipment_under_maintenance_count = Equipment.objects.filter(
            operational_status=Equipment.OPERATIONAL_STATUS.under_maintenance,
            is_removed=False
        ).count()
        return Response({'equipment_under_maintenance': equipment_under_maintenance_count})



    



class MaintenanceActivitiesByEquipmentView(generics.ListCreateAPIView):
    """
    List all activities for a specific equipment or create a new activity.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['technician', 'activity_type']

    def get_queryset(self):
        equipment_id = self.kwargs.get('equipment_id')
        queryset = (
            EquipmentMaintenanceActivity.objects
            .filter(equipment_id=equipment_id)
            .select_related('equipment', 'technician')
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
            return EquipmentMaintenanceActivityWriteSerializer
        return EquipmentMaintenanceActivityReadSerializer

    def perform_create(self, serializer):
        equipment_id = self.kwargs.get('equipment_id')
        equipment = get_object_or_404(Equipment, id=equipment_id)
        serializer.save(equipment=equipment)

    @swagger_auto_schema(
        tags=['Equipment Activities'],
        operation_description="Retrieve all activities for a specific equipment with optional filtering.",
        manual_parameters=[
            openapi.Parameter(
                'equipment_id', openapi.IN_PATH,
                description="ID of the equipment",
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
                description="Filter by activity type (preventive maintenance, repair, calibration)",
                type=openapi.TYPE_STRING,
                enum=['preventive maintenance', 'repair', 'calibration'],
                required=False
            ),
        ],
        responses={
            200: EquipmentMaintenanceActivityReadSerializer(many=True),
            401: openapi.Response(
                description="Unauthorized access.",
                examples={"application/json": {"detail": "Authentication credentials were not provided."}}
            )
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve all activities for a specific equipment with optional filtering.
        """
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Equipment Activities'],
        operation_description="Create a new activity for a specific equipment.",
        request_body=EquipmentMaintenanceActivityWriteSerializer,
        responses={
            201: EquipmentMaintenanceActivityReadSerializer,
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
        Create a new activity for a specific equipment.
        """
        return super().post(request, *args, **kwargs)



class MaintenanceActivitiesDetailByEquipmentView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete an activity for a specific equipment.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        equipment_id = self.kwargs.get('equipment_id')
        return EquipmentMaintenanceActivity.objects.filter(equipment_id=equipment_id)

    def get_object(self):
        queryset = self.get_queryset()
        activity_id = self.kwargs.get('activity_id')
        obj = get_object_or_404(queryset, id=activity_id)
        return obj

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return EquipmentMaintenanceActivityReadSerializer
        else:
            return EquipmentMaintenanceActivityWriteSerializer

    def put(self, request, *args, **kwargs):
        """
        Update an activity for a specific equipment. Supports partial updates.
        """
        kwargs['partial'] = True  # Allow partial updates
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Equipment Activities'],
        operation_description="Retrieve an activity for a specific equipment.",
        manual_parameters=[
            openapi.Parameter(
                'equipment_id', openapi.IN_PATH,
                description="ID of the equipment",
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
            200: openapi.Response(
                description="Activity retrieved successfully.",
                schema=EquipmentMaintenanceActivityReadSerializer,
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
    def get(self, request, *args, **kwargs):
        """
        Retrieve an activity for a specific equipment.
        """
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Equipment Activities'],
        operation_description="Update an activity for a specific equipment. Supports partial updates.",
        request_body=EquipmentMaintenanceActivityWriteSerializer,
        responses={
            200: openapi.Response(
                description="Activity updated successfully.",
                schema=EquipmentMaintenanceActivityReadSerializer,
            ),
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
        Update an activity for a specific equipment. Supports partial updates.
        """
        kwargs['partial'] = True
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Equipment Activities'],
        operation_description="Delete an activity for a specific equipment.",
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
        Delete an activity for a specific equipment.
        """
        return super().delete(request, *args, **kwargs)




class MaintenanceActivitiesListCreateView(generics.ListCreateAPIView):
    """
    List all equipment activities or create a new activity.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        include_deleted = self.request.query_params.get('include_deleted', 'false').lower()
        if include_deleted == 'true':
            queryset = EquipmentMaintenanceActivity.all_objects.all()
        else:
            queryset = EquipmentMaintenanceActivity.objects.all()
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EquipmentMaintenanceActivityWriteSerializer
        return EquipmentMaintenanceActivityReadSerializer

    @swagger_auto_schema(
        tags=['Equipment Activities'],
        operation_description="Retrieve a list of all equipment activities.",
        manual_parameters=[
            openapi.Parameter(
                'include_deleted', openapi.IN_QUERY,
                description="Include soft-deleted activities (true/false). Default is false.",
                type=openapi.TYPE_BOOLEAN,
                required=False
            ),
        ],
        responses={
            200: EquipmentMaintenanceActivityReadSerializer(many=True),
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
        Retrieve a list of all equipment activities.
        """
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Equipment Activities'],
        operation_description="Create a new equipment activity.",
        request_body=EquipmentMaintenanceActivityWriteSerializer,
        responses={
            201: EquipmentMaintenanceActivityReadSerializer,
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
        Create a new equipment activity.
        """
        return super().post(request, *args, **kwargs)



class MaintenanceActivitiesDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete an equipment activity.
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
            queryset = EquipmentMaintenanceActivity.all_objects.all()
        else:
            queryset = EquipmentMaintenanceActivity.objects.all()
        return queryset

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return EquipmentMaintenanceActivityWriteSerializer
        return EquipmentMaintenanceActivityReadSerializer

    @swagger_auto_schema(
        tags=['Equipment Activities'],
        operation_description="Retrieve an equipment activity by its primary key.",
        manual_parameters=[
            openapi.Parameter(
                'include_deleted', openapi.IN_QUERY,
                description="Include soft-deleted activity (true/false). Default is false.",
                type=openapi.TYPE_BOOLEAN,
                required=False
            ),
            openapi.Parameter(
                'pk', openapi.IN_PATH,
                description="Primary key of the equipment activity",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Equipment activity retrieved successfully.",
                schema=EquipmentMaintenanceActivityReadSerializer
            ),
            404: openapi.Response(
                description="Equipment activity not found.",
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
        Retrieve an equipment activity by its primary key.
        """
        return super().get(request, *args, **kwargs)




class MaintenanceScheduleListCreateView(generics.ListCreateAPIView):
    """
    List all maintenance schedules or create a new one.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['frequency', 'is_active']
    search_fields = ['title', 'description', 'equipment__name']  
    ordering_fields = ['start_date', 'end_date']  # Updated ordering fields

    def get_queryset(self):
        """
        Return maintenance schedules accessible to the user.
        """
        user = self.request.user
        if IsAdminOrSuperAdmin().has_permission(self.request, self):
            return MaintenanceSchedule.objects.all()
        else:
            return MaintenanceSchedule.objects.filter(Q(technician=user) | Q(for_all_equipment=True))

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
            return MaintenanceSchedule.objects.filter(Q(technician=user) | Q(for_all_equipment=True))

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
    # Record that the schedule was deactivated
    action.send(
        request.user,
        verb='deactivated maintenance schedule',
        target=schedule
    )
    return Response({'detail': 'Schedule deactivated.'}, status=status.HTTP_200_OK)






