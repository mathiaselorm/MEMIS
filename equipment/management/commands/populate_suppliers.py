from django.core.management.base import BaseCommand
from django.db import transaction
from equipment.models import Supplier

class Command(BaseCommand):
    help = "Create a predefined set of supplier records in the database (no randomness)."

    def handle(self, *args, **options):
        predefined_suppliers = [
            {
                "company_name": "MediHealth Inc",
                "company_email": "contact@medihealth.example.com",
                "contact": "123-456-7890",
                "website": "https://www.medihealth.example.com"
            },
            {
                "company_name": "SurgiPlus Corp",
                "company_email": "info@surgiplus.example.com",
                "contact": "555-123-4567",
                "website": "https://www.surgiplus.example.com"
            },
            {
                "company_name": "BioCare Systems",
                "company_email": "support@biocare.example.com",
                "contact": "789-101-1122",
                "website": "https://www.biocare.example.com"
            },
            {
                "company_name": "NeoTech Labs",
                "company_email": "service@neotech.example.com",
                "contact": "111-222-3333",
                "website": "https://www.neotech.example.com"
            },
            {
                "company_name": "GlobalMed Devices",
                "company_email": "sales@globalmed.example.com",
                "contact": "444-555-6666",
                "website": "https://www.globalmed.example.com"
            },
            {
                "company_name": "OmniHealth Solutions",
                "company_email": "support@omnihealth.example.com",
                "contact": "101-202-3030",
                "website": "https://www.omnihealth.example.com"
            },
            {
                "company_name": "VitalCare Supplies",
                "company_email": "contact@vitalcare.example.com",
                "contact": "555-777-8888",
                "website": "https://www.vitalcare.example.com"
            },
            {
                "company_name": "TechMed Innovations",
                "company_email": "info@techmed.example.com",
                "contact": "999-000-1111",
                "website": "https://www.techmed.example.com"
            },
            {
                "company_name": "SafeLife Equipment",
                "company_email": "sales@safelife.example.com",
                "contact": "888-999-0000",
                "website": "https://www.safelife.example.com"
            },
            {
                "company_name": "FutureLine Medical",
                "company_email": "connect@futureline.example.com",
                "contact": "222-333-4444",
                "website": "https://www.futureline.example.com"
            },
        ]

        with transaction.atomic():
            for supplier_data in predefined_suppliers:
                company_name = supplier_data["company_name"]
                supplier, created = Supplier.objects.get_or_create(
                    company_name=company_name,
                    defaults={
                        "company_email": supplier_data["company_email"],
                        "contact": supplier_data["contact"],
                        "website": supplier_data["website"],
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created supplier '{company_name}'"))
                else:
                    self.stdout.write(f"Supplier '{company_name}' already exists, skipped creation.")
        self.stdout.write(self.style.SUCCESS("Finished creating suppliers!"))
