from django.urls import path
from . import views  

urlpatterns = [
    # Item Endpoints
    path('inventory-items/', views.ItemListCreateView.as_view(), name='item-list'),
    path('inventory-items/<int:pk>/', views.ItemDetailView.as_view(), name='item-detail'),
    
    path('inventory/total/', views.TotalInventoryView.as_view(), name='total-inventory'),

]
