from django.db import models
from django.contrib.auth import get_user_model
from model_utils.models import TimeStampedModel

User = get_user_model()


        
class Notification(TimeStampedModel):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    message = models.TextField(blank=True, null=True)
    link = models.URLField(blank=True, null=True)  # Link to related details
    is_read = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return f"Notification for {self.user.first_name}"