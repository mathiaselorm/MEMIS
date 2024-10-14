from django.urls import path
from . import views  

urlpatterns = [
    # Category Endpoints
    path('categories/', views.CategoryList.as_view(), name='category-list'),
    path('categories/<str:identifier>/', views.CategoryDetail.as_view(), name='category-detail'),
    
    # Category Items Endpoints
    path('categories/<str:identifier>/items/', views.CategoryItemsList.as_view(), name='category-items'),

    # Supplier Endpoints
    path('suppliers/', views.SupplierList.as_view(), name='supplier-list'),
    path('suppliers/<int:pk>/', views.SupplierDetail.as_view(), name='supplier-detail'),
    
    # Item Endpoints
    path('items/', views.ItemList.as_view(), name='item-list'),
    path('items/<int:pk>/', views.ItemDetail.as_view(), name='item-detail'),
]
