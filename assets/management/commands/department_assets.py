from django.core.management.base import BaseCommand
from faker import Faker
from accounts.models import CustomUser  # Your Custom User model
from assets.models import Department, Asset, AssetStatus
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Populate the database with meaningful medical equipment for predefined departments'

    def handle(self, *args, **kwargs):
        fake = Faker()

        # Fetch the predefined departments from the database
        departments = Department.objects.filter(name__in=[
            "Cardiology", "Pediatrics", "Emergency", "Radiology", "Surgery"
        ])

        # Fetch the user with the specific email to use as 'added_by'
        try:
            user = CustomUser.objects.get(email="memisproject@gmail.com")
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR('User with email memisproject@gmail.com does not exist.'))
            return

        # Predefined medical equipment for assets
        medical_equipment = [
            {"name": "Automated External Defibrillator (AED)", "device_type": "Cardiac Care"},
            {"name": "Bone Densitometer", "device_type": "Diagnostic Imaging"},
            {"name": "Colposcope", "device_type": "Gynecological Care"},
            {"name": "Endoscope", "device_type": "Surgical"},
            {"name": "Oxygen Cylinder", "device_type": "Respiratory Support"},
            {"name": "Electrosurgical Unit", "device_type": "Surgical"},
            {"name": "Fetal Doppler", "device_type": "Monitoring"},
            {"name": "Incubation Warmer", "device_type": "Neonatal Care"},
            {"name": "Phototherapy Unit", "device_type": "Neonatal Care"},
            {"name": "Laryngoscope", "device_type": "Anesthesia"},
            {"name": "Mechanical Ventilator", "device_type": "Respiratory Support"},
            {"name": "Nebulizer", "device_type": "Respiratory Support"},
            {"name": "Orthopedic Drill", "device_type": "Orthopedics"},
            {"name": "Patient Lift", "device_type": "Mobility Aid"},
            {"name": "Portable X-Ray Machine", "device_type": "Diagnostic Imaging"},
            {"name": "Pulse Oximeter", "device_type": "Monitoring"},
            {"name": "Sphygmomanometer", "device_type": "Monitoring"},
            {"name": "Suction Machine", "device_type": "Surgical"},
            {"name": "Traction Bed", "device_type": "Orthopedics"},
            {"name": "Wound VAC", "device_type": "Wound Care"},
        ]


        # Verify that the predefined departments are in the database
        if len(departments) != 5:
            self.stdout.write(self.style.ERROR('Not all predefined departments exist in the database.'))
            return

        # Ensure each department gets 5 meaningful assets
        self.stdout.write('Creating assets...')
        equipment_index = 0
        total_equipment = len(medical_equipment)
        
        for department in departments:
            for _ in range(5):  # 5 assets per department
                # Cycle through the medical_equipment list
                equipment = medical_equipment[equipment_index]
                equipment_index = (equipment_index + 1) % total_equipment  # Increment and reset index if it exceeds list length
                
                asset = Asset.objects.create(
                    name=equipment["name"],
                    device_type=equipment["device_type"],
                    embossment_id=str(fake.unique.uuid4())[:20],  # Truncate to 20 characters if needed
                    status=random.choice([AssetStatus.ACTIVE, AssetStatus.INACTIVE, AssetStatus.REPAIR, AssetStatus.DECOMMISSIONED]),  # Use valid status choices
                    department=department,
                    quantity=random.randint(1, 10),  # Random quantity
                    model=fake.word(),
                    manufacturer=fake.company(),
                    serial_number=str(fake.unique.uuid4())[:20],  # Truncate to 20 characters if needed
                    embossment_date=fake.date_this_decade(),
                    manufacturing_date=fake.date_this_decade(),
                    description=f"{equipment['name']} used in {equipment['device_type']} applications.",
                    commission_date=fake.date_this_decade(),
                    added_by=user,  # Use the specified user
                    is_draft=False  # Assuming assets are not in draft
                )
                self.stdout.write(self.style.SUCCESS(f'Asset {asset.name} created for {department.name}'))

        self.stdout.write(self.style.SUCCESS('Database populated successfully with meaningful assets!'))
