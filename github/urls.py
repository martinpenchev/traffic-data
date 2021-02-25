from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('staff/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', include('users.urls')),
]