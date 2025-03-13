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
    Equipment, Supplier, EquipmentMaintenanceActivity,
    MaintenanceSchedule
    )
from .serializers import(
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
from django.db.models import Q, Count, functions
from rest_framework.exceptions import PermissionDenied, ValidationError

import logging
from django.utils import timezone
import datetime
import calendar
from collections import defaultdict

logger = logging.getLogger(__name__)









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
        # For GET and PUT, we use appropriate serializers.
        if self.request.method == 'GET':
            return SupplierReadSerializer
        # For both PUT (full update) and PATCH (partial update) we use the write serializer.
        return SupplierWriteSerializer

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
        """Retrieve a supplier by its primary key."""
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Suppliers'],
        operation_description="Perform a full update on a supplier by its primary key.",
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
        """Full update of a supplier record and also support partial updates"""
        kwargs['partial'] = True  # Enable partial updates
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Suppliers'],
        operation_description="Perform a partial update on a supplier by its primary key.",
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
    def patch(self, request, *args, **kwargs):
        """Partial update of a supplier record."""
        kwargs['partial'] = True  # Enable partial updates
        return super().patch(request, *args, **kwargs)

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
        """Delete a supplier record by its primary key."""
        return super().delete(request, *args, **kwargs)







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


class EquipmentStatusSummaryView(APIView):
    """
    Retrieve aggregated counts of equipment by operational status.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Equipment'],
        operation_description="Retrieve aggregated counts of equipment by operational status.",
        responses={
            200: openapi.Response(
                description="Equipment status summary retrieved successfully.",
                # The response is an object where each key is a status
                # and the value is an integer count.
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    additional_properties=openapi.Schema(
                        type=openapi.TYPE_INTEGER
                    )
                ),
                examples={
                    "application/json": {
                        "functional": 120,
                        "non_functional": 30,
                        "under_maintenance": 15,
                        "decommissioned": 5
                    }
                }
            ),
            401: openapi.Response(
                description="Unauthorized access.",
                examples={"application/json": {"detail": "Authentication credentials were not provided."}}
            )
        }
    )
    def get(self, request, *args, **kwargs):
        summary_qs = (
            Equipment.objects
            .values('operational_status')
            .annotate(total=Count('id'))
        )
        
        # Convert the QuerySet into a dict keyed by operational_status
        summary = {}
        total_equipment = 0
        for item in summary_qs:
            status = item['operational_status']
            count = item['total']
            summary[status] = count
            total_equipment += count

        # Optionally add the total to the response
        summary['total_equipment'] = total_equipment

        return Response(summary)





class EquipmentTypeSummaryView(APIView):
    """
    Retrieve aggregated counts of equipment by device type.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Equipment'],
        operation_description="Retrieve aggregated counts of equipment by device type.",
        responses={
            200: openapi.Response(
                description="Device type summary retrieved successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    additional_properties=openapi.Schema(type=openapi.TYPE_INTEGER)
                ),
                examples={
                    "application/json": {
                        "diagnostic": 10,
                        "therapeutic": 7,
                        "life_support": 5,
                        "lab": 12,
                        "monitoring": 4,
                        "hospital_industrial": 3,
                        "safety_equipment": 2,
                        "other": 9
                    }
                }
            ),
            401: openapi.Response(
                description="Unauthorized access.",
                examples={"application/json": {"detail": "Authentication credentials were not provided."}}
            )
        }
    )
    def get(self, request, *args, **kwargs):
        # Aggregate by device_type and count the number of equipment in each category
        summary_qs = (
            Equipment.objects
            .values('device_type') 
            .annotate(total=Count('id'))
        )
        
        # Convert the QuerySet into a dictionary keyed by device_type
        summary = {item['device_type']: item['total'] for item in summary_qs}

        return Response(summary)
    
    
    
class  MaintenanceActivityOverviewView(APIView):
    """
    Returns daily counts of maintenance reports (Preventive Maintenance, Repair, Calibration)
    within a specified date range.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Maintenance Reports'],
        operation_description=(
            "Retrieve daily counts of maintenance reports within a specified period. "
            "The query parameter 'period' accepts the following values: "
            "7 (for last 7 days), 30 (for last 30 days), or '3month' (for last 3 months). "
            "If not provided or invalid, defaults to 30 days."
        ),
        manual_parameters=[
            openapi.Parameter(
                'period',
                openapi.IN_QUERY,
                description="Period for which to retrieve data. Valid values: 7, 30, or '3month'.",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={
            200: openapi.Response(
                description="A list of daily report counts for each type of maintenance report.",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                            'preventive_maintenance': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'repair': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'calibration': openapi.Schema(type=openapi.TYPE_INTEGER),
                        }
                    )
                ),
                examples={
                    "application/json": [
                        {
                            "date": "2025-06-09",
                            "preventive_maintenance": 5,
                            "repair": 3,
                            "calibration": 2
                        },
                        {
                            "date": "2025-06-10",
                            "preventive_maintenance": 1,
                            "repair": 0,
                            "calibration": 0
                        }
                    ]
                }
            ),
            401: openapi.Response(
                description="Unauthorized access.",
                examples={"application/json": {"detail": "Authentication credentials were not provided."}}
            ),
        }
    )
    def get(self, request, *args, **kwargs):
        # Determine the period in days. Default to 30 if not provided or invalid.
        period_param = request.query_params.get('period', '30').lower()

        # Accept 7, 30 or "3month" (or "3 months") as valid period values.
        if period_param in ['7', '30']:
            period = int(period_param)
        elif period_param in ['3month', '3 months']:
            period = 90  # Approximate 3 months as 90 days.
        else:
            period = 30  # Default to 30 days
            
        end_date = timezone.now()
        start_date = end_date - datetime.timedelta(days=period)

        # Filter the activities within the chosen date range
        queryset = EquipmentMaintenanceActivity.objects.filter(
            date_time__gte=start_date,
            date_time__lte=end_date
        )

        # Group by day and activity_type, and count
        grouped_qs = (
            queryset
            .annotate(day=functions.TruncDay('date_time'))
            .values('day', 'activity_type')
            .annotate(count=Count('id'))
            .order_by('day')
        )

        # Build a dictionary keyed by date, with sub-keys for each activity type
        data_by_day = defaultdict(lambda: {
            'preventive maintenance': 0,
            'repair': 0,
            'calibration': 0
        })

        for item in grouped_qs:
            day = item['day']
            activity_type = item['activity_type']
            data_by_day[day][activity_type] = item['count']

        #  Convert this dictionary into a list of objects sorted by date
        final_data = []
        for day in sorted(data_by_day.keys()):
            final_data.append({
                'date': day.strftime('%Y-%m-%d'),
                'preventive_maintenance': data_by_day[day]['preventive maintenance'],
                'repair': data_by_day[day]['repair'],
                'calibration': data_by_day[day]['calibration'],
            })

        return Response(final_data)



class MaintenanceActivitiesByEquipmentView(generics.ListCreateAPIView):
    """
    List all maintenance reports for a specific equipment or create a new report.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        equipment_id = self.kwargs.get('equipment_id')

        queryset = (
            EquipmentMaintenanceActivity.objects
            .filter(equipment_id=equipment_id)
            .select_related('equipment', 'technician')
        )

        # Filter by 'year' query parameter if provided
        year_str = self.request.query_params.get('year')
        if year_str:
            try:
                year = int(year_str)
                queryset = queryset.filter(date_time__year=year)
            except ValueError:
                pass  # or raise a validation error if you prefer

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
        tags=['Maintenance Reports'],
        operation_description="Retrieve all maintenance reports for a specific equipment with optional filtering by year (e.g., ?year=2024).",
        manual_parameters=[
            openapi.Parameter(
                'equipment_id', openapi.IN_PATH,
                description="ID of the equipment",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'year', openapi.IN_QUERY,
                description="Filter by year (e.g., 2024)",
                type=openapi.TYPE_INTEGER,
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
        Retrieve all Maintenance reports for a specific equipment with optional filtering by year.
        """
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Maintenance Reports'],
        operation_description="Create a new maintenance report for a specific equipment.",
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
       Create a new maintenance report for this equipment (by DB primary key).
        """
        return super().post(request, *args, **kwargs)




class MaintenanceActivitiesListCreateView(generics.ListCreateAPIView):
    """
    List all maintenance reports or create a new report.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return EquipmentMaintenanceActivity.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EquipmentMaintenanceActivityWriteSerializer
        return EquipmentMaintenanceActivityReadSerializer

    @swagger_auto_schema(
        tags=['Maintenance Reports'],
        operation_description="Retrieve a list of all maintenance reports.",
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
        Retrieve a list of all maintenance reports.
        """
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Maintenance Reports'],
        operation_description="Create a new  maintenance report.",
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
        Create a new  maintenance report.
        """
        return super().post(request, *args, **kwargs)



class MaintenanceActivitiesDetailView(generics.RetrieveAPIView):
    """
    Retrieve a maintenance report.
    """
    lookup_field = 'pk'

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return EquipmentMaintenanceActivity.objects.all()

    def get_serializer_class(self):
        return EquipmentMaintenanceActivityReadSerializer

    @swagger_auto_schema(
        tags=['Maintenance Reports'],
        operation_description="Retrieve an maintenance report by its primary key.",
        manual_parameters=[
            openapi.Parameter(
                'pk', openapi.IN_PATH,
                description="Primary key of the maintenance report",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Maintenance report retrieved successfully.",
                schema=EquipmentMaintenanceActivityReadSerializer
            ),
            404: openapi.Response(
                description="Maintenance report not found.",
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
        Retrieve an maintenance report by its primary key.
        """
        return super().get(request, *args, **kwargs)



class UpcomingMaintenanceScheduleView(APIView):
    """
    Lists all maintenance occurrences (including recurring ones)
    that fall within the current calendar month.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List all upcoming maintenance events for the current month (including recurring).",
        tags=['Maintenance Schedules'],
        responses={
            200: openapi.Response(
                description="A list of upcoming maintenance events within the current month.",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "title": openapi.Schema(type=openapi.TYPE_STRING),
                            "activity_type": openapi.Schema(type=openapi.TYPE_STRING),
                            "equipment": openapi.Schema(type=openapi.TYPE_STRING),
                            "date": openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                        }
                    )
                ),
                examples={
                    "application/json": [
                        {
                            "title": "Bolt Tightening Tonometer",
                            "activity_type": "repair",
                            "equipment": "Endoscope",
                            "date": "2024-01-15"
                        },
                        {
                            "title": "System Servicing",
                            "activity_type": "preventive maintenance",
                            "equipment": "All Equipment",
                            "date": "2024-01-20"
                        }
                    ]
                }
            ),
            401: openapi.Response(
                description="Unauthorized access.",
                examples={"application/json": {"detail": "Authentication credentials were not provided."}}
            ),
        }
    )
    def get(self, request, *args, **kwargs):
        # 1. Determine start_of_month and end_of_month
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate last day of the current month
        _, last_day = calendar.monthrange(now.year, now.month)
        end_of_month = start_of_month.replace(
            day=last_day,
            hour=23,
            minute=59,
            second=59,
            microsecond=999999
        )

        # 2. Retrieve all maintenance schedules
        schedules = MaintenanceSchedule.objects.all()

        # 3. Collect all occurrences in the current month
        events = []
        for schedule in schedules:
            occurrences = schedule.get_occurrences_in_range(start_of_month, end_of_month)
            
            # Determine how to label equipment
            if schedule.for_all_equipment:
                equipment_label = "All Equipment"
            else:
                # Single piece of equipment (ForeignKey)
                if schedule.equipment:
                    equipment_label = schedule.equipment.name
                else:
                    equipment_label = "No equipment linked"
            
            for occ in occurrences:
                events.append({
                    "title": schedule.title,
                    "activity_type": schedule.activity_type,
                    "equipment": equipment_label,
                    "date": occ.strftime('%Y-%m-%d'),  # or ISO 8601: occ.isoformat()
                })

        # 4. Sort the events by date
        events.sort(key=lambda e: e["date"])

        # 5. Return as JSON
        return Response(events)

class MaintenanceScheduleListCreateView(generics.ListCreateAPIView):
    """
    List all maintenance schedules or create a new one.
    """
    permission_classes = [IsAuthenticated]
    # filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    # filterset_fields = ['frequency', 'is_active']
    # search_fields = ['title', 'description', 'equipment__name']  
    # ordering_fields = ['start_date', 'end_date']  # Updated ordering fields

    def get_queryset(self):
        """
        Return maintenance schedules accessible to the user.
        """
        # If this is a swagger fake view or the user isn't authenticated, return an empty queryset.
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return MaintenanceSchedule.objects.none()

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
        # If this is a swagger fake view or the user isn't authenticated, return an empty queryset.
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return MaintenanceSchedule.objects.none()

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
    if not request.user.is_authenticated:
        return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)
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






# class MaintenanceActivitiesDetailByEquipmentView(generics.RetrieveUpdateDestroyAPIView):
#     """
#     Retrieve, update, or delete an activity for a specific equipment.
#     """
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         equipment_id = self.kwargs.get('equipment_id')
#         return EquipmentMaintenanceActivity.objects.filter(equipment_id=equipment_id)

#     def get_object(self):
#         queryset = self.get_queryset()
#         activity_id = self.kwargs.get('activity_id')
#         obj = get_object_or_404(queryset, id=activity_id)
#         return obj

#     def get_serializer_class(self):
#         if self.request.method == 'GET':
#             return EquipmentMaintenanceActivityReadSerializer
#         else:
#             return EquipmentMaintenanceActivityWriteSerializer

#     def put(self, request, *args, **kwargs):
#         """
#         Update an activity for a specific equipment. Supports partial updates.
#         """
#         kwargs['partial'] = True  # Allow partial updates
#         return super().put(request, *args, **kwargs)

#     @swagger_auto_schema(
#         tags=['Equipment Activities'],
#         operation_description="Retrieve an activity for a specific equipment.",
#         manual_parameters=[
#             openapi.Parameter(
#                 'equipment_id', openapi.IN_PATH,
#                 description="ID of the equipment",
#                 type=openapi.TYPE_INTEGER,
#                 required=True
#             ),
#             openapi.Parameter(
#                 'activity_id', openapi.IN_PATH,
#                 description="ID of the activity",
#                 type=openapi.TYPE_INTEGER,
#                 required=True
#             ),
#         ],
#         responses={
#             200: openapi.Response(
#                 description="Activity retrieved successfully.",
#                 schema=EquipmentMaintenanceActivityReadSerializer,
#             ),
#             404: openapi.Response(
#                 description="Activity not found.",
#                 examples={"application/json": {"detail": "Not found."}}
#             ),
#             401: openapi.Response(
#                 description="Unauthorized access.",
#                 examples={"application/json": {"detail": "Authentication credentials were not provided."}}
#             )
#         }
#     )
#     def get(self, request, *args, **kwargs):
#         """
#         Retrieve an activity for a specific equipment.
#         """
#         return super().get(request, *args, **kwargs)

#     @swagger_auto_schema(
#         tags=['Equipment Activities'],
#         operation_description="Update an activity for a specific equipment. Supports partial updates.",
#         request_body=EquipmentMaintenanceActivityWriteSerializer,
#         responses={
#             200: openapi.Response(
#                 description="Activity updated successfully.",
#                 schema=EquipmentMaintenanceActivityReadSerializer,
#             ),
#             400: openapi.Response(
#                 description="Invalid data provided.",
#                 examples={"application/json": {"detail": "Validation error details."}}
#             ),
#             404: openapi.Response(
#                 description="Activity not found.",
#                 examples={"application/json": {"detail": "Not found."}}
#             ),
#             401: openapi.Response(
#                 description="Unauthorized access.",
#                 examples={"application/json": {"detail": "Authentication credentials were not provided."}}
#             )
#         }
#     )
#     def put(self, request, *args, **kwargs):
#         """
#         Update an activity for a specific equipment. Supports partial updates.
#         """
#         kwargs['partial'] = True
#         return super().put(request, *args, **kwargs)

#     @swagger_auto_schema(
#         tags=['Equipment Activities'],
#         operation_description="Delete an activity for a specific equipment.",
#         responses={
#             204: openapi.Response(description="Activity deleted successfully."),
#             404: openapi.Response(
#                 description="Activity not found.",
#                 examples={"application/json": {"detail": "Not found."}}
#             ),
#             401: openapi.Response(
#                 description="Unauthorized access.",
#                 examples={"application/json": {"detail": "Authentication credentials were not provided."}}
#             )
#         }
#     )
#     def delete(self, request, *args, **kwargs):
#         """
#         Delete an activity for a specific equipment.
#         """
#         return super().delete(request, *args, **kwargs)
