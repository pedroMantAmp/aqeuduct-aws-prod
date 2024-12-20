from django.contrib import admin
from django.urls import path, include

# URL configuration
urlpatterns = [
    # Admin site URLs
    path('admin/', admin.site.urls),

    # Application URLs
    # Replace 'django_project.myapp.urls' with the correct path to your app's urls.py
    path('', include('django_project.myapp.urls')),
]