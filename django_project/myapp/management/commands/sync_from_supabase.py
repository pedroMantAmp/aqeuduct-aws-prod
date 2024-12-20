"""
Custom Django management command to sync data from Supabase to RDS.
"""

from django.core.management.base import BaseCommand
from supabase import create_client, Client
from django_project.myapp.models import RDSClient
import os


class Command(BaseCommand):
    """
    Django command to synchronize data from Supabase to RDS.

    Usage:
        python manage.py sync_from_supabase
    """

    help = "Sync data from Supabase to RDS"

    def handle(self, *args, **kwargs):
        """
        Execute the sync process.
        """
        self.stdout.write("Starting Supabase to RDS sync...")

        # Supabase configuration
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url or not supabase_key:
            self.stderr.write("Supabase URL or API key is missing in the environment variables.")
            return

        supabase: Client = create_client(supabase_url, supabase_key)

        try:
            # Fetch data from Supabase `clients` table
            response = supabase.table("clients").select("*").execute()

            if response.status_code != 200:
                self.stderr.write(f"Failed to fetch data from Supabase: {response.data}")
                return

            supabase_clients = response.data

            # Sync each client to RDS
            for client in supabase_clients:
                # Extract client data
                clientid = client.get("clientid")
                clientname = client.get("clientname")
                aqueductclientnumber = client.get("aqueductclientnumber")
                dba = client.get("dba")
                streetaddress = client.get("streetaddress")
                city = client.get("city")
                state = client.get("state")
                zipcode = client.get("zip")  # Updated from 'zip' to 'zipcode'
                country = client.get("country")
                createdat = client.get("createdat")

                # Insert or update the RDS client table
                RDSClient.objects.update_or_create(
                    clientid=clientid,
                    defaults={
                        "clientname": clientname,
                        "aqueductclientnumber": aqueductclientnumber,
                        "dba": dba,
                        "streetaddress": streetaddress,
                        "city": city,
                        "state": state,
                        "zip": zipcode,  # Updated here
                        "country": country,
                        "createdat": createdat,
                    },
                )

                self.stdout.write(f"Successfully synced client: {clientid}")

        except Exception as e:
            self.stderr.write(f"An error occurred during sync: {e}")