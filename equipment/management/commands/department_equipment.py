from django.core.management.base import BaseCommand
from faker import Faker
from accounts.models import CustomUser  # or use get_user_model()
from equipment.models import Department, Equipment
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Populate the database with meaningful medical equipment for predefined departments'

    def handle(self, *args, **kwargs):
        fake = Faker()

        # Fetch the predefined departments from the database
        departments = Department.objects.filter(name__in=[
            "Urology", "Pathology", "Orthopedics", "Oncology", "Neurology"
        ])

        # Fetch the user with the specific email to use as 'added_by'
        try:
            user = CustomUser.objects.get(email="mathiaselorm@gmail.com")
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR('User with email mathiaselorm@gmail.com does not exist.'))
            return

        # Predefined medical equipment with associated department names
        medical_equipment = [
            {"name": "Urodynamic System", "device_type": "Diagnostic Equipment", "department": "Urology"},
            {"name": "Cystoscope", "device_type": "Endoscopic Device", "department": "Urology"},
            {"name": "Lithotripter", "device_type": "Therapeutic Device", "department": "Urology"},
            {"name": "Dialysis Machine", "device_type": "Renal Care", "department": "Urology"},
            {"name": "Bladder Scanner", "device_type": "Diagnostic Imaging", "department": "Urology"},

            {"name": "Tissue Processor", "device_type": "Lab Equipment", "department": "Pathology"},
            {"name": "Cryostat", "device_type": "Lab Equipment", "department": "Pathology"},
            {"name": "Hematology Analyzer", "device_type": "Diagnostic Lab Equipment", "department": "Pathology"},
            {"name": "Microtome", "device_type": "Lab Equipment", "department": "Pathology"},
            {"name": "Centrifuge", "device_type": "Lab Equipment", "department": "Pathology"},

            {"name": "Bone Saw", "device_type": "Surgical Tool", "department": "Orthopedics"},
            {"name": "Orthopedic Power Drill", "device_type": "Surgical Tool", "department": "Orthopedics"},
            {"name": "Traction Splint", "device_type": "Orthopedic Device", "department": "Orthopedics"},
            {"name": "Joint Replacement Kit", "device_type": "Surgical Kit", "department": "Orthopedics"},
            {"name": "Casting Machine", "device_type": "Therapeutic Device", "department": "Orthopedics"},

            {"name": "Radiotherapy Machine", "device_type": "Therapeutic Device", "department": "Oncology"},
            {"name": "Infusion Pump", "device_type": "Infusion Device", "department": "Oncology"},
            {"name": "Chemotherapy Hood", "device_type": "Protective Equipment", "department": "Oncology"},
            {"name": "Gamma Knife", "device_type": "Stereotactic Radiosurgery", "department": "Oncology"},
            {"name": "Linear Accelerator", "device_type": "Radiotherapy", "department": "Oncology"},

            {"name": "EEG Machine", "device_type": "Diagnostic Equipment", "department": "Neurology"},
            {"name": "EMG Machine", "device_type": "Diagnostic Equipment", "department": "Neurology"},
            {"name": "Nerve Stimulator", "device_type": "Therapeutic Device", "department": "Neurology"},
            {"name": "TMS Machine", "device_type": "Neurostimulation", "department": "Neurology"},
            {"name": "Neurological Hammer", "device_type": "Diagnostic Tool", "department": "Neurology"}
        ]

        # Verify that the predefined departments exist
        if departments.count() != 5:
            self.stdout.write(self.style.ERROR('Not all predefined departments exist in the database.'))
            return

        self.stdout.write('Creating equipment...')
        equipment_index = 0
        total_equipment = len(medical_equipment)
        manufacturer_list = ["MedEquip", "HealthTech", "SurgiTech", "CardioLife", "RespirTech", "NeonatalCare", "InfuCare"]

        for department in departments:
            for _ in range(5):  # Create 5 equipment entries per department
                equipment_data = medical_equipment[equipment_index]
                equipment_index = (equipment_index + 1) % total_equipment

                # Generate a unique embossment_id and serial_number
                embossment_id = f"{equipment_data['name'].split()[0][:3].upper()}-{random.randint(1, 999):03d}"
                serial_number = f"SN{random.randint(1000000000, 9999999999)}"
                operational_status = random.choice([
                    Equipment.OPERATIONAL_STATUS.functional,
                    Equipment.OPERATIONAL_STATUS.under_maintenance,
                    Equipment.OPERATIONAL_STATUS.decommissioned
                ])
                manufacturer = random.choice(manufacturer_list)
                model = f"{equipment_data['name'].split()[0][:3].upper()}-{random.randint(1000, 9999)}"
                manufacturing_date = fake.date_this_decade()

                equipment = Equipment.objects.create(
                    name=equipment_data["name"],
                    device_type=equipment_data["device_type"],
                    embossment_id=embossment_id,
                    serial_number=serial_number,
                    operational_status=operational_status,
                    department=department,
                    model=model,
                    manufacturer=manufacturer,
                    manufacturing_date=manufacturing_date,
                    description=f"{equipment_data['name']} used in {equipment_data['device_type']} applications.",
                    decommission_date=None,
                    added_by=user
                )
                self.stdout.write(self.style.SUCCESS(f'Equipment {equipment.name} created for {department.name}'))

        self.stdout.write(self.style.SUCCESS('Database populated successfully with meaningful equipment!'))
