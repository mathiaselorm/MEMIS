
from django.urls import path
from . import views


urlpatterns = [
    path('activity-stream/', views.ActivityStreamView.as_view(), name='activity-stream'),
]
