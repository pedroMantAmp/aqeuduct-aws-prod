from django.urls import path
from . import views

urlpatterns = [
    path('webhooks/sync-clients/', views.sync_clients, name='sync_clients'),  # Webhook for client sync
]