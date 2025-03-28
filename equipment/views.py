from rest_framework import generics, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import api_view, permission_classes

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
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, OpenApiParameter


from accounts.permissions import IsAdminOrSuperAdmin
from django.db.models import Q, Count, functions
from django.db.models.functions import ExtractMonth
from rest_framework.exceptions import PermissionDenied, ValidationError

import logging
from django.utils import timezone
import datetime
import calendar
from collections import defaultdict

logger = logging.getLogger(__name__)




@extend_schema(
    summary="List Suppliers",
    description="Retrieve a list of all suppliers.",
    responses={
        200: OpenApiResponse(
            description="List of suppliers retrieved successfully.",
            examples=[
                OpenApiExample(
                    "Suppliers List",
                    value=[
                        {
                            "id": 1,
                            "company_name": "Example Supplier",
                            "company_email": "supplier@example.com",
                            "contact": "123456789",
                            "website": "https://example.com",
                            "created": "2023-01-01T12:00:00Z",
                            "modified": "2023-01-01T12:00:00Z"
                        }
                    ],
                    response_only=True,
                )
            ]
        ),
        401: OpenApiResponse(
            description="Unauthorized access.",
            examples=[
                OpenApiExample(
                    "Unauthorized",
                    value={"detail": "Authentication credentials were not provided."},
                    response_only=True,
                )
            ]
        )
    },
    tags=["Suppliers"]
)
class SupplierListCreateView(generics.ListCreateAPIView):
    """
    List all suppliers or create a new supplier.
    """
    permission_classes = [IsAuthenticated]
    queryset = Supplier.objects.all()

    def get_serializer_class(self):
        method = getattr(self.request, 'method', None)
        if method == 'POST':
            return SupplierWriteSerializer
        return SupplierReadSerializer

    @extend_schema(
        summary="Retrieve Suppliers",
        description="Retrieve a list of all suppliers.",
        responses={
            200: OpenApiResponse(
                description="List of suppliers retrieved successfully.",
                examples=[
                    OpenApiExample(
                        "Suppliers List",
                        value=[
                            {
                                "id": 1,
                                "company_name": "Example Supplier",
                                "company_email": "supplier@example.com",
                                "contact": "123456789",
                                "website": "https://example.com",
                                "created": "2023-01-01T12:00:00Z",
                                "modified": "2023-01-01T12:00:00Z"
                            }
                        ],
                        response_only=True,
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Unauthorized access.",
                examples=[
                    OpenApiExample(
                        "Unauthorized",
                        value={"detail": "Authentication credentials were not provided."},
                        response_only=True,
                    )
                ]
            )
        },
        tags=["Suppliers"]
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve a list of suppliers.
        """
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Create Supplier",
        description="Create a new supplier.",
        request=SupplierWriteSerializer,
        responses={
            201: OpenApiResponse(
                description="Supplier created successfully.",
                examples=[
                    OpenApiExample(
                        "Created Supplier",
                        value={
                            "id": 1,
                            "company_name": "Example Supplier",
                            "company_email": "supplier@example.com",
                            "contact": "123456789",
                            "website": "https://example.com",
                            "created": "2023-01-01T12:00:00Z",
                            "modified": "2023-01-01T12:00:00Z"
                        },
                        response_only=True,
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Invalid input.",
                examples=[
                    OpenApiExample(
                        "Validation Error",
                        value={"detail": "Validation error details."},
                        response_only=True,
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Unauthorized access.",
                examples=[
                    OpenApiExample(
                        "Unauthorized",
                        value={"detail": "Authentication credentials were not provided."},
                        response_only=True,
                    )
                ]
            )
        },
        tags=["Suppliers"]
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
        method = getattr(self.request, 'method', None)
        if method == 'GET':
            return SupplierReadSerializer
        # For PUT and PATCH we use the write serializer.
        return SupplierWriteSerializer

    @extend_schema(
        summary="Retrieve Supplier",
        description="Retrieve a supplier by its primary key.",
        parameters=[
            OpenApiParameter(
                name="pk",
                location=OpenApiParameter.PATH,
                description="Primary key of the supplier",
                type=int
            )
        ],
        responses={
            200: SupplierReadSerializer,
            404: OpenApiResponse(
                description="Supplier not found.",
                examples=[OpenApiExample("Not Found", value={"detail": "Not found."}, response_only=True)]
            ),
            401: OpenApiResponse(
                description="Unauthorized access.",
                examples=[OpenApiExample("Unauthorized", value={"detail": "Authentication credentials were not provided."}, response_only=True)]
            )
        },
        tags=["Suppliers"]
    )
    def get(self, request, *args, **kwargs):
        """Retrieve a supplier by its primary key."""
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Full Update Supplier",
        description="Perform a full update on a supplier by its primary key.",
        request=SupplierWriteSerializer,
        responses={
            200: SupplierReadSerializer,
            400: OpenApiResponse(
                description="Invalid input.",
                examples=[OpenApiExample("Validation Error", value={"detail": "Validation error details."}, response_only=True)]
            ),
            404: OpenApiResponse(
                description="Supplier not found.",
                examples=[OpenApiExample("Not Found", value={"detail": "Not found."}, response_only=True)]
            ),
            401: OpenApiResponse(
                description="Unauthorized access.",
                examples=[OpenApiExample("Unauthorized", value={"detail": "Authentication credentials were not provided."}, response_only=True)]
            )
        },
        tags=["Suppliers"]
    )
    def put(self, request, *args, **kwargs):
        """
        Full update of a supplier record.
        Partial updates are enabled.
        """
        kwargs['partial'] = True  # Enable partial updates
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Partial Update Supplier",
        description="Perform a partial update on a supplier by its primary key.",
        request=SupplierWriteSerializer,
        responses={
            200: SupplierReadSerializer,
            400: OpenApiResponse(
                description="Invalid input.",
                examples=[OpenApiExample("Validation Error", value={"detail": "Validation error details."}, response_only=True)]
            ),
            404: OpenApiResponse(
                description="Supplier not found.",
                examples=[OpenApiExample("Not Found", value={"detail": "Not found."}, response_only=True)]
            ),
            401: OpenApiResponse(
                description="Unauthorized access.",
                examples=[OpenApiExample("Unauthorized", value={"detail": "Authentication credentials were not provided."}, response_only=True)]
            )
        },
        tags=["Suppliers"]
    )
    def patch(self, request, *args, **kwargs):
        """Partial update of a supplier record."""
        kwargs['partial'] = True  # Enable partial updates
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        summary="Delete Supplier",
        description="Delete a supplier by its primary key.",
        parameters=[
            OpenApiParameter(
                name="pk",
                location=OpenApiParameter.PATH,
                description="Primary key of the supplier",
                type=int
            )
        ],
        responses={
            204: OpenApiResponse(description="Supplier deleted successfully."),
            404: OpenApiResponse(
                description="Supplier not found.",
                examples=[OpenApiExample("Not Found", value={"detail": "Not found."}, response_only=True)]
            ),
            401: OpenApiResponse(
                description="Unauthorized access.",
                examples=[OpenApiExample("Unauthorized", value={"detail": "Authentication credentials were not provided."}, response_only=True)]
            )
        },
        tags=["Suppliers"]
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
        method = getattr(self.request, 'method', None)
        if method == 'POST':
            return EquipmentWriteSerializer
        return EquipmentReadSerializer

    @extend_schema(
        summary="List Equipment",
        description="Retrieve a list of all equipment.",
        responses={
            200: EquipmentReadSerializer(many=True),
            401: OpenApiResponse(
                description="Unauthorized access.",
                examples=[OpenApiExample(
                    "Unauthorized",
                    value={"detail": "Authentication credentials were not provided."},
                    response_only=True
                )]
            )
        },
        tags=["Equipment"]
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve a list of all equipment.
        """
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Create Equipment",
        description="Create a new equipment entry.",
        request=EquipmentWriteSerializer,
        responses={
            201: OpenApiResponse(
                description="Equipment successfully created.",
                examples=[OpenApiExample(
                    "Created Equipment",
                    value={"id": 1, "name": "Equipment Name", "equipment_id": "ABCDEF123456", "device_type": "diagnostic", "...": "..."},
                    response_only=True
                )]
            ),
            400: OpenApiResponse(
                description="Bad request - Invalid data submitted.",
                examples=[OpenApiExample(
                    "Validation Error",
                    value={"detail": "Validation error details."},
                    response_only=True
                )]
            ),
            401: OpenApiResponse(
                description="Unauthorized - User is not authenticated.",
                examples=[OpenApiExample(
                    "Unauthorized",
                    value={"detail": "Authentication credentials were not provided."},
                    response_only=True
                )]
            )
        },
        tags=["Equipment"]
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
        method = getattr(self.request, 'method', None)
        if method == 'GET':
            return EquipmentReadSerializer
        return EquipmentWriteSerializer

    def perform_destroy(self, instance):
        # Custom deletion logic can be added here if needed.
        instance.delete()

    @extend_schema(
        summary="Retrieve Equipment",
        description="Retrieve equipment by its primary key.",
        parameters=[
            OpenApiParameter(
                name="pk",
                location=OpenApiParameter.PATH,
                description="Primary key of the equipment",
                type=int,
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Maintenance report retrieved successfully.",
                response=EquipmentMaintenanceActivityReadSerializer
            ),
            404: OpenApiResponse(
                description="Equipment not found.",
                examples=[OpenApiExample(
                    "Not Found",
                    value={"detail": "Not found."},
                    response_only=True
                )]
            ),
        },
        tags=["Equipment"]
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve equipment by its primary key.
        """
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update Equipment",
        description="Update equipment by its primary key.",
        request=EquipmentWriteSerializer,
        parameters=[
            OpenApiParameter(
                name="pk",
                location=OpenApiParameter.PATH,
                description="Primary key of the equipment",
                type=int,
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Equipment updated successfully.",
                response=EquipmentWriteSerializer
            ),
            400: OpenApiResponse(
                description="Invalid data provided.",
                examples=[OpenApiExample(
                    "Validation Error",
                    value={"detail": "Validation error details."},
                    response_only=True
                )]
            ),
            404: OpenApiResponse(
                description="Equipment not found.",
                examples=[OpenApiExample(
                    "Not Found",
                    value={"detail": "Not found."},
                    response_only=True
                )]
            ),
        },
        tags=["Equipment"]
    )
    def put(self, request, *args, **kwargs):
        """
        Update equipment by its primary key.
        Partial updates are enabled.
        """
        kwargs['partial'] = True  # Enable partial updates
        return self.update(request, *args, **kwargs)

    @extend_schema(
        summary="Partially Update Equipment",
        description="Partially update equipment by its primary key.",
        request=EquipmentWriteSerializer,
        parameters=[
            OpenApiParameter(
                name="pk",
                location=OpenApiParameter.PATH,
                description="Primary key of the equipment",
                type=int,
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Equipment partially updated successfully.",
                response=EquipmentWriteSerializer
            ),
            400: OpenApiResponse(
                description="Invalid data provided.",
                examples=[OpenApiExample(
                    "Validation Error",
                    value={"detail": "Validation error details."},
                    response_only=True
                )]
            ),
            404: OpenApiResponse(
                description="Equipment not found.",
                examples=[OpenApiExample(
                    "Not Found",
                    value={"detail": "Not found."},
                    response_only=True
                )]
            ),
        },
        tags=["Equipment"]
    )
    def patch(self, request, *args, **kwargs):
        """
        Partially update equipment by its primary key.
        """
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Delete Equipment",
        description="Delete equipment by its primary key.",
        parameters=[
            OpenApiParameter(
                name="pk",
                location=OpenApiParameter.PATH,
                description="Primary key of the equipment",
                type=int,
                required=True
            )
        ],
        responses={
            204: OpenApiResponse(description="Equipment deleted successfully."),
            404: OpenApiResponse(
                description="Equipment not found.",
                examples=[OpenApiExample(
                    "Not Found",
                    value={"detail": "Not found."},
                    response_only=True
                )]
            ),
            401: OpenApiResponse(
                description="Unauthorized access.",
                examples=[OpenApiExample(
                    "Unauthorized",
                    value={"detail": "Authentication credentials were not provided."},
                    response_only=True
                )]
            )
        },
        tags=["Equipment"]
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

    @extend_schema(
        summary="Get Total Equipment Count",
        description="Get the total number of equipment currently registered in the system.",
        responses={
            200: OpenApiResponse(
                description="Total number of equipment successfully retrieved.",
                response={
                    "type": "object",
                    "properties": {
                        "total_equipment": {
                            "type": "integer",
                            "description": "Total count of equipment"
                        }
                    }
                },
                examples=[
                    OpenApiExample(
                        "Total Equipment Example",
                        value={"total_equipment": 170},
                        response_only=True,
                    )
                ]
            )
        },
        tags=["Equipment"]
    )
    def get(self, request, format=None):
        total_equipment = Equipment.objects.count()
        return Response({'total_equipment': total_equipment})


class EquipmentStatusSummaryView(APIView):
    """
    Retrieve aggregated counts of equipment by operational status.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get Equipment Status Summary",
        description=(
            "Retrieve aggregated counts of equipment by operational status. "
            "The response is an object where each key is a status and the value is an integer count. "
            "Additionally, the total equipment count is provided under the 'total_equipment' key."
        ),
        responses={
            200: OpenApiResponse(
                description="Equipment status summary retrieved successfully.",
                response={
                    "type": "object",
                    "additionalProperties": {"type": "integer"},
                    "properties": {
                        "total_equipment": {
                            "type": "integer",
                            "description": "Total count of equipment"
                        }
                    }
                },
                examples=[
                    OpenApiExample(
                        "Equipment Status Summary Example",
                        value={
                            "functional": 120,
                            "non_functional": 30,
                            "under_maintenance": 15,
                            "decommissioned": 5,
                            "total_equipment": 170
                        },
                        response_only=True
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Unauthorized access.",
                examples=[
                    OpenApiExample(
                        "Unauthorized",
                        value={"detail": "Authentication credentials were not provided."},
                        response_only=True
                    )
                ]
            )
        },
        tags=["Equipment"]
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

    @extend_schema(
        summary="Get Equipment Type Summary",
        description="Retrieve aggregated counts of equipment by device type.",
        responses={
            200: OpenApiResponse(
                description="Device type summary retrieved successfully.",
                response={
                    "type": "object",
                    "additionalProperties": {"type": "integer"}
                },
                examples=[
                    OpenApiExample(
                        "Device Type Summary Example",
                        value={
                            "diagnostic": 10,
                            "therapeutic": 7,
                            "life_support": 5,
                            "lab": 12,
                            "monitoring": 4,
                            "hospital_industrial": 3,
                            "safety_equipment": 2,
                            "other": 9
                        },
                        response_only=True,
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Unauthorized access.",
                examples=[
                    OpenApiExample(
                        "Unauthorized",
                        value={"detail": "Authentication credentials were not provided."},
                        response_only=True
                    )
                ]
            )
        },
        tags=["Equipment"]
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


class MaintenanceActivityOverviewView(APIView):
    """
    Returns daily counts of maintenance reports (Preventive Maintenance, Repair, Calibration)
    within a specified date range.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get Daily Maintenance Report Counts",
        description=(
            "Retrieve daily counts of maintenance reports within a specified period. "
            "The query parameter 'period' accepts the following values: "
            "7 (for last 7 days), 30 (for last 30 days), or '3month' (for last 3 months). "
            "If not provided or invalid, defaults to 30 days."
        ),
        parameters=[
            OpenApiParameter(
                name="period",
                location=OpenApiParameter.QUERY,
                description="Period for which to retrieve data. Valid values: 7, 30, or '3month'.",
                type=str,
                required=False
            )
        ],
        responses={
            200: OpenApiResponse(
                description="A list of daily report counts for each type of maintenance report.",
                response={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "string", "format": "date"},
                            "preventive_maintenance": {"type": "integer"},
                            "repair": {"type": "integer"},
                            "calibration": {"type": "integer"}
                        }
                    }
                },
                examples=[
                    OpenApiExample(
                        "Maintenance Report Example",
                        value=[
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
                        ],
                        response_only=True
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Unauthorized access.",
                examples=[
                    OpenApiExample(
                        "Unauthorized",
                        value={"detail": "Authentication credentials were not provided."},
                        response_only=True
                    )
                ]
            )
        },
        tags=["Maintenance Reports"]
    )
    def get(self, request, *args, **kwargs):
        # Determine the period in days. Default to 30 if not provided or invalid.
        period_param = request.query_params.get('period', '30').lower()
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

        # Convert this dictionary into a list of objects sorted by date
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
                pass  # Optionally, you can raise a validation error here.
        return queryset

    def get_serializer_class(self):
        method = getattr(self.request, 'method', None)
        if method == 'POST':
            return EquipmentMaintenanceActivityWriteSerializer
        return EquipmentMaintenanceActivityReadSerializer

    def perform_create(self, serializer):
        equipment_id = self.kwargs.get('equipment_id')
        equipment = get_object_or_404(Equipment, id=equipment_id)
        serializer.save(equipment=equipment)

    @extend_schema(
        summary="List Maintenance Reports for Equipment",
        description=(
            "Retrieve all maintenance reports for a specific equipment with optional filtering by year. "
            "For example, appending '?year=2024' filters reports to those from 2024."
        ),
        parameters=[
            OpenApiParameter(
                name="equipment_id",
                location=OpenApiParameter.PATH,
                description="ID of the equipment",
                type=int,
                required=True
            ),
            OpenApiParameter(
                name="year",
                location=OpenApiParameter.QUERY,
                description="Filter by year (e.g., 2024)",
                type=int,
                required=False
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Maintenance reports retrieved successfully.",
                response=EquipmentMaintenanceActivityReadSerializer(many=True)
            ),
            401: OpenApiResponse(
                description="Unauthorized access.",
                examples=[OpenApiExample(
                    "Unauthorized",
                    value={"detail": "Authentication credentials were not provided."},
                    response_only=True
                )]
            )
        },
        tags=["Maintenance Reports"]
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve all maintenance reports for a specific equipment with optional filtering by year.
        """
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Create Maintenance Report for Equipment",
        description="Create a new maintenance report for a specific equipment.",
        request=EquipmentMaintenanceActivityWriteSerializer,
        responses={
            201: OpenApiResponse(
                description="Maintenance report created successfully.",
                response=EquipmentMaintenanceActivityReadSerializer
            ),
            400: OpenApiResponse(
                description="Invalid data provided.",
                examples=[OpenApiExample(
                    "Validation Error",
                    value={"detail": "Validation error details."},
                    response_only=True
                )]
            ),
            401: OpenApiResponse(
                description="Unauthorized access.",
                examples=[OpenApiExample(
                    "Unauthorized",
                    value={"detail": "Authentication credentials were not provided."},
                    response_only=True
                )]
            )
        },
        tags=["Maintenance Reports"]
    )
    def post(self, request, *args, **kwargs):
        """
        Create a new maintenance report for this equipment (by DB primary key).
        """
        return super().post(request, *args, **kwargs)


class MaintenanceActivitiesDetailByEquipmentView(generics.RetrieveAPIView):
    """
    Retrieve an activity for a specific equipment.
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
        method = getattr(self.request, 'method', None)
        if method == 'GET':
            return EquipmentMaintenanceActivityReadSerializer
        return EquipmentMaintenanceActivityWriteSerializer

    @extend_schema(
        summary="Retrieve Maintenance Activity",
        description="Retrieve an activity for a specific equipment.",
        parameters=[
            OpenApiParameter(
                name="equipment_id",
                location=OpenApiParameter.PATH,
                description="ID of the equipment",
                type=int,
                required=True
            ),
            OpenApiParameter(
                name="activity_id",
                location=OpenApiParameter.PATH,
                description="ID of the activity",
                type=int,
                required=True
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Activity retrieved successfully.",
                response=EquipmentMaintenanceActivityReadSerializer
            ),
            404: OpenApiResponse(
                description="Activity not found.",
                examples=[OpenApiExample(
                    "Not Found",
                    value={"detail": "Not found."},
                    response_only=True
                )]
            ),
            401: OpenApiResponse(
                description="Unauthorized access.",
                examples=[OpenApiExample(
                    "Unauthorized",
                    value={"detail": "Authentication credentials were not provided."},
                    response_only=True
                )]
            )
        },
        tags=["Equipment Activities"]
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve an activity for a specific equipment.
        """
        return super().get(request, *args, **kwargs)



class MaintenanceActivitiesListCreateView(generics.ListCreateAPIView):
    """
    List all maintenance reports or create a new report.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return EquipmentMaintenanceActivity.objects.all()

    def get_serializer_class(self):
        method = getattr(self.request, 'method', None)
        if method == 'POST':
            return EquipmentMaintenanceActivityWriteSerializer
        return EquipmentMaintenanceActivityReadSerializer

    @extend_schema(
        summary="List Maintenance Reports",
        description="Retrieve a list of all maintenance reports.",
        responses={
            200: OpenApiResponse(
                description="Maintenance reports retrieved successfully.",
                response=EquipmentMaintenanceActivityReadSerializer(many=True)
            ),
            401: OpenApiResponse(
                description="Unauthorized access.",
                examples=[OpenApiExample(
                    "Unauthorized",
                    value={"detail": "Authentication credentials were not provided."},
                    response_only=True
                )]
            )
        },
        tags=["Maintenance Reports"]
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve a list of all maintenance reports.
        """
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Create Maintenance Report",
        description="Create a new maintenance report.",
        request=EquipmentMaintenanceActivityWriteSerializer,
        responses={
            201: OpenApiResponse(
                description="Maintenance report created successfully.",
                response=EquipmentMaintenanceActivityReadSerializer
            ),
            400: OpenApiResponse(
                description="Invalid data provided.",
                examples=[OpenApiExample(
                    "Validation Error",
                    value={"detail": "Validation error details."},
                    response_only=True
                )]
            ),
            401: OpenApiResponse(
                description="Unauthorized access.",
                examples=[OpenApiExample(
                    "Unauthorized",
                    value={"detail": "Authentication credentials were not provided."},
                    response_only=True
                )]
            )
        },
        tags=["Maintenance Reports"]
    )
    def post(self, request, *args, **kwargs):
        """
        Create a new maintenance report.
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

    @extend_schema(
        summary="Retrieve Maintenance Report",
        description="Retrieve a maintenance report by its primary key.",
        parameters=[
            OpenApiParameter(
                name="pk",
                location=OpenApiParameter.PATH,
                description="Primary key of the maintenance report",
                type=int,
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Maintenance report retrieved successfully.",
                response=EquipmentMaintenanceActivityReadSerializer
            ),
            404: OpenApiResponse(
                description="Maintenance report not found.",
                examples=[OpenApiExample(
                    "Not Found",
                    value={"detail": "Not found."},
                    response_only=True
                )]
            ),
            401: OpenApiResponse(
                description="Unauthorized access.",
                examples=[OpenApiExample(
                    "Unauthorized",
                    value={"detail": "Authentication credentials were not provided."},
                    response_only=True
                )]
            )
        },
        tags=["Maintenance Reports"]
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve a maintenance report by its primary key.
        """
        return super().get(request, *args, **kwargs)



class EquipmentMaintenanceActivityYearlyOverviewView(APIView):
    """
    Returns monthly counts of maintenance activities for a single equipment (by ID)
    filtered by a specified year (defaults to current year if not provided).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get Yearly Maintenance Overview",
        description=(
            "Returns an array of 12 objects (one for each month) with the counts of: \n"
            "- Preventive Maintenance\n"
            "- Repair\n"
            "- Calibration\n"
            "for a given equipment in a given year. If the 'year' query parameter is omitted or invalid, "
            "the current year is used."
        ),
        parameters=[
            OpenApiParameter(
                name="equipment_id",
                location=OpenApiParameter.PATH,
                description="ID of the equipment",
                type=int,
                required=True
            ),
            OpenApiParameter(
                name="year",
                location=OpenApiParameter.QUERY,
                description="Year to filter by (e.g., 2024). Defaults to current year if omitted.",
                type=int,
                required=False
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Monthly activity counts for the specified equipment.",
                response={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "month": {"type": "integer", "description": "Month number (1-12)"},
                            "preventive_maintenance": {"type": "integer", "description": "Count of preventive maintenance reports"},
                            "repair": {"type": "integer", "description": "Count of repair reports"},
                            "calibration": {"type": "integer", "description": "Count of calibration reports"},
                        }
                    }
                },
                examples=[
                    OpenApiExample(
                        "Yearly Overview Example",
                        value=[
                            {"month": 1, "preventive_maintenance": 5, "repair": 2, "calibration": 1},
                            {"month": 2, "preventive_maintenance": 3, "repair": 1, "calibration": 0},
                            # ... objects for months 3-12
                        ],
                        response_only=True
                    )
                ]
            )
        },
        tags=["Maintenance Reports"]
    )
    def get(self, request, equipment_id):
        # 1. Validate that the equipment exists
        get_object_or_404(Equipment, id=equipment_id)

        # 2. Parse the 'year' query parameter or default to the current year
        year_str = request.query_params.get('year')
        if year_str is not None:
            try:
                year = int(year_str)
            except ValueError:
                year = timezone.now().year
        else:
            year = timezone.now().year

        # 3. Filter activities for this equipment and the given year
        queryset = EquipmentMaintenanceActivity.objects.filter(
            equipment_id=equipment_id, date_time__year=year
        )

        # 4. Group by month using ExtractMonth and activity_type, then count
        grouped_qs = (
            queryset
            .annotate(month=ExtractMonth('date_time'))
            .values('month', 'activity_type')
            .annotate(count=Count('id'))
            .order_by('month')
        )

        # 5. Initialize a structure to store monthly counts for each activity type
        data_by_month = defaultdict(lambda: {
            'preventive maintenance': 0,
            'repair': 0,
            'calibration': 0
        })

        # 6. Fill data_by_month with actual counts from the QuerySet
        for row in grouped_qs:
            m = row['month'] or 0
            atype = row['activity_type']
            data_by_month[m][atype] = row['count']

        # 7. Build final response: 12 objects, one for each month
        final_data = []
        for m in range(1, 13):
            final_data.append({
                'month': m,
                'preventive_maintenance': data_by_month[m]['preventive maintenance'],
                'repair': data_by_month[m]['repair'],
                'calibration': data_by_month[m]['calibration'],
            })

        return Response(final_data)


class UpcomingMaintenanceScheduleView(APIView):
    """
    Lists all maintenance occurrences (including recurring ones)
    that fall within the current calendar month.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Upcoming Maintenance Events",
        description=(
            "List all upcoming maintenance events for the current month (including recurring events). "
            "Each event includes the title, activity type, equipment label, and the scheduled date."
        ),
        responses={
            200: OpenApiResponse(
                description="A list of upcoming maintenance events within the current month.",
                response={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Title of the maintenance schedule"},
                            "activity_type": {"type": "string", "description": "Type of maintenance activity"},
                            "equipment": {"type": "string", "description": "Name of the equipment or 'All Equipment'"},
                            "date": {"type": "string", "format": "date", "description": "Date of the occurrence"}
                        }
                    }
                },
                examples=[
                    OpenApiExample(
                        "Upcoming Maintenance Example",
                        value=[
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
                        ],
                        response_only=True
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Unauthorized access.",
                examples=[
                    OpenApiExample(
                        "Unauthorized",
                        value={"detail": "Authentication credentials were not provided."},
                        response_only=True
                    )
                ]
            )
        },
        tags=["Maintenance Schedules"]
    )
    def get(self, request, *args, **kwargs):
        # 1. Determine the start and end of the current month.
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        _, last_day = calendar.monthrange(now.year, now.month)
        end_of_month = start_of_month.replace(
            day=last_day, hour=23, minute=59, second=59, microsecond=999999
        )

        # 2. Retrieve all maintenance schedules.
        schedules = MaintenanceSchedule.objects.all()

        # 3. Collect all occurrences within the current month.
        events = []
        for schedule in schedules:
            occurrences = schedule.get_occurrences_in_range(start_of_month, end_of_month)
            # Determine the equipment label.
            if schedule.for_all_equipment:
                equipment_label = "All Equipment"
            else:
                equipment_label = schedule.equipment.name if schedule.equipment else "No equipment linked"
            for occ in occurrences:
                events.append({
                    "title": schedule.title,
                    "activity_type": schedule.activity_type,
                    "equipment": equipment_label,
                    "date": occ.strftime('%Y-%m-%d'),
                })

        # 4. Sort the events by date.
        events.sort(key=lambda e: e["date"])

        return Response(events)

class MaintenanceScheduleListCreateView(generics.ListCreateAPIView):
    """
    List all maintenance schedules or create a new one.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return maintenance schedules accessible to the user.
        """
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return MaintenanceSchedule.objects.none()
        user = self.request.user
        if IsAdminOrSuperAdmin().has_permission(self.request, self):
            return MaintenanceSchedule.objects.all()
        else:
            return MaintenanceSchedule.objects.filter(Q(technician=user) | Q(for_all_equipment=True))

    def get_serializer_class(self):
        method = getattr(self.request, 'method', None)
        if method == 'POST':
            return MaintenanceScheduleWriteSerializer
        return MaintenanceScheduleReadSerializer

    @extend_schema(
        summary="List Maintenance Schedules",
        description="Retrieve a list of maintenance schedules accessible to the user.",
        responses={
            200: OpenApiResponse(
                description="Maintenance schedules retrieved successfully.",
               response=MaintenanceScheduleReadSerializer(many=True)
            ),
            401: OpenApiResponse(
                description="Unauthorized",
                examples=[OpenApiExample(
                    "Unauthorized",
                    value={"detail": "Authentication credentials were not provided."},
                    response_only=True
                )]
            )
        },
        tags=["Maintenance Schedules"]
    )
    def get(self, request, *args, **kwargs):
        """
        List all maintenance schedules.
        """
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Create Maintenance Schedule",
        description="Create a new maintenance schedule.",
        request=MaintenanceScheduleWriteSerializer,
        responses={
            201: OpenApiResponse(
                description="Maintenance schedule created successfully.",
                response=MaintenanceScheduleReadSerializer
            ),
            400: OpenApiResponse(
                description="Invalid input",
                examples=[OpenApiExample(
                    "Validation Error",
                    value={"detail": "Validation error details."},
                    response_only=True
                )]
            ),
            401: OpenApiResponse(
                description="Unauthorized",
                examples=[OpenApiExample(
                    "Unauthorized",
                    value={"detail": "Authentication credentials were not provided."},
                    response_only=True
                )]
            )
        },
        tags=["Maintenance Schedules"]
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
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return MaintenanceSchedule.objects.none()
        user = self.request.user
        if IsAdminOrSuperAdmin().has_permission(self.request, self):
            return MaintenanceSchedule.objects.all()
        else:
            return MaintenanceSchedule.objects.filter(Q(technician=user) | Q(for_all_equipment=True))

    def get_serializer_class(self):
        method = getattr(self.request, 'method', None)
        if method in ['PUT', 'PATCH']:
            return MaintenanceScheduleWriteSerializer
        return MaintenanceScheduleReadSerializer

    @extend_schema(
        summary="Retrieve Maintenance Schedule",
        description="Retrieve a maintenance schedule by its primary key.",
        parameters=[
            OpenApiParameter(
                name="pk",
                location=OpenApiParameter.PATH,
                description="ID of the maintenance schedule",
                type=int,
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Maintenance schedule retrieved successfully.",
                response=MaintenanceScheduleReadSerializer
            ),
            404: OpenApiResponse(
                description="Not found",
                examples=[OpenApiExample(
                    "Not Found",
                    value={"detail": "Not found."},
                    response_only=True
                )]
            ),
            401: OpenApiResponse(
                description="Unauthorized",
                examples=[OpenApiExample(
                    "Unauthorized",
                    value={"detail": "Authentication credentials were not provided."},
                    response_only=True
                )]
            )
        },
        tags=["Maintenance Schedules"]
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve a maintenance schedule.
        """
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update Maintenance Schedule",
        description="Update a maintenance schedule. Partial updates are allowed.",
        request=MaintenanceScheduleWriteSerializer,
        responses={
            200: OpenApiResponse(
                description="Maintenance schedule updated successfully.",
                response=MaintenanceScheduleReadSerializer
            ),
            400: OpenApiResponse(
                description="Invalid input",
                examples=[OpenApiExample(
                    "Validation Error",
                    value={"detail": "Validation error details."},
                    response_only=True
                )]
            ),
            404: OpenApiResponse(
                description="Not found",
                examples=[OpenApiExample(
                    "Not Found",
                    value={"detail": "Not found."},
                    response_only=True
                )]
            ),
            401: OpenApiResponse(
                description="Unauthorized",
                examples=[OpenApiExample(
                    "Unauthorized",
                    value={"detail": "Authentication credentials were not provided."},
                    response_only=True
                )]
            )
        },
        tags=["Maintenance Schedules"]
    )
    def put(self, request, *args, **kwargs):
        """
        Update a maintenance schedule.
        """
        kwargs['partial'] = True  # Allow partial updates
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Delete Maintenance Schedule",
        description="Delete a maintenance schedule by its primary key.",
        parameters=[
            OpenApiParameter(
                name="pk",
                location=OpenApiParameter.PATH,
                description="ID of the maintenance schedule",
                type=int,
                required=True
            )
        ],
        responses={
            204: OpenApiResponse(description="No content"),
            404: OpenApiResponse(
                description="Not found",
                examples=[OpenApiExample(
                    "Not Found",
                    value={"detail": "Not found."},
                    response_only=True
                )]
            ),
            401: OpenApiResponse(
                description="Unauthorized",
                examples=[OpenApiExample(
                    "Unauthorized",
                    value={"detail": "Authentication credentials were not provided."},
                    response_only=True
                )]
            )
        },
        tags=["Maintenance Schedules"]
    )
    def delete(self, request, *args, **kwargs):
        """
        Delete a maintenance schedule.
        """
        return super().delete(request, *args, **kwargs)


@extend_schema(
    methods=['POST'],
    summary="Deactivate Maintenance Schedule",
    description="Deactivate a maintenance schedule by setting is_active to False.",
    request=None,
    responses={
        200: OpenApiResponse(
            description="Schedule deactivated successfully.",
            examples=[OpenApiExample(
                "Deactivation Success",
                value={"detail": "Schedule deactivated."},
                response_only=True
            )]
        ),
        401: OpenApiResponse(
            description="Unauthorized",
            examples=[OpenApiExample(
                "Unauthorized",
                value={"detail": "Authentication credentials were not provided."},
                response_only=True
            )]
        ),
        403: OpenApiResponse(
            description="Forbidden",
            examples=[OpenApiExample(
                "Forbidden",
                value={"detail": "Not allowed."},
                response_only=True
            )]
        )
    },
    tags=["Maintenance Schedules"]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deactivate_schedule(request, pk):
    """
    Deactivate a maintenance schedule by setting is_active to False.
    """
    schedule = get_object_or_404(MaintenanceSchedule, pk=pk)
    if schedule.technician != request.user:
        return Response({'detail': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)
    schedule.is_active = False
    schedule.save()
    return Response({'detail': 'Schedule deactivated.'}, status=status.HTTP_200_OK)






