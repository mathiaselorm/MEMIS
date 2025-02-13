from django.urls import path
from . import views  

urlpatterns = [
    # Category Endpoints
    path('categories/', views.CategoryListCreateView.as_view(), name='category-list'),
    path('categories/<str:identifier>/', views.CategoryDetailView.as_view(), name='category-detail'),

    # Item Endpoints
    path('items/', views.ItemListCreateView.as_view(), name='item-list'),
    path('items/<int:pk>/', views.ItemDetailView.as_view(), name='item-detail'),

    # Category Items Endpoint - items within a specific category
    path('categories/<str:identifier>/items/', views.CategoryItemsListView.as_view(), name='category-items-list'),
    

]
