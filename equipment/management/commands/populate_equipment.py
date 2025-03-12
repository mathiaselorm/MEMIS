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
                "name": "Hematology Analyzer",
                "device_type": Equipment.DEVICE_TYPE.lab,
                "department": Equipment.DEPARTMENT.laboratory,
                "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                "model": "HEMA-3030",
                "manufacturer": "NeoTech Labs",  # Different from 'GlobalMed Devices'
                "serial_number": "SN100001",
                "manufacturing_date": date(2019, 3, 20),
                "description": "Lab device for blood analysis.",
                "supplier_name": "GlobalMed Devices",  # Link to a different supplier
                "decommission_date": None
            },
            {
                "name": "EEG Machine",
                "device_type": Equipment.DEVICE_TYPE.diagnostic,
                "department": Equipment.DEPARTMENT.neurology,
                "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                "model": "EEG-999",
                "manufacturer": "MediHealth Inc",  # Not the same as supplier
                "serial_number": "SN100002",
                "manufacturing_date": date(2020, 6, 11),
                "description": "Diagnostic device for brain wave analysis.",
                "supplier_name": "VitalCare Supplies",
                "decommission_date": None
            },
            {
                "name": "Centrifuge",
                "device_type": Equipment.DEVICE_TYPE.lab,
                "department": Equipment.DEPARTMENT.laboratory,
                "operational_status": Equipment.OPERATIONAL_STATUS.under_maintenance,
                "model": "CENT-500",
                "manufacturer": "BioCare Systems",
                "serial_number": "SN100003",
                "manufacturing_date": date(2018, 2, 1),
                "description": "Lab equipment for separating fluids.",
                "supplier_name": "TechMed Innovations",
                "decommission_date": None
            },
            {
                "name": "CT Scanner",
                "device_type": Equipment.DEVICE_TYPE.diagnostic,    # "diagnostic"
                "department": Equipment.DEPARTMENT.radiology,       # "radiology"
                "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                "model": "CTS-5000",
                "manufacturer": "XRayVision",
                "serial_number": "SN300001",
                "manufacturing_date": date(2019, 8, 15),
                "description": "Diagnostic imaging device for cross-sectional scans.",
                "supplier_name": "MediHealth Inc",
                "decommission_date": None
            },
            {
                "name": "Surgical Laser",
                "device_type": Equipment.DEVICE_TYPE.therapeutic,   # "therapeutic"
                "department": Equipment.DEPARTMENT.surgical,        # "surgical"
                "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                "model": "LASER-700",
                "manufacturer": "SurgiLight",
                "serial_number": "SN300002",
                "manufacturing_date": date(2021, 2, 2),
                "description": "Therapeutic laser for precision surgery.",
                "supplier_name": "SurgiPlus Corp",
                "decommission_date": None
            },
            {
                    "name": "X-Ray Machine",
                    "device_type": Equipment.DEVICE_TYPE.diagnostic,           # "diagnostic"
                    "department": Equipment.DEPARTMENT.radiology,              # "radiology"
                    "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                    "model": "XRM-900",
                    "manufacturer": "XRayVision",
                    "serial_number": "SN200010",
                    "manufacturing_date": date(2020, 10, 25),
                    "description": "Diagnostic device for radiology imaging.",
                    "supplier_name": "FutureLine Medical",
                    "decommission_date": None
                },
            {
                    "name": "Contraction Monitor",
                    "device_type": Equipment.DEVICE_TYPE.monitoring,     # "monitoring"
                    "department": Equipment.DEPARTMENT.maternity,        # "maternity"
                    "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                    "model": "CM-2021",
                    "manufacturer": "NeoNatalCare",
                    "serial_number": "SN300005",
                    "manufacturing_date": date(2020, 1, 15),
                    "description": "Monitors uterine contractions in maternity ward.",
                    "supplier_name": "GlobalMed Devices",
                    "decommission_date": None
                },
            {
                    "name": "Blood Analyzer",
                    "device_type": Equipment.DEVICE_TYPE.lab,            # "lab"
                    "department": Equipment.DEPARTMENT.laboratory,       # "laboratory"
                    "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                    "model": "BLA-101",
                    "manufacturer": "LabSolutions",
                    "serial_number": "SN200004",
                    "manufacturing_date": date(2017, 5, 3),
                    "description": "Lab device for analyzing blood samples.",
                    "supplier_name": "BioCare Systems",
                    "decommission_date": None
                },
                {
                    "name": "Fetal Monitor",
                    "device_type": Equipment.DEVICE_TYPE.monitoring,      # "monitoring"
                    "department": Equipment.DEPARTMENT.maternity,         # "maternity"
                    "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                    "model": "FET-700",
                    "manufacturer": "NeoNatalCare",
                    "serial_number": "SN200005",
                    "manufacturing_date": date(2021, 4, 5),
                    "description": "Monitoring device for fetal heart rate.",
                    "supplier_name": "GlobalMed Devices",
                    "decommission_date": None
                },
                {
                    "name": "Autoclave",
                    "device_type": Equipment.DEVICE_TYPE.hospital_industrial,  # "hospital_industrial"
                    "department": Equipment.DEPARTMENT.surgical,               # "surgical"
                    "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                    "model": "AUTO-CLV",
                    "manufacturer": "SterileSafe",
                    "serial_number": "SN200006",
                    "manufacturing_date": date(2016, 11, 2),
                    "description": "Hospital-industrial device for sterilizing surgical tools.",
                    "supplier_name": "OmniHealth Solutions",
                    "decommission_date": None
                },
                {
                    "name": "Fire Extinguisher",
                    "device_type": Equipment.DEVICE_TYPE.safety_equipment,     # "safety_equipment"
                    "department": Equipment.DEPARTMENT.emergency,              # "emergency"
                    "operational_status": Equipment.OPERATIONAL_STATUS.non_functional,
                    "model": "FEXT-100",
                    "manufacturer": "SafeLife",
                    "serial_number": "SN200007",
                    "manufacturing_date": date(2015, 9, 1),
                    "description": "Safety equipment for fire emergencies.",
                    "supplier_name": "SafeLife Equipment",
                    "decommission_date": None
                },
                {
                    "name": "Fluoroscopy Machine",
                    "device_type": Equipment.DEVICE_TYPE.diagnostic,           # "diagnostic"
                    "department": Equipment.DEPARTMENT.radiology,              # "radiology"
                    "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                    "model": "FLUOR-808",
                    "manufacturer": "XRayVision",
                    "serial_number": "SN300010",
                    "manufacturing_date": date(2021, 9, 5),
                    "description": "Diagnostic imaging device for real-time moving images.",
                    "supplier_name": "FutureLine Medical",
                    "decommission_date": None
                },
                {
                    "name": "Infusion Pump",
                    "device_type": Equipment.DEVICE_TYPE.monitoring,
                    "department": Equipment.DEPARTMENT.inpatient,
                    "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                    "model": "INFU-202",
                    "manufacturer": "MediHealth Inc",
                    "serial_number": "SN100005",
                    "manufacturing_date": date(2021, 4, 5),
                    "description": "Monitoring/infusion device for inpatient care.",
                    "supplier_name": "SafeLife Equipment",
                    "decommission_date": None
                },
                {
                    "name": "Dialysis Machine",
                    "device_type": Equipment.DEVICE_TYPE.life_support,
                    "department": Equipment.DEPARTMENT.urology,
                    "operational_status": Equipment.OPERATIONAL_STATUS.decommissioned,
                    "model": "DIAL-6000",
                    "manufacturer": "GlobalMed Devices",
                    "serial_number": "SN100006",
                    "manufacturing_date": date(2017, 9, 10),
                    "description": "Life-support device for renal care.",
                    "supplier_name": "MediHealth Inc",
                    # Decommissioned => set a date
                    "decommission_date": date(2023, 1, 1)
                },
                {
                    "name": "Bone Saw",
                    "device_type": Equipment.DEVICE_TYPE.hospital_industrial,
                    "department": Equipment.DEPARTMENT.orthopedic,
                    "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                    "model": "BONE-2021",
                    "manufacturer": "NeoTech Labs",
                    "serial_number": "SN100007",
                    "manufacturing_date": date(2018, 6, 1),
                    "description": "Surgical tool for orthopedic bone cutting.",
                    "supplier_name": "BioCare Systems",
                    "decommission_date": None
                },
                {
                    "name": "Chemotherapy Hood",
                    "device_type": Equipment.DEVICE_TYPE.safety_equipment,
                    "department": Equipment.DEPARTMENT.oncology,
                    "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                    "model": "CHEMO-HOOD",
                    "manufacturer": "SafeLife Equipment",
                    "serial_number": "SN100008",
                    "manufacturing_date": date(2021, 5, 5),
                    "description": "Protective hood for chemotherapy preparation.",
                    "supplier_name": "SafeLife Equipment",
                    "decommission_date": None
                },
                {
                    "name": "Anesthesia Machine",
                    "device_type": Equipment.DEVICE_TYPE.therapeutic,    # "therapeutic"
                    "department": Equipment.DEPARTMENT.surgical,         # "surgical"
                    "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                    "model": "ANES-202",
                    "manufacturer": "SurgiCare",
                    "serial_number": "SN200002",
                    "manufacturing_date": date(2020, 6, 11),
                    "description": "Therapeutic device for anesthesia delivery in surgery.",
                    "supplier_name": "SurgiPlus Corp",
                    "decommission_date": None
                },
                {
                    "name": "Ventilator",
                    "device_type": Equipment.DEVICE_TYPE.life_support,    # "life_support"
                    "department": Equipment.DEPARTMENT.icu,              # "icu"
                    "operational_status": Equipment.OPERATIONAL_STATUS.under_maintenance,
                    "model": "VENT-500",
                    "manufacturer": "RespiraTech",
                    "serial_number": "SN200003",
                    "manufacturing_date": date(2018, 2, 1),
                    "description": "Life-support device for mechanical ventilation in ICU.",
                    "supplier_name": "NeoTech Labs",
                    "decommission_date": None
                },
                {
                    "name": "Orthopedic Power Drill",
                    "device_type": Equipment.DEVICE_TYPE.other,
                    "department": Equipment.DEPARTMENT.orthopedic,
                    "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                    "model": "ORTHO-DRILL",
                    "manufacturer": "TechMed Innovations",
                    "serial_number": "SN100010",
                    "manufacturing_date": date(2019, 11, 20),
                    "description": "Other category device for orthopedic surgeries.",
                    "supplier_name": "NeoTech Labs",
                    "decommission_date": None
                },
                {
                "name": "MRI Machine",
                "device_type": Equipment.DEVICE_TYPE.diagnostic,  # "diagnostic"
                "department": Equipment.DEPARTMENT.radiology,     # "radiology"
                "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                "model": "MRI-2000",
                "manufacturer": "BrainScan Inc",
                "serial_number": "SN400001",
                "manufacturing_date": date(2017, 3, 10),
                "description": "Diagnostic imaging device for MRI scans.",
                "supplier_name": "Infinity MediSolutions",  # Example from your new supplier set
                "decommission_date": None
                },
                {
                    "name": "Ultrasound Scanner",
                    "device_type": Equipment.DEVICE_TYPE.diagnostic,  # "diagnostic"
                    "department": Equipment.DEPARTMENT.maternity,     # "maternity"
                    "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                    "model": "ULTR-700",
                    "manufacturer": "SonoTech",
                    "serial_number": "SN400002",
                    "manufacturing_date": date(2019, 2, 15),
                    "description": "Diagnostic imaging for prenatal care.",
                    "supplier_name": "Delta Labs",
                    "decommission_date": None
                },
                {
                    "name": "Defibrillator",
                    "device_type": Equipment.DEVICE_TYPE.life_support,  # "life_support"
                    "department": Equipment.DEPARTMENT.emergency,       # "emergency"
                    "operational_status": Equipment.OPERATIONAL_STATUS.under_maintenance,
                    "model": "DEF-100",
                    "manufacturer": "SafePulse",
                    "serial_number": "SN400003",
                    "manufacturing_date": date(2018, 9, 5),
                    "description": "Life support device for cardiac emergencies in the emergency department.",
                    "supplier_name": "eHeal Medical",
                    "decommission_date": None
                },
                {
                    "name": "Infusion Pump",
                    "device_type": Equipment.DEVICE_TYPE.monitoring,    # "monitoring"
                    "department": Equipment.DEPARTMENT.inpatient,       # "inpatient"
                    "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                    "model": "INF-505",
                    "manufacturer": "MediFlow",
                    "serial_number": "SN400004",
                    "manufacturing_date": date(2020, 1, 2),
                    "description": "Monitoring device for fluid infusion in inpatient wards.",
                    "supplier_name": "Helios Healthcare",
                    "decommission_date": None
                },
                {
                    "name": "Dental X-Ray",
                    "device_type": Equipment.DEVICE_TYPE.diagnostic,    # "diagnostic"
                    "department": Equipment.DEPARTMENT.dental,          # "dental"
                    "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                    "model": "DENT-XR",
                    "manufacturer": "XRayVision",
                    "serial_number": "SN400005",
                    "manufacturing_date": date(2016, 10, 30),
                    "description": "Diagnostic imaging device for dental radiology.",
                    "supplier_name": "Sphere Diagnostics",
                    "decommission_date": None
                },
                {
                    "name": "Pathogen Analyzer",
                    "device_type": Equipment.DEVICE_TYPE.lab,           # "lab"
                    "department": Equipment.DEPARTMENT.laboratory,      # "laboratory"
                    "operational_status": Equipment.OPERATIONAL_STATUS.non_functional,
                    "model": "PATH-777",
                    "manufacturer": "BioScan",
                    "serial_number": "SN400006",
                    "manufacturing_date": date(2015, 11, 20),
                    "description": "Lab device for analyzing pathogen cultures.",
                    "supplier_name": "Aviva Pharmaceuticals",
                    "decommission_date": None
                },
                {
                    "name": "Sterilizer",
                    "device_type": Equipment.DEVICE_TYPE.hospital_industrial,  # "hospital_industrial"
                    "department": Equipment.DEPARTMENT.surgical,               # "surgical"
                    "operational_status": Equipment.OPERATIONAL_STATUS.functional,
                    "model": "STER-CLN",
                    "manufacturer": "PureSteril",
                    "serial_number": "SN400007",
                    "manufacturing_date": date(2018, 3, 2),
                    "description": "Hospital-industrial equipment for sterilizing surgical instruments.",
                    "supplier_name": "Westpoint Biotech",
                    "decommission_date": None
                }  
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
