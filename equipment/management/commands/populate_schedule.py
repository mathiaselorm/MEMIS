import random
import calendar
from datetime import datetime, timedelta, date, time
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from equipment.models import MaintenanceSchedule, Equipment
from accounts.models import CustomUser

class Command(BaseCommand):
    help = (
        "Populate the MaintenanceSchedule table with meaningful data. "
        "For each month in the current year, create between 4 and 10 maintenance schedules, "
        "ensuring at least one schedule is recurring (frequency != 'once')."
    )

    def handle(self, *args, **options):
        current_year = timezone.now().year

        # Fetch equipment from DB (must exist)
        equipment_qs = list(Equipment.objects.all())
        if not equipment_qs:
            self.stdout.write(self.style.ERROR("No equipment found. Create equipment first."))
            return

        # Get a list of valid technician users using a predefined list of emails.
        tech_emails = ["mathiaselorm@gmail.com", "memisproject@gmail.com", "memis@gmail.com"]
        technicians = []
        for email in tech_emails:
            try:
                user = CustomUser.objects.get(email=email)
                technicians.append(user)
            except CustomUser.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Technician {email} not found."))
        if not technicians:
            self.stdout.write(self.style.ERROR("No valid technicians found. Aborting."))
            return

        # Define possible activity types for the schedule (from the MaintenanceSchedule model)
        # You can use the same activity choices as in EquipmentMaintenanceActivity.
        activity_types = ["preventive maintenance", "repair", "calibration"]
        # Define recurring frequency options
        recurring_options = ['daily', 'weekly', 'biweekly', 'monthly']

        total_created = 0

        with transaction.atomic():
            # Iterate over each month (1 to 12) in the current year.
            for month in range(1, 13):
                # Get number of days in the month.
                _, last_day = calendar.monthrange(current_year, month)
                # Determine number of schedules to create for this month.
                num_schedules = random.randint(4, 10)
                self.stdout.write(self.style.SUCCESS(
                    f"Month {calendar.month_name[month]} {current_year}: Creating {num_schedules} schedules."
                ))
                # List to hold schedules created for this month.
                month_schedules = []

                for _ in range(num_schedules):
                    # Generate a random day and time within this month.
                    day = random.randint(1, last_day)
                    # Random time for start_date.
                    random_hour = random.randint(0, 23)
                    random_minute = random.randint(0, 59)
                    random_second = random.randint(0, 59)
                    start_dt_naive = datetime(current_year, month, day, random_hour, random_minute, random_second)
                    start_dt = timezone.make_aware(start_dt_naive, timezone.get_default_timezone())
                    
                    # End date: add a random 1 to 4 hours after start.
                    end_dt = start_dt + timedelta(hours=random.randint(1, 4))
                    
                    # Randomly pick an activity type.
                    activity_type = random.choice(activity_types)
                    
                    # Decide frequency: 70% chance one-time ("once"), 30% chance recurring.
                    if random.random() < 0.7:
                        frequency = 'once'
                        interval = 1
                        recurring_end = None
                    else:
                        frequency = random.choice(recurring_options)
                        interval = 2 if frequency == 'biweekly' else random.randint(1, 4)
                        # Set recurring_end: random extra days, ensuring it does not go beyond the month.
                        max_extra = last_day - day
                        # Ensure at least 7 days difference if possible.
                        if max_extra < 7:
                            extra_days = max_extra if max_extra > 0 else 1
                        else:
                            extra_days = random.randint(7, max_extra)
                        recurring_end = start_dt + timedelta(days=extra_days)
                    
                    # Randomly decide if schedule applies to all equipment (50% chance).
                    if random.random() < 0.5:
                        for_all_equipment = True
                        equipment_instance = None
                    else:
                        for_all_equipment = False
                        equipment_instance = random.choice(equipment_qs)
                    
                    # Choose a technician at random.
                    technician = random.choice(technicians)
                    
                    # Create title and description.
                    if for_all_equipment:
                        title = f"General {activity_type.capitalize()} Schedule - {calendar.month_name[month]}"
                    else:
                        title = f"{activity_type.capitalize()} Schedule for {equipment_instance.name}"
                    description = f"Scheduled {activity_type} maintenance for {calendar.month_name[month]} {current_year}."
                    
                    schedule = MaintenanceSchedule(
                        activity_type=activity_type,
                        for_all_equipment=for_all_equipment,
                        equipment=equipment_instance,
                        technician=technician,
                        title=title,
                        description=description,
                        start_date=start_dt,
                        end_date=end_dt,
                        frequency=frequency,
                        interval=interval,
                        recurring_end=recurring_end
                    )
                    schedule.save()
                    month_schedules.append(schedule)
                    total_created += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"Created: {schedule.title} | Frequency: {schedule.frequency} | Start: {start_dt.strftime('%Y-%m-%d %H:%M')}"
                    ))
                
                # Ensure at least one recurring schedule exists for the month.
                recurring_exists = any(s.frequency != 'once' for s in month_schedules)
                if not recurring_exists and month_schedules:
                    # Pick one schedule and update it to be recurring.
                    schedule = random.choice(month_schedules)
                    schedule.frequency = random.choice(recurring_options)
                    schedule.interval = 2 if schedule.frequency == 'biweekly' else random.randint(1, 4)
                    # Set recurring_end to at least 7 days after start_date, but not exceeding month-end.
                    day = schedule.start_date.day
                    max_extra = last_day - day
                    extra_days = random.randint(7, max_extra if max_extra >= 7 else max_extra + 7)
                    schedule.recurring_end = schedule.start_date + timedelta(days=extra_days)
                    schedule.save()
                    self.stdout.write(self.style.SUCCESS(
                        f"Updated '{schedule.title}' to recurring for {calendar.month_name[month]}."
                    ))
                    
        self.stdout.write(self.style.SUCCESS(
            f"\nSuccessfully created {total_created} maintenance schedule records for the year {current_year}."
        ))
