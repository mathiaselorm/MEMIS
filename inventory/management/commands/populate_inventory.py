import random
from faker import Faker
from django.core.management.base import BaseCommand
from inventory.models import Category, Supplier, Item
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError

fake = Faker()

class Command(BaseCommand):
    help = 'Populate the database with fake data'

    def add_arguments(self, parser):
        parser.add_argument('--categories', type=int, default=10, help='Number of categories to create')
        parser.add_argument('--suppliers', type=int, default=10, help='Number of suppliers to create')
        parser.add_argument('--items', type=int, default=50, help='Number of items to create')

    def handle(self, *args, **kwargs):
        categories_count = kwargs['categories']
        suppliers_count = kwargs['suppliers']
        items_count = kwargs['items']

        self.stdout.write(f'Generating {categories_count} categories...')
        categories = []
        for _ in range(categories_count):
            category_name = fake.unique.word().capitalize()
            try:
                category = Category.objects.create(
                    name=category_name,
                    description=fake.text(max_nb_chars=200)
                )
                categories.append(category)
            except IntegrityError:
                self.stdout.write(self.style.ERROR(f'Category with name "{category_name}" already exists. Skipping.'))
                continue

        self.stdout.write(f'Generating {suppliers_count} suppliers...')
        suppliers = []
        for _ in range(suppliers_count):
            supplier = Supplier.objects.create(
                name=fake.company(),
                contact_info=f"{fake.phone_number()} - {fake.email()}"
            )
            suppliers.append(supplier)

        self.stdout.write(f'Generating {items_count} items...')
        for _ in range(items_count):
            current_stock = random.randint(0, 100)
            reorder_threshold = random.randint(0, min(20, current_stock))  # Ensure reorder_threshold <= current_stock

            item = Item(
                descriptive_name=fake.word().capitalize(),
                batch_number=fake.unique.ean(length=8),
                current_stock=current_stock,
                reorder_threshold=reorder_threshold,
                location=fake.city(),
                category=random.choice(categories),
                supplier=random.choice(suppliers)
            )
            try:
                item.save()
                self.stdout.write(self.style.SUCCESS(f'Created item: {item.descriptive_name}'))
            except ValidationError as e:
                self.stdout.write(self.style.ERROR(f"Validation error for item '{item.descriptive_name}': {e.message_dict}"))
            except IntegrityError:
                self.stdout.write(self.style.ERROR(f"Item with batch number '{item.batch_number}' already exists. Skipping."))

        self.stdout.write(self.style.SUCCESS('Database population complete!'))
