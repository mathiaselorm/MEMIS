from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import CustomUser

class Command(BaseCommand):
    help = "Create a predefined set of user records in the database (no randomness)."

    def handle(self, *args, **options):
        predefined_users = [
            {
                "first_name": "Alice",
                "last_name": "Johnson",
                "email": "alice.johnson@example.com",
                "phone_number": "123-456-7890",
                "user_role": CustomUser.UserRole.TECHNICIAN,
                "password": "password123",
            },
            {
                "first_name": "Bob",
                "last_name": "Smith",
                "email": "bob.smith@example.com",
                "phone_number": "234-567-8901",
                "user_role": CustomUser.UserRole.ADMIN,
                "password": "password123",
            },
            {
                "first_name": "Carol",
                "last_name": "Williams",
                "email": "carol.williams@example.com",
                "phone_number": "345-678-9012",
                "user_role": CustomUser.UserRole.ADMIN,
                "password": "password123",
            },
            {
                "first_name": "David",
                "last_name": "Brown",
                "email": "david.brown@example.com",
                "phone_number": "456-789-0123",
                "user_role": CustomUser.UserRole.TECHNICIAN,
                "password": "password123",
            },
            {
                "first_name": "Eve",
                "last_name": "Jones",
                "email": "eve.jones@example.com",
                "phone_number": "567-890-1234",
                "user_role": CustomUser.UserRole.TECHNICIAN,
                "password": "password123",
            },
            {
                "first_name": "Frank",
                "last_name": "Miller",
                "email": "frank.miller@example.com",
                "phone_number": "678-901-2345",
                "user_role": CustomUser.UserRole.TECHNICIAN,
                "password": "password123",
            },
            {
                "first_name": "Grace",
                "last_name": "Davis",
                "email": "grace.davis@example.com",
                "phone_number": "789-012-3456",
                "user_role": CustomUser.UserRole.ADMIN,
                "password": "password123",
            },
            {
                "first_name": "Heidi",
                "last_name": "Wilson",
                "email": "heidi.wilson@example.com",
                "phone_number": "890-123-4567",
                "user_role": CustomUser.UserRole.TECHNICIAN,
                "password": "password123",
            },
            {
                "first_name": "Ivan",
                "last_name": "Moore",
                "email": "ivan.moore@example.com",
                "phone_number": "901-234-5678",
                "user_role": CustomUser.UserRole.ADMIN,
                "password": "password123",
            },
            {
                "first_name": "Judy",
                "last_name": "Taylor",
                "email": "judy.taylor@example.com",
                "phone_number": "012-345-6789",
                "user_role": CustomUser.UserRole.TECHNICIAN,
                "password": "password123",
            },
        ]

        with transaction.atomic():
            for user_data in predefined_users:
                email = user_data["email"]
                user, created = CustomUser.objects.get_or_create(
                    email=email,
                    defaults={
                        "first_name": user_data["first_name"],
                        "last_name": user_data["last_name"],
                        "phone_number": user_data["phone_number"],
                        "user_role": user_data["user_role"],
                    }
                )
                if created:
                    if user_data.get("password"):
                        user.set_password(user_data["password"])
                        user.save()
                    self.stdout.write(self.style.SUCCESS(f"Created user '{email}'"))
                else:
                    self.stdout.write(f"User '{email}' already exists, skipped creation.")
        self.stdout.write(self.style.SUCCESS("Finished creating users!"))
