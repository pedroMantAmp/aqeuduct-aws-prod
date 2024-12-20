"""
Service for synchronizing client data from Supabase to RDS.

Fetches all records from the Supabase `clients` table and updates/inserts them
into the RDS `clients` table.
"""

from django.db import transaction  # Ensure this is imported
from django.utils.timezone import make_aware, is_naive
from django_project.myapp.models import RDSClient, SupabaseClient
import logging

logger = logging.getLogger(__name__)


def sync_clients_to_rds():
    """
    Synchronize client data from Supabase to RDS.

    Fetches all records from the Supabase `clients` table and updates or inserts them
    into the RDS `clients` table. Logs success or error details.
    """
    try:
        # Fetch all clients from Supabase
        supabase_clients = SupabaseClient.objects.using('supabase').all()

        # Sync to RDS
        for supabase_client in supabase_clients:
            # Ensure `createdat` is timezone-aware
            createdat = supabase_client.createdat
            if is_naive(createdat):
                createdat = make_aware(createdat)

            with transaction.atomic(using='default'):  # Importing transaction fixes the issue
                RDSClient.objects.update_or_create(
                    clientid=supabase_client.clientid,
                    defaults={
                        "clientname": supabase_client.clientname,
                        "aqueductclientnumber": supabase_client.aqueductclientnumber,
                        "dba": supabase_client.dba,
                        "streetaddress": supabase_client.streetaddress,
                        "city": supabase_client.city,
                        "state": supabase_client.state,
                        "zip": supabase_client.zip,
                        "country": supabase_client.country,
                        "createdat": createdat,
                    },
                )
        logger.info("Client sync successful")
    except Exception as e:
        logger.error(f"Error syncing clients: {e}")
        raise