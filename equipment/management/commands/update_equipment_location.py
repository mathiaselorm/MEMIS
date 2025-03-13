import random
from django.core.management.base import BaseCommand
from equipment.models import Equipment

class Command(BaseCommand):
    help = "Update equipment location with meaningful data if not already set."

    def handle(self, *args, **options):
        # Mapping of department codes to realistic storage/usage locations.
        location_mapping = {
            "emergency": "Emergency Room",
            "opd": "Outpatient Department, Room 101",
            "inpatient": "Inpatient Ward, Block A",
            "maternity": "MLabor & Delivery Unit",
            "laboratory": "Laboratory Section, Floor 2",
            "pediatric": "Pediatric Unit, Room 203",
            "icu": "Intensive Care Unit (ICU)",
            "radiology": "Radiology Department, Room 305",
            "oncology": "Infusion Clinic",
            "surgical": "Surgical Suite",
            "cardiology": " Heart Center",
            "orthopedic": "Fracture Clinic",
            "urology": "Diagnostic Imaging Center",
            "neurology": "Brain and Nerve Center",
            "gynecology": "Gynecology Unit",
        }

        updated_count = 0

        # Loop through all equipment in the database.
        for eq in Equipment.objects.all():
            # Update only if location is missing or empty.
            if not eq.location:
                # Get the corresponding location based on the equipment's department.
                # If the department isn't in the mapping, default to a general location.
                new_location = location_mapping.get(eq.department, "General Equipment Storage")
                eq.location = new_location
                eq.save(update_fields=["location"])
                updated_count += 1
                self.stdout.write(f"Updated '{eq.name}' (ID: {eq.equipment_id}) with location: {new_location}")

        self.stdout.write(self.style.SUCCESS(f"Successfully updated {updated_count} equipment records."))
