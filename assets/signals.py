from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify
from .models import Department, Asset, ActionLog, ActionType

@receiver(pre_save, sender=Department)
def create_department_slug(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = slugify(instance.name)

@receiver(pre_save, sender=Asset)
def log_asset_change(sender, instance, **kwargs):
    if instance._state.adding:
        # Action is 'create' when adding a new asset
        action = ActionType.CREATE
        changes = 'N/A'
    else:
        # Action is 'update' when modifying an existing asset
        action = ActionType.UPDATE
        dirty_fields = instance.get_dirty_fields()
        changes = ', '.join([f"{field}: {dirty_fields[field]}" for field in dirty_fields])

    # Log the action
    ActionLog.objects.create(
        asset=instance,
        action=action,
        performed_by=instance.added_by,
        reason=f"Asset {action.lower()} with changes: {changes if action == ActionType.UPDATE else 'N/A'}"
    )
