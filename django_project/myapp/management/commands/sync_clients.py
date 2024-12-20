"""
Custom Django management command to sync clients from Supabase to RDS.
"""

from django.core.management.base import BaseCommand
from django_project.myapp.services import sync_clients_to_rds


class Command(BaseCommand):
    """
    Django command to synchronize clients from Supabase to RDS.

    Usage:
        python manage.py sync_clients
    """

    help = "Sync clients from Supabase to RDS"

    def handle(self, *args, **kwargs):
        """
        Handle the command execution.

        Calls the sync_clients_to_rds function to perform the synchronization.
        Logs the start and completion of the process, or any errors encountered.
        """
        self.stdout.write(self.style.NOTICE("Starting client sync..."))
        try:
            sync_clients_to_rds()
            self.stdout.write(self.style.SUCCESS("Client sync completed successfully!"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error during client sync: {e}"))