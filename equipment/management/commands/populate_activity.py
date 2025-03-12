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
        "using multiple templates, random date/time in [Nov 2024..Mar 2025], "
        "and ensuring no collisions (same eq, same activity_type, same datetime)."
    )

    START_DATE = datetime(2024, 11, 1)
    END_DATE = datetime(2025, 3, 31, 23, 59, 59)

    def add_arguments(self, parser):
        parser.add_argument(
            "--min-records",
            type=int,
            default=5,
            help="Minimum number of maintenance records per equipment (default=2).",
        )
        parser.add_argument(
            "--max-records",
            type=int,
            default=15,
            help="Maximum number of maintenance records per equipment (default=6).",
        )

    def handle(self, *args, **options):
        min_records = options["min_records"]
        max_records = options["max_records"]
        if min_records < 1 or max_records < min_records:
            self.stdout.write(self.style.ERROR(
                "Invalid min/max. --min-records must be >=1, and --max-records >= min-records."
            ))
            return

        # 1) Gather possible technicians
        tech_emails = ["mathiaselorm@gmail.com", "memisproject@gmail.com", "memis@gmail.com"]
        technicians = []
        for email in tech_emails:
            try:
                user_obj = CustomUser.objects.get(email=email)
                technicians.append(user_obj)
            except CustomUser.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f"Technician user '{email}' not found. Skipping."
                ))
        valid_techs = [t for t in technicians if t]
        if not valid_techs:
            self.stdout.write(self.style.ERROR(
                "No valid technicians found among the three emails. Aborting."
            ))
            return

        # 2) Retrieve all equipment
        equipment_list = list(Equipment.objects.order_by("id"))
        if not equipment_list:
            self.stdout.write(self.style.ERROR("No equipment in the DB. Please create equipment first."))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Found {len(equipment_list)} equipment. Creating between {min_records} and {max_records} records per item."
            )
        )

        # 3) The activity templates
        #    We'll randomly pick from these templates for each record
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

        # Helper: random datetime in [START_DATE..END_DATE], made "aware"
        def random_aware_datetime():
            total_secs = int((self.END_DATE - self.START_DATE).total_seconds())
            rand_offset = random.randint(0, total_secs)
            naive_dt = self.START_DATE + timedelta(seconds=rand_offset)
            # Convert to aware datetime using the default time zone
            return timezone.make_aware(naive_dt, timezone.get_default_timezone())

        # We'll store used combos (activity_type, dt_str) per equipment
        used_times_per_equipment = {}

        tech_index = 0
        total_created = 0

        with transaction.atomic():
            for eq in equipment_list:
                eq_id = eq.id
                used_times_per_equipment[eq_id] = set()

                # Decide how many records for this equipment
                records_for_this_equipment = random.randint(min_records, max_records)

                for _ in range(records_for_this_equipment):
                    # Round robin for technician
                    assigned_tech = valid_techs[tech_index % len(valid_techs)]
                    tech_index += 1

                    # Randomly pick a template
                    tpl = random.choice(templates)

                    # We generate random date_time, ensuring no collision for (activity_type, date_time)
                    while True:
                        dt_aware = random_aware_datetime()
                        dt_key = (tpl["activity_type"], dt_aware.strftime("%Y-%m-%d %H:%M:%S"))
                        if dt_key not in used_times_per_equipment[eq_id]:
                            used_times_per_equipment[eq_id].add(dt_key)
                            break
                        # else generate again

                    # Refresh eq so we see any updated operational_status from prior loop
                    eq.refresh_from_db()
                    pre_stat = eq.operational_status

                    # Create the activity
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
