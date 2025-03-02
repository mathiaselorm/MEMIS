import random
from faker import Faker
from django.core.management.base import BaseCommand
from inventory.models import Item
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError

fake = Faker()

class Command(BaseCommand):
    help = 'Populate the database with fake item data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--items', type=int, default=50, help='Number of items to create'
        )

    def handle(self, *args, **kwargs):
        items_count = kwargs['items']

        valid_categories = ['replacement', 'maintenance', 'critical', 'consumable']

        self.stdout.write(f'Generating {items_count} items...')
        for _ in range(items_count):
            quantity = random.randint(0, 20)
            item = Item(
                name=fake.word().capitalize(),
                item_code=fake.unique.ean(length=8),
                category=random.choice(valid_categories),
                description=fake.text(max_nb_chars=200),
                quantity=quantity,
                location=f"Cabinet {chr(random.randint(65, 90))}-{random.randint(1,20)}",
            )
            try:
                item.save()
                self.stdout.write(self.style.SUCCESS(f'Created item: {item.name}'))
            except ValidationError as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Validation error for item '{item.name}': {e.message_dict}"
                    )
                )
            except IntegrityError:
                self.stdout.write(
                    self.style.ERROR(
                        f"Item with code '{item.item_code}' already exists. Skipping."
                    )
                )

        self.stdout.write(self.style.SUCCESS('Database population complete!'))
