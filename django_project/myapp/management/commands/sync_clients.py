from django.core.management.base import BaseCommand
from supabase import create_client
from django_project.myapp.models import RDSClient
import os
import boto3
import logging
from datetime import datetime, timezone
from django.utils.timezone import make_aware, is_naive


# Configure AWS CloudWatch logging
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
LOG_GROUP_NAME = "SupabaseToRDSLogs"
LOG_STREAM_NAME = f"sync-clients-{datetime.now(timezone.utc).strftime('%Y-%m-%d_%H-%M-%S')}"

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS CloudWatch client
cloudwatch_client = boto3.client("logs", region_name=AWS_REGION)


def setup_cloudwatch_logs():
    """
    Create a CloudWatch log group and stream if they do not exist.
    """
    try:
        cloudwatch_client.create_log_group(logGroupName=LOG_GROUP_NAME)
    except cloudwatch_client.exceptions.ResourceAlreadyExistsException:
        pass

    try:
        cloudwatch_client.create_log_stream(logGroupName=LOG_GROUP_NAME, logStreamName=LOG_STREAM_NAME)
    except cloudwatch_client.exceptions.ResourceAlreadyExistsException:
        pass


def log_to_cloudwatch(message):
    """
    Log a message to AWS CloudWatch Logs.
    """
    try:
        timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
        cloudwatch_client.put_log_events(
            logGroupName=LOG_GROUP_NAME,
            logStreamName=LOG_STREAM_NAME,
            logEvents=[{"timestamp": timestamp, "message": message}],
        )
    except Exception as e:
        logger.error(f"Failed to log to CloudWatch: {e}")


def sync_clients_to_rds():
    """
    Synchronize client data from Supabase to RDS and log events.
    """
    logger.info("Starting sync_clients_to_rds function...")
    log_to_cloudwatch("Starting sync_clients_to_rds function...")

    # Supabase configuration
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        error_message = "Supabase URL or API key is missing in the environment variables."
        logger.error(error_message)
        log_to_cloudwatch(error_message)
        raise ValueError(error_message)

    supabase_client = create_client(supabase_url, supabase_key)

    try:
        # Fetch clients from Supabase
        response = supabase_client.table("clients").select("*").execute()

        supabase_clients = response.data

        if not supabase_clients:
            logger.info("No clients found in Supabase.")
            log_to_cloudwatch("No clients found in Supabase.")
            return

        # Sync clients to RDS
        for client in supabase_clients:
            try:
                # Ensure `createdat` is timezone-aware
                createdat = client.get("createdat")
                if createdat:
                    createdat = datetime.fromisoformat(createdat)  # Parse ISO 8601 string to datetime
                    if is_naive(createdat):
                        createdat = make_aware(createdat)  # Make timezone-aware

                # Insert or update the client in RDS
                RDSClient.objects.update_or_create(
                    clientid=client.get("clientid"),
                    defaults={
                        "clientname": client.get("clientname"),
                        "aqueductclientnumber": client.get("aqueductclientnumber"),
                        "dba": client.get("dba"),
                        "streetaddress": client.get("streetaddress"),
                        "city": client.get("city"),
                        "state": client.get("state"),
                        "zip": client.get("zip"),
                        "country": client.get("country"),
                        "createdat": createdat,
                    },
                )
                success_message = f"Successfully synced client: {client.get('clientid')}"
                logger.info(success_message)
                log_to_cloudwatch(success_message)
            except Exception as e:
                error_message = f"Error syncing client {client.get('clientid')}: {e}"
                logger.error(error_message)
                log_to_cloudwatch(error_message)

    except Exception as e:
        error_message = f"Failed to fetch data from Supabase: {e}"
        logger.error(error_message)
        log_to_cloudwatch(error_message)
        raise Exception(error_message)


class Command(BaseCommand):
    """
    Django management command to sync clients from Supabase to RDS.

    This command wraps the `sync_clients_to_rds` function and provides
    a CLI interface for initiating the synchronization process.

    Usage:
        python manage.py sync_clients
    """

    help = "Sync clients from Supabase to RDS"

    def handle(self, *args, **kwargs):
        """
        Execute the sync process and log results to CloudWatch.
        """
        setup_cloudwatch_logs()
        logger.info("Starting client sync...")
        log_to_cloudwatch("Starting client sync...")
        try:
            sync_clients_to_rds()
            success_message = "Client sync completed successfully!"
            self.stdout.write(self.style.SUCCESS(success_message))
            log_to_cloudwatch(success_message)
        except Exception as e:
            error_message = f"Error during client sync: {e}"
            self.stderr.write(self.style.ERROR(error_message))
            log_to_cloudwatch(error_message)