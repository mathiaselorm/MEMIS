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
            "Cardiology", "Pediatrics", "Emergency", "Radiology", "Gynecology"
        ])

        # Fetch the user with the specific email to use as 'added_by'
        try:
            user = CustomUser.objects.get(email="memisproject@gmail.com")
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR('User with email memisproject@gmail.com does not exist.'))
            return

        # Predefined medical equipment for assets with department
        medical_equipment = [
            {"name": "Automated External Defibrillator (AED)", "device_type": "Cardiac Care", "department": "Cardiology"},
            {"name": "Bone Densitometer", "device_type": "Diagnostic Imaging", "department": "Radiology"},
            {"name": "Colposcope", "device_type": "Gynecological Care", "department": "Gynecology"},
            {"name": "Endoscope", "device_type": "Surgical", "department": "Surgery"},
            {"name": "Oxygen Cylinder", "device_type": "Respiratory Support", "department": "Emergency"},
            {"name": "Electrosurgical Unit", "device_type": "Surgical", "department": "Surgery"},
            {"name": "Fetal Doppler", "device_type": "Monitoring", "department": "Pediatrics"},
            {"name": "Incubation Warmer", "device_type": "Neonatal Care", "department": "Pediatrics"},
            {"name": "Phototherapy Unit", "device_type": "Neonatal Care", "department": "Pediatrics"},
            {"name": "Laryngoscope", "device_type": "Anesthesia", "department": "Surgery"},
            {"name": "Mechanical Ventilator", "device_type": "Respiratory Support", "department": "Emergency"},
            {"name": "Nebulizer", "device_type": "Respiratory Support", "department": "Emergency"},
            {"name": "Orthopedic Drill", "device_type": "Orthopedics", "department": "Orthopedics"},
            {"name": "Patient Lift", "device_type": "Mobility Aid", "department": "Orthopedics"},
            {"name": "Portable X-Ray Machine", "device_type": "Diagnostic Imaging", "department": "Radiology"},
            {"name": "Pulse Oximeter", "device_type": "Monitoring", "department": "Emergency"},
            {"name": "Sphygmomanometer", "device_type": "Monitoring", "department": "Pediatrics"},
            {"name": "Suction Machine", "device_type": "Surgical", "department": "Surgery"},
            {"name": "Traction Bed", "device_type": "Orthopedics", "department": "Orthopedics"},
            {"name": "Wound VAC", "device_type": "Wound Care", "department": "Surgery"}
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
