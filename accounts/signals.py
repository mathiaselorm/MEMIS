from django.db.models.signals import post_save, post_delete
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .models import CustomUser, AuditLog


@receiver(post_save, sender=CustomUser)
def log_user_create_update(sender, instance, created, **kwargs):
    """
    Logs the creation or update of a user.
    """
    action = 'create' if created else 'update'

    # Only log actions for admins or superusers
    if instance.user_role == CustomUser.UseRole.ADMIN or instance.is_superuser:
        AuditLog.objects.create(
            user=instance,  # The admin performing the action
            action=action,
            target_user=instance,  # The user being created or updated
            details=f'User {action}d: {instance.first_name}'
        )


@receiver(post_delete, sender=CustomUser)
def log_user_delete(sender, instance, **kwargs):
    """
    Logs the deletion of a user.
    """
    # Only log actions for admins or superusers
    if instance.user_role == CustomUser.UseRole.ADMIN or instance.is_superuser:
        AuditLog.objects.create(
            user=instance,  # The admin performing the action
            action='delete',
            target_user=instance,  # The user being deleted
            details=f'User deleted: {instance.first_name}'
        )


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """
    Logs the login action of a user.
    """
    AuditLog.objects.create(
        user=user,
        action='login',
        target_user=user,
        details=f'User logged in: {user.first_name}'
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """
    Logs the logout action of a user.
    """
    AuditLog.objects.create(
        user=user,
        action='logout',
        target_user=user,
        details=f'User logged out: {user.first_name}'
    )


def log_role_assignment(admin_user, target_user, new_role):
    """
    Custom function to log role assignment by an admin.
    """
    previous_role = target_user.get_user_role_display()
    target_user.user_role = new_role
    target_user.save()

    # Log the role assignment action
    AuditLog.objects.create(
        user=admin_user,  # The admin assigning the role
        action='assign_role',
        target_user=target_user,
        details=f'Role changed from {previous_role} to {target_user.get_user_role_display()} for user {target_user.username}'
    )


def log_role_revocation(admin_user, target_user, old_role):
    """
    Custom function to log role revocation by an admin.
    """
    previous_role = target_user.get_user_role_display()
    target_user.user_role = old_role
    target_user.save()

    # Log the role revocation action
    AuditLog.objects.create(
        user=admin_user,  # The admin revoking the role
        action='revoke_role',
        target_user=target_user,
        details=f'Role changed from {previous_role} for user {target_user.username}'
    )
