import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from accounts.models import CustomUser
from equipment.models import Equipment, EquipmentMaintenanceActivity

class Command(BaseCommand):
    help = (
        "Populates the database with a random number of maintenance records per equipment, "
        "using multiple templates, random date/time in [Jan 2025..Mar 2025], "
        "and ensuring no collisions (same equipment, same activity_type, same datetime)."
    )

    START_DATE = datetime(2025, 1, 1)
    # Fixed: Removed extra argument; now END_DATE uses microsecond=59
    END_DATE = datetime(2025, 3, 6, 11, 31, 23, 59)

    def add_arguments(self, parser):
        parser.add_argument(
            "--min-records",
            type=int,
            default=5,
            help="Minimum number of maintenance records per equipment (default=5).",
        )
        parser.add_argument(
            "--max-records",
            type=int,
            default=15,
            help="Maximum number of maintenance records per equipment (default=15).",
        )

    def handle(self, *args, **options):
        min_records = options["min_records"]
        max_records = options["max_records"]
        if min_records < 1 or max_records < min_records:
            self.stdout.write(self.style.ERROR(
                "Invalid min/max. --min-records must be >=1, and --max-records >= min-records."
            ))
            return

        # 1) Retrieve all users from the CustomUser table and use them as potential technicians.
        valid_techs = list(CustomUser.objects.all())
        if not valid_techs:
            self.stdout.write(self.style.ERROR("No users found in the CustomUser table. Aborting."))
            return

        # 2) Retrieve all equipment records.
        equipment_list = list(Equipment.objects.order_by("id"))
        if not equipment_list:
            self.stdout.write(self.style.ERROR("No equipment in the DB. Please create equipment first."))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Found {len(equipment_list)} equipment. Creating between {min_records} and {max_records} records per item."
            )
        )

        # 3) The activity templates.
        templates = [
            {
                "activity_type": "preventive maintenance",
                "post_status": None,
                "notes": "Scheduled preventive maintenance."
            },
            {
                "activity_type": "repair",
                "post_status": "functional",
                "notes": "Repaired device and restored functionality."
            },
            {
                "activity_type": "calibration",
                "post_status": "functional",
                "notes": "Calibrated device for better accuracy."
            },
            {
                "activity_type": "repair",
                "post_status": "non_functional",
                "notes": "Repair attempt failed; device is now non-functional."
            },
            {
                "activity_type": "repair",
                "post_status": "under_maintenance",
                "notes": "Awaiting spare parts; device is under maintenance."
            },
        ]

        # Helper: random datetime in [START_DATE..END_DATE], converted to an aware datetime.
        def random_aware_datetime():
            total_secs = int((self.END_DATE - self.START_DATE).total_seconds())
            rand_offset = random.randint(0, total_secs)
            naive_dt = self.START_DATE + timedelta(seconds=rand_offset)
            return timezone.make_aware(naive_dt, timezone.get_default_timezone())

        # Store used (activity_type, datetime) combos per equipment to avoid collisions.
        used_times_per_equipment = {}

        total_created = 0
        tech_index = 0

        with transaction.atomic():
            for eq in equipment_list:
                eq_id = eq.id
                used_times_per_equipment[eq_id] = set()

                records_for_this_equipment = random.randint(min_records, max_records)

                for _ in range(records_for_this_equipment):
                    # Randomly select a technician from all users.
                    assigned_tech = random.choice(valid_techs)

                    # Randomly pick a template.
                    tpl = random.choice(templates)

                    # Generate a random datetime, ensuring no collision for (activity_type, datetime)
                    while True:
                        dt_aware = random_aware_datetime()
                        dt_key = (tpl["activity_type"], dt_aware.strftime("%Y-%m-%d %H:%M:%S"))
                        if dt_key not in used_times_per_equipment[eq_id]:
                            used_times_per_equipment[eq_id].add(dt_key)
                            break

                    # Refresh equipment to get current operational_status.
                    eq.refresh_from_db()
                    pre_stat = eq.operational_status

                    activity = EquipmentMaintenanceActivity(
                        equipment=eq,
                        activity_type=tpl["activity_type"],
                        date_time=dt_aware,
                        technician=assigned_tech,
                        pre_status=pre_stat,
                        post_status=tpl["post_status"],
                        notes=tpl["notes"]
                    )
                    activity.save()

                    total_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Created {tpl['activity_type']} on '{eq.name}' | "
                            f"{dt_aware.strftime('%Y-%m-%d %H:%M')} | "
                            f"Tech={assigned_tech.email} | pre_status={pre_stat} "
                            f"| post_status={tpl['post_status'] or 'None'}"
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nAll done! Created {total_created} total maintenance activities across {len(equipment_list)} equipment."
            )
        )
