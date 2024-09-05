"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.urls import path, include


schema_view = get_schema_view(
   openapi.Info(
      title="MEMIS API",
      default_version='v1',
      description="API documentation for MEMIS",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('assets.urls')),
    path('api/', include('inventory.urls')),
    path('api/', include('accounts.urls')),	
    path('api/login/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/login/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/login/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]


admin.site.index_title = 'MEMIS' 
admin.site.site_header = 'MEMIS Admin'
admin.site.site_title = 'MEMIS Admin'