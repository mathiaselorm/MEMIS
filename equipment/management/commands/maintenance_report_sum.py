import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from equipment.models import EquipmentMaintenanceActivity

class Command(BaseCommand):
    help = (
        "For each day with maintenance activities, check for each required activity type. "
        "If an activity type has zero records for that day, then with 50% probability, "
        "boost the count by creating duplicate records so that the final count is randomized "
        "between 2 and 10. Otherwise, leave that activity type at zero."
    )

    def handle(self, *args, **options):
        # Define the required activity types.
        required_types = ["preventive maintenance", "repair", "calibration"]
        # Set probability for boosting a missing type (0.5 means 50% chance).
        boost_probability = 0.5

        # Retrieve all maintenance activities.
        all_activities = list(EquipmentMaintenanceActivity.objects.all())
        if not all_activities:
            self.stdout.write(self.style.ERROR("No maintenance activities found in the database."))
            return

        # Group activities by the date portion of date_time.
        groups = {}
        for activity in all_activities:
            day = activity.date_time.date()
            groups.setdefault(day, []).append(activity)

        total_added = 0

        with transaction.atomic():
            for day, activities in groups.items():
                # Count the number of activities per required type.
                counts = {atype: 0 for atype in required_types}
                for act in activities:
                    if act.activity_type in counts:
                        counts[act.activity_type] += 1

                # For each required type that is missing (zero count)
                for atype in required_types:
                    if counts[atype] == 0:
                        # Decide with a probability whether to boost this type.
                        if random.random() < boost_probability:
                            # Randomly choose a target count between 2 and 10.
                            target_count = random.randint(2, 10)
                            self.stdout.write(self.style.SUCCESS(
                                f"Day {day}: missing '{atype}' boosted to {target_count} records."
                            ))
                            for _ in range(target_count):
                                # Pick an existing record from the same day as base.
                                base_activity = random.choice(activities)
                                # Add a random offset (0 to 300 seconds) so that the new record falls on the same day.
                                offset = timedelta(seconds=random.randint(0, 300))
                                naive_dt = datetime.combine(day, base_activity.date_time.time())
                                new_date_time = timezone.make_aware(naive_dt, timezone.get_default_timezone()) + offset

                                new_activity = EquipmentMaintenanceActivity(
                                    equipment=base_activity.equipment,
                                    activity_type=atype,
                                    date_time=new_date_time,
                                    technician=base_activity.technician,
                                    pre_status=base_activity.pre_status,
                                    post_status=base_activity.post_status,
                                    notes=(base_activity.notes or "") + " [boost duplicate]"
                                )
                                new_activity.save()
                                total_added += 1
                                activities.append(new_activity)  # Append to group's list.
                        else:
                            self.stdout.write(f"Day {day}: missing '{atype}' left at zero.")
        self.stdout.write(self.style.SUCCESS(
            f"\nSuccessfully added {total_added} duplicate maintenance activity records for boosting missing types."
        ))








# import random
# from datetime import datetime, timedelta
# from django.core.management.base import BaseCommand
# from django.db import transaction
# from django.utils import timezone
# from equipment.models import EquipmentMaintenanceActivity

# class Command(BaseCommand):
#     help = (
#         "For each day with maintenance activities, add duplicates so that the final count "
#         "for that day is a random number between 0 and 20. This simulates higher activity figures "
#         "for testing the maintenance overview reports."
#     )

#     def handle(self, *args, **options):
#         # Fetch all maintenance activities.
#         all_activities = list(EquipmentMaintenanceActivity.objects.all())
#         if not all_activities:
#             self.stdout.write(self.style.ERROR("No maintenance activities found in the database."))
#             return

#         # Group activities by the date part of their date_time.
#         groups = {}
#         for activity in all_activities:
#             day = activity.date_time.date()
#             groups.setdefault(day, []).append(activity)

#         total_added = 0

#         with transaction.atomic():
#             for day, activities in groups.items():
#                 current_count = len(activities)
#                 # Choose a random target count between 0 and 20 for this day.
#                 target_count = random.randint(0, 20)
#                 if current_count < target_count:
#                     to_add = target_count - current_count
#                     self.stdout.write(self.style.SUCCESS(
#                         f"Day {day}: current count = {current_count}, target = {target_count}. Adding {to_add} records."
#                     ))
#                     for _ in range(to_add):
#                         # Pick one existing activity randomly from this day to duplicate.
#                         base_activity = random.choice(activities)
#                         # Add a small random offset (0 to 300 seconds) so the new record falls on the same day.
#                         offset = timedelta(seconds=random.randint(0, 300))
#                         # Construct a new datetime that remains within the same day.
#                         new_date_time = timezone.make_aware(
#                             datetime.combine(day, base_activity.date_time.time())
#                         ) + offset
#                         # Create a duplicate of the activity with the same field values,
#                         # but add a note that this record is a duplicate.
#                         new_activity = EquipmentMaintenanceActivity(
#                             equipment=base_activity.equipment,
#                             activity_type=base_activity.activity_type,
#                             date_time=new_date_time,
#                             technician=base_activity.technician,
#                             pre_status=base_activity.pre_status,
#                             post_status=base_activity.post_status,
#                             notes=base_activity.notes + " [duplicate]"
#                         )
#                         new_activity.save()
#                         total_added += 1
#                         # Also append to the group's list so further duplicates can be made if needed.
#                         activities.append(new_activity)

#         self.stdout.write(self.style.SUCCESS(
#             f"\nSuccessfully added {total_added} duplicate maintenance activity records."
#         ))
