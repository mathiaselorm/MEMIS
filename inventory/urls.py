from django.urls import path
from . import views  

urlpatterns = [
    path('categories/', views.CategoryList.as_view(), name='category-list'),
    path('categories/<str:identifier>/', views.CategoryDetail.as_view(), name='category-detail'),
    
    path('categories/<str:identifier>/items/', views.CategoryItemsList.as_view(), name='category-items'),

    
    path('suppliers/', views.SupplierList.as_view(), name='supplier-list'),
    path('suppliers/<int:pk>/', views.SupplierDetail.as_view(), name='supplier-detail'),
    
    path('items/', views.ItemList.as_view(), name='item-list'),
    path('items/<int:pk>/', views.ItemDetail.as_view(), name='item-detail'),
]
