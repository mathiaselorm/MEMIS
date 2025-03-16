from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date
from accounts.models import CustomUser  # or use get_user_model() if preferred
from equipment.models import Equipment, Supplier

class Command(BaseCommand):
    help = "Populate 10 additional equipment items (with some decommissioned), randomly assigning 'added_by' from all CustomUser objects."

    def handle(self, *args, **options):
        # Fetch all users from the CustomUser table
        valid_users = list(CustomUser.objects.all())
        if not valid_users:
            self.stdout.write(self.style.ERROR("No users found in the CustomUser table. Aborting."))
            return

        # 2) Fully predefined list of 10 equipment items
        # Ensure device_type and department exactly match the model choices,
        # and include the location field.
        predefined_equipment = [
            {
                "name": "Portable Ultrasound",
                "device_type": Equipment.DEVICE_TYPE.diagnostic,
                "department": Equipment.DEPARTMENT.emergency,
                "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                "model": "PUS-100",
                "manufacturer": "OmniHealth Solutions",
                "serial_number": "SN600001",
                "manufacturing_date": date(2021, 3, 10),
                "description": "Handheld diagnostic ultrasound for rapid emergency evaluations.",
                "supplier_name": "SurgiPlus Corp",
                "decommission_date": None,
                "location": "Emergency Room"
            },
            {
                "name": "Patient Monitor",
                "device_type": Equipment.DEVICE_TYPE.monitoring,
                "department": Equipment.DEPARTMENT.inpatient,
                "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                "model": "PM-2000",
                "manufacturer": "MediHealth Inc",
                "serial_number": "SN600002",
                "manufacturing_date": date(2020, 12, 15),
                "description": "Advanced monitoring system for continuous patient observation.",
                "supplier_name": "MediHealth Inc",
                "decommission_date": None,
                "location": "ICU"
            },
            {
                "name": "Surgical Microscope",
                "device_type": Equipment.DEVICE_TYPE.other,
                "department": Equipment.DEPARTMENT.surgical,
                "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                "model": "SM-300",
                "manufacturer": "SurgiPlus Corp",
                "serial_number": "SN600003",
                "manufacturing_date": date(2021, 1, 20),
                "description": "High-quality microscope for enhanced visualization during surgery.",
                "supplier_name": "SurgiPlus Corp",
                "decommission_date": None,
                "location": "Operating Room"
            },
            {
                "name": "Defibrillator",
                "device_type": Equipment.DEVICE_TYPE.life_support,
                "department": Equipment.DEPARTMENT.emergency,
                "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                "model": "DF-500",
                "manufacturer": "GlobalMed Devices",
                "serial_number": "SN600004",
                "manufacturing_date": date(2021, 2, 5),
                "description": "Automated external defibrillator for cardiac emergencies.",
                "supplier_name": "GlobalMed Devices",
                "decommission_date": None,
                "location": "Emergency Room"
            },
            {
                "name": "Anesthesia Machine",
                "device_type": Equipment.DEVICE_TYPE.therapeutic,
                "department": Equipment.DEPARTMENT.surgical,
                "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                "model": "AM-1000",
                "manufacturer": "BioCare Systems",
                "serial_number": "SN600005",
                "manufacturing_date": date(2021, 4, 25),
                "description": "Advanced anesthesia machine ensuring precise dosage delivery during surgery.",
                "supplier_name": "BioCare Systems",
                "decommission_date": None,
                "location": "Operating Room"
            },
            {
                "name": "Endoscopy System",
                "device_type": Equipment.DEVICE_TYPE.diagnostic,
                "department": Equipment.DEPARTMENT.surgical,
                "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                "model": "ENDO-100",
                "manufacturer": "TechMed Innovations",
                "serial_number": "SN600007",
                "manufacturing_date": date(2020, 12, 1),
                "description": "High-definition endoscopy system for minimally invasive procedures.",
                "supplier_name": "BioCare Systems",
                "decommission_date": None,
                "location": "Operating Room"
            },
            {
                "name": "Infusion Pump",
                "device_type": Equipment.DEVICE_TYPE.other,
                "department": Equipment.DEPARTMENT.inpatient,
                "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                "model": "IP-300",
                "manufacturer": "OmniHealth Solutions",
                "serial_number": "SN600008",
                "manufacturing_date": date(2021, 5, 5),
                "description": "Automated infusion pump for accurate medication delivery.",
                "supplier_name": "OmniHealth Solutions",
                "decommission_date": None,
                "location": "General Ward"
            },
            {
                "name": "Ventilator",
                "device_type": Equipment.DEVICE_TYPE.life_support,
                "department": Equipment.DEPARTMENT.icu,
                "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                "model": "VENT-500",
                "manufacturer": "MediHealth Inc",
                "serial_number": "SN600009",
                "manufacturing_date": date(2021, 6, 15),
                "description": "Mechanical ventilator for critical respiratory support.",
                "supplier_name": "MediHealth Inc",
                "decommission_date": None,
                "location": "ICU"
            },
            {
                "name": "X-Ray Machine",
                "device_type": Equipment.DEVICE_TYPE.other,
                "department": Equipment.DEPARTMENT.radiology,
                "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                "model": "XR-400",
                "manufacturer": "GlobalMed Devices",
                "serial_number": "SN600010",
                "manufacturing_date": date(2021, 3, 30),
                "description": "Digital X-ray machine for diagnostic imaging.",
                "supplier_name": "GlobalMed Devices",
                "decommission_date": None,
                "location": "Radiology Department"
            },
            {
                "name": "Infant Warmer",
                "device_type": Equipment.DEVICE_TYPE.other,
                "department": Equipment.DEPARTMENT.maternity,
                "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                "model": "IW-150",
                "manufacturer": "BioCare Systems",
                "serial_number": "SN600011",
                "manufacturing_date": date(2021, 7, 10),
                "description": "Specialized warmer for newborn care.",
                "supplier_name": "BioCare Systems",
                "decommission_date": None,
                "location": "Maternity Ward"
                
            },
            {
                "name": "MRI Scanner",
                "device_type": Equipment.DEVICE_TYPE.diagnostic,
                "department": Equipment.DEPARTMENT.radiology,
                "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                "model": "MRI-900",
                "manufacturer": "GlobalMed Devices",
                "serial_number": "SN700001",
                "manufacturing_date": date(2019, 11, 20),
                "description": "High-resolution MRI scanner for detailed diagnostic imaging.",
                "supplier_name": "GlobalMed Devices",
                "decommission_date": None,
                "location": "Radiology Department"
            },
            {
                "name": "CT Scanner",
                "device_type": Equipment.DEVICE_TYPE.diagnostic,
                "department": Equipment.DEPARTMENT.radiology,
                "operational_status": Equipment.OPERATIONAL_STATUS.decommissioned,
                "model": "CT-800",
                "manufacturer": "TechMed Innovations",
                "serial_number": "SN700002",
                "manufacturing_date": date(2018, 8, 15),
                "description": "CT scanner, now decommissioned due to outdated technology.",
                "supplier_name": "TechMed Innovations",
                "decommission_date": date(2023, 1, 10),
                "location": "Radiology Department"
            },
            {
                "name": "X-Ray Film Processor",
                "device_type": Equipment.DEVICE_TYPE.other,
                "department": Equipment.DEPARTMENT.radiology,
                "operational_status": Equipment.OPERATIONAL_STATUS.decommissioned,
                "model": "XFP-300",
                "manufacturer": "MediHealth Inc",
                "serial_number": "SN700003",
                "manufacturing_date": date(2017, 5, 30),
                "description": "Legacy X-Ray film processor, replaced by digital systems.",
                "supplier_name": "MediHealth Inc",
                "decommission_date": date(2022, 6, 1),
                "location": "Radiology Department"
            },
            {
                "name": "Infusion Pump II",
                "device_type": Equipment.DEVICE_TYPE.other,
                "department": Equipment.DEPARTMENT.inpatient,
                "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                "model": "IP-400",
                "manufacturer": "OmniHealth Solutions",
                "serial_number": "SN700004",
                "manufacturing_date": date(2020, 2, 14),
                "description": "Next generation infusion pump with improved accuracy.",
                "supplier_name": "OmniHealth Solutions",
                "decommission_date": None,
                "location": "General Ward"
            },
            {
                "name": "Ventilator Pro",
                "device_type": Equipment.DEVICE_TYPE.life_support,
                "department": Equipment.DEPARTMENT.icu,
                "operational_status": Equipment.OPERATIONAL_STATUS.decommissioned,
                "model": "VENT-PRO",
                "manufacturer": "MediHealth Inc",
                "serial_number": "SN700005",
                "manufacturing_date": date(2020, 9, 9),
                "description": "Advanced ventilator, now decommissioned after replacement.",
                "supplier_name": "MediHealth Inc",
                "decommission_date": date(2023, 3, 5),
                "location": "ICU"
            },
            {
                "name": "Dialysis Machine",
                "device_type": Equipment.DEVICE_TYPE.other,
                "department": Equipment.DEPARTMENT.inpatient,
                "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                "model": "DIAL-100",
                "manufacturer": "BioCare Systems",
                "serial_number": "SN700006",
                "manufacturing_date": date(2021, 7, 21),
                "description": "State-of-the-art dialysis machine for renal patients.",
                "supplier_name": "BioCare Systems",
                "decommission_date": None,
                "location": "Renal Unit"
            },
            {
                "name": "ECG Machine",
                "device_type": Equipment.DEVICE_TYPE.monitoring,
                "department": Equipment.DEPARTMENT.inpatient,
                "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                "model": "ECG-500",
                "manufacturer": "OmniHealth Solutions",
                "serial_number": "SN700007",
                "manufacturing_date": date(2021, 10, 10),
                "description": "Modern ECG machine for cardiac monitoring.",
                "supplier_name": "OmniHealth Solutions",
                "decommission_date": None,
                "location": "Cardiology Department"
            },
            {
                "name": "Infant Incubator",
                "device_type": Equipment.DEVICE_TYPE.other,
                "department": Equipment.DEPARTMENT.maternity,
                "operational_status": Equipment.OPERATIONAL_STATUS.decommissioned,
                "model": "INC-200",
                "manufacturer": "BioCare Systems",
                "serial_number": "SN700008",
                "manufacturing_date": date(2019, 3, 25),
                "description": "Old model incubator now decommissioned due to efficiency issues.",
                "supplier_name": "BioCare Systems",
                "decommission_date": date(2021, 12, 31),
                "location": "Maternity Ward"
            },
        ]

        self.stdout.write("\nCreating 10 predefined equipment records with complete data...\n")

        user_index = 0  # Cycle through valid_users
        total_created = 0

        with transaction.atomic():
            for eq_data in predefined_equipment:
                # 2A) Find the supplier by company_name (using updated field name)
                supplier_obj = None
                if eq_data.get("supplier_name"):
                    supplier_obj = Supplier.objects.filter(company_name=eq_data["supplier_name"]).first()
                    if not supplier_obj:
                        self.stdout.write(self.style.WARNING(
                            f"Supplier '{eq_data['supplier_name']}' not found. Equipment will have no supplier."
                        ))

                # 2B) Pick a user from valid_users in a round-robin
                assigned_user = valid_users[user_index % len(valid_users)]
                user_index += 1

                # 2C) Create Equipment record (including the location field)
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
                    added_by=assigned_user,
                    location=eq_data["location"]
                )
                equipment.save()  # Triggers auto-generation of equipment_id

                total_created += 1
                self.stdout.write(self.style.SUCCESS(
                    f"Created Equipment: {equipment.name} "
                    f"| ID={equipment.equipment_id} "
                    f"| Dept={equipment.department} "
                    f"| Type={equipment.device_type} "
                    f"| Status={equipment.operational_status} "
                    f"| Location={equipment.location} "
                    f"| Added By={assigned_user.email}"
                ))

        self.stdout.write(self.style.SUCCESS(f"\nAll {total_created} predefined equipment records created successfully!"))
