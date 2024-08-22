from django.core.management.base import BaseCommand
from faker import Faker
from accounts.models import CustomUser

class Command(BaseCommand):
    help = 'Populates the database with fake data'

    def handle(self, *args, **options):
        fake = Faker()
        for _ in range(5):  # Number of instances you want to create
            # Assuming full_name and phone_number are correct field names
            # Ensure phone_number and other methods are correctly used
            while True:
                email = fake.email()
                if not CustomUser.objects.filter(email=email).exists():
                    break
            
            CustomUser.objects.create(
                email=email,
                full_name=fake.name(),
                phone_number=fake.phone_number(),  # Correct method to generate phone numbers
                # Add other fields as necessary, ensure all required fields are included
            )
        self.stdout.write(self.style.SUCCESS('Successfully populated database with fake data'))
