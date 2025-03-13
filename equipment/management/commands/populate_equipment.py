from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date
from accounts.models import CustomUser  # or use get_user_model()
from equipment.models import Equipment, Supplier

class Command(BaseCommand):
    help = "Populate predefined equipment items, rotating among 3 user emails for 'added_by'."

    def handle(self, *args, **options):
        # 1) Fetch the 3 possible users. We'll cycle them in a round-robin for the 'added_by' field.
        user_emails = ["mathiaselorm@gmail.com", "memisproject@gmail.com", "memis@gmail.com"]
        all_users = []
        for email in user_emails:
            try:
                user_obj = CustomUser.objects.get(email=email)
                all_users.append(user_obj)
            except CustomUser.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f"User with email '{email}' does not exist. Will skip this user."
                ))

        valid_users = [u for u in all_users if u is not None]
        if not valid_users:
            self.stdout.write(self.style.ERROR(
                "No valid users found among the three emails. Cannot assign 'added_by'. Aborting."
            ))
            return

        # 2) Fully predefined list of 10 equipment items (device_type and department EXACTLY match model choices)
        predefined_equipment = [
            {
            "name": "Portable Ultrasound",
            "device_type": Equipment.DEVICE_TYPE.diagnostic,      # Allowed: "diagnostic"
            "department": Equipment.DEPARTMENT.emergency,         # Allowed: "emergency"
            "operational_status": Equipment.OPERATIONAL_STATUS.functional,
            "model": "PUS-100",
            "manufacturer": "OmniHealth Solutions",
            "serial_number": "SN600001",
            "manufacturing_date": date(2021, 3, 10),
            "description": "Handheld diagnostic ultrasound for rapid emergency evaluations.",
            "supplier_name": "SurgiPlus Corp",
            "decommission_date": None
            },
            {
                "name": "Patient Monitor",
                "device_type": Equipment.DEVICE_TYPE.monitoring,       # Allowed: "monitoring"
                "department": Equipment.DEPARTMENT.inpatient,          # Allowed: "inpatient"
                "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                "model": "PM-2000",
                "manufacturer": "MediHealth Inc",
                "serial_number": "SN600002",
                "manufacturing_date": date(2020, 12, 15),
                "description": "Advanced monitoring system for continuous patient observation.",
                "supplier_name": "MediHealth Inc",
                "decommission_date": None
            },
            {
                "name": "Surgical Microscope",
                "device_type": Equipment.DEVICE_TYPE.other,            # Allowed: "other"
                "department": Equipment.DEPARTMENT.surgical,           # Allowed: "surgical"
                "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                "model": "SM-300",
                "manufacturer": "SurgiPlus Corp",
                "serial_number": "SN600003",
                "manufacturing_date": date(2021, 1, 20),
                "description": "High-quality microscope for enhanced visualization during surgery.",
                "supplier_name": "SurgiPlus Corp",
                "decommission_date": None
            },
            {
                "name": "Defibrillator",
                "device_type": Equipment.DEVICE_TYPE.life_support,     # Allowed: "life_support"
                "department": Equipment.DEPARTMENT.emergency,           # Allowed: "emergency"
                "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                "model": "DF-500",
                "manufacturer": "GlobalMed Devices",
                "serial_number": "SN600004",
                "manufacturing_date": date(2021, 2, 5),
                "description": "Automated external defibrillator for cardiac emergencies.",
                "supplier_name": "GlobalMed Devices",
                "decommission_date": None
            },
            {
                "name": "Anesthesia Machine",
                "device_type": Equipment.DEVICE_TYPE.therapeutic,      # Allowed: "therapeutic"
                "department": Equipment.DEPARTMENT.surgical,           # Allowed: "surgical"
                "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                "model": "AM-1000",
                "manufacturer": "BioCare Systems",
                "serial_number": "SN600005",
                "manufacturing_date": date(2021, 4, 25),
                "description": "Advanced anesthesia machine ensuring precise dosage delivery during surgery.",
                "supplier_name": "BioCare Systems",
                "decommission_date": None
            },
            {
                "name": "Endoscopy System",
                "device_type": Equipment.DEVICE_TYPE.diagnostic,       # Allowed: "diagnostic"
                "department": Equipment.DEPARTMENT.surgical,           # Allowed: "surgical"
                "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                "model": "ENDO-100",
                "manufacturer": "TechMed Innovations",
                "serial_number": "SN600007",
                "manufacturing_date": date(2020, 12, 1),
                "description": "High-definition endoscopy system for minimally invasive procedures.",
                "supplier_name": "BioCare Systems",
                "decommission_date": None
            },
        ]

        self.stdout.write("\nCreating 10 predefined equipment records with validated device types & departments...\n")

        user_index = 0  # We'll cycle through valid_users
        total_created = 0

        with transaction.atomic():
            for eq_data in predefined_equipment:
                # 2A) Find the supplier by company_name (using updated field name)
                supplier_obj = None
                if eq_data["supplier_name"]:
                    supplier_obj = Supplier.objects.filter(company_name=eq_data["supplier_name"]).first()
                    if not supplier_obj:
                        self.stdout.write(self.style.WARNING(
                            f"Supplier '{eq_data['supplier_name']}' not found. Equipment will have no supplier."
                        ))

                # 2B) Pick a user from valid_users in a round-robin
                assigned_user = valid_users[user_index % len(valid_users)]
                user_index += 1

                # 2C) Create Equipment record
                equipment = Equipment(
                    name=eq_data["name"],
                    device_type=eq_data["device_type"],
                    department=eq_data["department"],
                    operational_status=eq_data["operational_status"],
                    model=eq_data["model"],
                    manufacturer=eq_data["manufacturer"],
                    serial_number=eq_data["serial_number"],
                    manufacturing_date=eq_data["manufacturing_date"],
                    description=eq_data["description"],
                    supplier=supplier_obj,
                    decommission_date=eq_data["decommission_date"],
                    added_by=assigned_user
                )
                equipment.save()  # triggers auto-generation of equipment_id

                total_created += 1
                self.stdout.write(self.style.SUCCESS(
                    f"Created Equipment: {equipment.name} "
                    f"| ID={equipment.equipment_id} "
                    f"| Dept={equipment.department} "
                    f"| Type={equipment.device_type} "
                    f"| Status={equipment.operational_status} "
                    f"| Added By={assigned_user.email}"
                ))

        self.stdout.write(self.style.SUCCESS(f"\nAll {total_created} predefined equipment records created successfully!"))
