from django import forms
from .models import Department

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'slug', 'head', 'contact_phone', 'contact_email', 'status', 'is_removed']
