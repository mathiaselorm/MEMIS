from django.core.management.base import BaseCommand
from faker import Faker
from accounts.models import CustomUser  # Your Custom User model
from assets.models import Department, Asset, AssetStatus
from django.utils import timezone
import random
from datetime import datetime

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
            user = CustomUser.objects.get(email="memis@gmail.com")
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR('User with email memis@gmail.com does not exist.'))
            return

        # Predefined medical equipment for assets with department
        medical_equipment = [
            # Urology Department Assets
            {"name": "Urodynamic System", "device_type": "Diagnostic Equipment", "department": "Urology"},
            {"name": "Cystoscope", "device_type": "Endoscopic Device", "department": "Urology"},
            {"name": "Lithotripter", "device_type": "Therapeutic Device", "department": "Urology"},
            {"name": "Dialysis Machine", "device_type": "Renal Care", "department": "Urology"},
            {"name": "Bladder Scanner", "device_type": "Diagnostic Imaging", "department": "Urology"},
            
            # Pathology Department Assets
            {"name": "Tissue Processor", "device_type": "Lab Equipment", "department": "Pathology"},
            {"name": "Cryostat", "device_type": "Lab Equipment", "department": "Pathology"},
            {"name": "Hematology Analyzer", "device_type": "Diagnostic Lab Equipment", "department": "Pathology"},
            {"name": "Microtome", "device_type": "Lab Equipment", "department": "Pathology"},
            {"name": "Centrifuge", "device_type": "Lab Equipment", "department": "Pathology"},

            # Orthopedics Department Assets
            {"name": "Bone Saw", "device_type": "Surgical Tool", "department": "Orthopedics"},
            {"name": "Orthopedic Power Drill", "device_type": "Surgical Tool", "department": "Orthopedics"},
            {"name": "Traction Splint", "device_type": "Orthopedic Device", "department": "Orthopedics"},
            {"name": "Joint Replacement Kit", "device_type": "Surgical Kit", "department": "Orthopedics"},
            {"name": "Casting Machine", "device_type": "Therapeutic Device", "department": "Orthopedics"},

            # Oncology Department Assets
            {"name": "Radiotherapy Machine", "device_type": "Therapeutic Device", "department": "Oncology"},
            {"name": "Infusion Pump", "device_type": "Infusion Device", "department": "Oncology"},
            {"name": "Chemotherapy Hood", "device_type": "Protective Equipment", "department": "Oncology"},
            {"name": "Gamma Knife", "device_type": "Stereotactic Radiosurgery", "department": "Oncology"},
            {"name": "Linear Accelerator", "device_type": "Radiotherapy", "department": "Oncology"},

            # Neurology Department Assets
            {"name": "EEG Machine", "device_type": "Diagnostic Equipment", "department": "Neurology"},
            {"name": "EMG Machine", "device_type": "Diagnostic Equipment", "department": "Neurology"},
            {"name": "Nerve Stimulator", "device_type": "Therapeutic Device", "department": "Neurology"},
            {"name": "TMS Machine", "device_type": "Neurostimulation", "department": "Neurology"},
            {"name": "Neurological Hammer", "device_type": "Diagnostic Tool", "department": "Neurology"}
        ]


        # Verify that the predefined departments are in the database
        if len(departments) != 5:
            self.stdout.write(self.style.ERROR('Not all predefined departments exist in the database.'))
            return

        # Ensure each department gets 5 meaningful assets
        self.stdout.write('Creating assets...')
        equipment_index = 0
        total_equipment = len(medical_equipment)
        
        # Predefined list for manufacturers and images
        manufacturer_list = ["MedEquip", "HealthTech", "SurgiTech", "CardioLife", "RespirTech", "NeonatalCare", "InfuCare"]

        for department in departments:
            for _ in range(5):  # 5 assets per department
                # Cycle through the medical_equipment list
                equipment = medical_equipment[equipment_index]
                equipment_index = (equipment_index + 1) % total_equipment  # Increment and reset index if it exceeds list length
                
                embossment_id = f"{equipment['name'].split()[0][:3].upper()}-{random.randint(1, 999):03d}"
                serial_number = f"SN{random.randint(1000000000, 9999999999)}"
                status = random.choice([AssetStatus.ACTIVE, AssetStatus.INACTIVE, AssetStatus.REPAIR, AssetStatus.DECOMMISSIONED])
                manufacturer = random.choice(manufacturer_list)
                model = f"{equipment['name'].split()[0][:3].upper()}-{random.randint(1000, 9999)}"
                embossment_date = fake.date_this_decade()
                manufacturing_date = fake.date_this_decade()
                commission_date = fake.date_this_decade()

                asset = Asset.objects.create(
                    name=equipment["name"],
                    device_type=equipment["device_type"],
                    embossment_id=embossment_id,
                    serial_number=serial_number,
                    status=status,
                    department=department,
                    quantity=random.randint(1, 10),
                    model=model,
                    manufacturer=manufacturer,
                    embossment_date=embossment_date,
                    manufacturing_date=manufacturing_date,
                    description=f"{equipment['name']} used in {equipment['device_type']} applications.",
                    commission_date=commission_date,
                    added_by=user,
                    is_draft=False,
                )
                self.stdout.write(self.style.SUCCESS(f'Asset {asset.name} created for {department.name}'))

        self.stdout.write(self.style.SUCCESS('Database populated successfully with meaningful assets!'))
