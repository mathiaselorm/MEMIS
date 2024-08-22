from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Asset, MaintenanceReport, Department, AssetStatus
from .serializers import DepartmentSerializer, AssetSerializer, MaintenanceReportSerializer
from .utils import get_object_by_id_or_slug




class DepartmentList(APIView):
    """
    List all departments or create a new department.
    """
    def get(self, request, format=None):
        departments = Department.objects.all()
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = DepartmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class DepartmentDetail(APIView):
    """
    Retrieve, update or delete a department using either an ID or a slug.
    """
    def get_object(self, identifier):
        """
        Use the get_object_by_id_or_slug utility to handle both IDs and slugs.
        """
        return get_object_by_id_or_slug(Department, identifier)

    def get(self, request, identifier, format=None):
        department = self.get_object(identifier)
        serializer = DepartmentSerializer(department)
        return Response(serializer.data)

    def put(self, request, identifier, format=None):
        department = self.get_object(identifier)
        serializer = DepartmentSerializer(department, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, identifier, format=None):
        department = self.get_object(identifier)
        department.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TotalDepartmentsView(APIView):
    """
    View to return the total number of departments in the system.
    """
    def get(self, request, format=None):
        total_departments = Department.objects.count()
        return Response({'total_departments': total_departments})


class AssetList(APIView):
    """
    List all assets or create a new asset.
    """
    def get(self, request, format=None):
        assets = Asset.objects.all()
        serializer = AssetSerializer(assets, many=True)
        return Response(serializer.data)

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

    def get(self, request, pk, format=None):
        asset = self.get_object(pk)
        serializer = AssetSerializer(asset)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        asset = self.get_object(pk)
        serializer = AssetSerializer(asset, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        asset = self.get_object(pk)
        asset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TotalAssetsView(APIView):
    """
    View to return the total number of assets in the system.
    """
    def get(self, request, format=None):
        total_assets = Asset.objects.count()
        return Response({'total_assets': total_assets})
    

class TotalAssetsUnderMaintenanceView(APIView):
    """
    View to return the total number of assets currently under maintenance.
    """
    def get(self, request, format=None):
        # Using the AssetStatus.REPAIR to filter assets under maintenance
        assets_under_maintenance_count = Asset.objects.filter(status=AssetStatus.REPAIR).count()
        return Response({'assets_under_maintenance': assets_under_maintenance_count})


class AssetMaintenanceReports(APIView):
    """
    List all maintenance reports for a specific asset.
    """
    def get(self, request, pk, format=None):
        try:
            asset = Asset.objects.get(pk=pk)
        except Asset.DoesNotExist:
            return Response({'error': 'Asset not found'}, status=status.HTTP_404_NOT_FOUND)

        reports = MaintenanceReport.objects.filter(asset=asset)
        serializer = MaintenanceReportSerializer(reports, many=True)
        return Response(serializer.data)
    

class CreateMaintenanceReport(APIView):
    """
    Create a new maintenance report, expecting asset identifier in the request body.
    """
    def post(self, request, format=None):
        serializer = MaintenanceReportSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class MaintenanceReportDetail(APIView):
    """
    Retrieve, update, or delete a maintenance report specific to an asset.
    """
    def get_object(self, asset_pk, report_pk):
        try:
            # Ensure that the report belongs to the specified asset
            return MaintenanceReport.objects.get(pk=report_pk, asset__pk=asset_pk)
        except MaintenanceReport.DoesNotExist:
            raise Http404("Maintenance report not found")

    def get(self, request, asset_pk, report_pk, format=None):
        report = self.get_object(asset_pk, report_pk)
        serializer = MaintenanceReportSerializer(report)
        return Response(serializer.data)

    def put(self, request, asset_pk, report_pk, format=None):
        report = self.get_object(asset_pk, report_pk)
        serializer = MaintenanceReportSerializer(report, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, asset_pk, report_pk, format=None):
        report = self.get_object(asset_pk, report_pk)
        report.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

