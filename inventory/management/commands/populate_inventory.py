from django.core.management.base import BaseCommand
from inventory.models import Item
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError

class Command(BaseCommand):
    help = 'Populate the database with meaningful inventory items'

    def handle(self, *args, **kwargs):
        # Predefined list of meaningful inventory items
        inventory_items = [
            {
                "name": "Replacement Battery for Ultrasound",
                "item_code": "RB-US-001",
                "category": "replacement",
                "description": "Battery replacement for portable ultrasound machines ensuring continuous operation.",
                "quantity": 15,
                "location": "Storage Room A - Shelf 1",
            },
            {
                "name": "Maintenance Toolkit for X-Ray Machines",
                "item_code": "MT-XR-001",
                "category": "maintenance",
                "description": "Comprehensive toolkit for routine maintenance of X-ray machines.",
                "quantity": 5,
                "location": "Maintenance Department - Cabinet 2",
            },
            {
                "name": "Critical Component - Infusion Pump Motor",
                "item_code": "CC-IP-001",
                "category": "critical",
                "description": "Essential spare motor required for infusion pump functionality.",
                "quantity": 3,
                "location": "Central Warehouse - Shelf 3",
            },
            {
                "name": "Consumable - Disposable Syringe",
                "item_code": "CON-SY-001",
                "category": "consumable",
                "description": "Disposable syringe used in various infusion procedures to ensure sterility.",
                "quantity": 200,
                "location": "Pharmacy Storage - Shelf 4",
            },
            {
                "name": "Replacement Filter for Ventilators",
                "item_code": "RB-VN-002",
                "category": "replacement",
                "description": "High-efficiency filter replacement for ventilators, critical for patient safety.",
                "quantity": 10,
                "location": "Ventilator Maintenance Room - Shelf 1",
            },
            {
                "name": "Maintenance Diagnostic Tool for MRI",
                "item_code": "MT-MRI-002",
                "category": "maintenance",
                "description": "Diagnostic tool kit used for troubleshooting MRI machine issues.",
                "quantity": 2,
                "location": "Radiology Department - Storage 3",
            },
            {
                "name": "Critical Component - ECG Lead Set",
                "item_code": "CC-ECG-003",
                "category": "critical",
                "description": "Spare set of ECG leads required for immediate replacement to avoid downtime.",
                "quantity": 8,
                "location": "Cardiology Department - Supply Closet",
            },
            {
                "name": "Consumable - Surgical Gloves",
                "item_code": "CON-SG-004",
                "category": "consumable",
                "description": "Sterile surgical gloves, an essential consumable for all surgical procedures.",
                "quantity": 500,
                "location": "Operating Room - Storage Cabinet",
            },
            # Additional items
            {
                "name": "Replacement Circuit Board for Ultrasound",
                "item_code": "RB-US-005",
                "category": "replacement",
                "description": "Circuit board replacement for ultrasound devices to ensure proper signal processing.",
                "quantity": 7,
                "location": "Electronics Storage - Shelf 2",
            },
            {
                "name": "Maintenance Calibration Kit for Blood Analyzers",
                "item_code": "MT-BA-003",
                "category": "maintenance",
                "description": "Calibration kit to maintain accuracy in blood analyzer readings.",
                "quantity": 4,
                "location": "Lab Supplies - Cabinet 1",
            },
            {
                "name": "Critical Component - Defibrillator Battery",
                "item_code": "CC-DF-004",
                "category": "critical",
                "description": "Battery essential for defibrillators to ensure they operate during emergencies.",
                "quantity": 5,
                "location": "Emergency Storage - Shelf 1",
            },
            {
                "name": "Consumable - Surgical Masks",
                "item_code": "CON-SM-005",
                "category": "consumable",
                "description": "Disposable surgical masks to maintain a sterile environment in operating rooms.",
                "quantity": 1000,
                "location": "Operating Room - Supply Closet",
            },
            {
                "name": "Replacement Cable for ECG Monitor",
                "item_code": "RB-EC-006",
                "category": "replacement",
                "description": "Replacement cable ensuring reliable connectivity for ECG monitors.",
                "quantity": 20,
                "location": "Cardiology Dept. - Equipment Room",
            },
            {
                "name": "Maintenance Wrench Set for Surgical Equipment",
                "item_code": "MT-SE-007",
                "category": "maintenance",
                "description": "Wrench set designed for routine maintenance and adjustments of surgical equipment.",
                "quantity": 3,
                "location": "Surgical Supplies - Tool Cabinet",
            },
            {
                "name": "Critical Component - Ventilator Sensor",
                "item_code": "CC-VS-008",
                "category": "critical",
                "description": "Sensor critical to the proper function of ventilators, ensuring accurate monitoring.",
                "quantity": 6,
                "location": "Respiratory Dept. - Storage Box",
            },
            {
                "name": "Consumable - Antiseptic Wipes",
                "item_code": "CON-AW-009",
                "category": "consumable",
                "description": "Antiseptic wipes used for sanitizing equipment and surfaces in clinical settings.",
                "quantity": 300,
                "location": "Pharmacy - Aisle 2",
            },
            {
                "name": "ECG Electrode Pads (Box of 50)",
                "item_code": "INV-ECG-001",
                "category": "consumable",
                "description": "Disposable electrode pads for ECG machines ensuring accurate signal acquisition.",
                "quantity": 50,
                "location": "Cardiology Supply Room"
            },
            {
                "name": "Defibrillator Battery Pack",
                "item_code": "INV-DEF-001",
                "category": "critical",
                "description": "Replacement battery pack for defibrillators; critical for cardiac emergency operations.",
                "quantity": 2,
                "location": "Critical Components Storage"
            },
            {
                "name": "Ultrasound Probe Transducer",
                "item_code": "INV-US-001",
                "category": "replacement",
                "description": "High-resolution transducer for portable ultrasound machines used in diagnostic imaging.",
                "quantity": 3,
                "location": "Imaging Department Storage"
            },
            {
                "name": "Sterilization Tray",
                "item_code": "INV-STER-001",
                "category": "maintenance",
                "description": "Stainless steel tray for holding surgical instruments during sterilization cycles.",
                "quantity": 10,
                "location": "Surgical Equipment Room"
            },
            {
                "name": "Infusion Pump Circuit Set",
                "item_code": "INV-INF-001",
                "category": "consumable",
                "description": "Disposable circuit sets for infusion pumps ensuring sterile fluid delivery.",
                "quantity": 25,
                "location": "Inpatient Supplies"
            },
            {
                "name": "Ventilator Filter Cartridge",
                "item_code": "INV-VEN-001",
                "category": "replacement",
                "description": "High-efficiency filter cartridge for ventilators to maintain clean airflow.",
                "quantity": 8,
                "location": "ICU Equipment Storage"
            },
            {
                "name": "Disposable Surgical Gloves (Box of 100)",
                "item_code": "INV-GLOVES-001",
                "category": "consumable",
                "description": "Sterile, disposable surgical gloves for maintaining aseptic conditions in the OR.",
                "quantity": 50,
                "location": "Operating Room Supplies"
            },
             {
                "name": "Respiratory Filter for Ventilator",
                "item_code": "INV-RESP-001",
                "category": "replacement",
                "description": "High-efficiency respiratory filter for ventilators to maintain optimal air quality.",
                "quantity": 7,
                "location": "ICU Supplies Storage"
            },
        ]

        self.stdout.write('Populating inventory items...')
        for data in inventory_items:
            try:
                item = Item.objects.create(
                    name=data["name"],
                    item_code=data["item_code"],
                    category=data["category"],
                    description=data["description"],
                    quantity=data["quantity"],
                    location=data["location"],
                )
                self.stdout.write(self.style.SUCCESS(f'Created item: {item.name}'))
            except ValidationError as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Validation error for item '{data['name']}': {e.message_dict}"
                    )
                )
            except IntegrityError:
                self.stdout.write(
                    self.style.ERROR(
                        f"Item with code '{data['item_code']}' already exists. Skipping."
                    )
                )

        self.stdout.write(self.style.SUCCESS('Inventory items populated successfully!'))
