"""
Views for Django application.

This module contains the following views:

1. `home`: 
   - A simple home page view that returns a basic HTML response.
   - Useful as a placeholder or a default route.

2. `sync_new_client`: 
   - A webhook endpoint for syncing client data from Supabase to RDS.
   - Accepts a POST request with client data in JSON format.
   - Inserts or updates the client record in the RDS database.

Functions:
- `home(request)`: Returns a basic HTML response for the home page.
- `sync_new_client(request)`: Handles Supabase webhook requests for syncing new clients.

Notes:
- `sync_new_client` is exempt from CSRF protection (`@csrf_exempt`) to allow external webhook calls.
- Ensure the webhook is secured using a secret token or IP whitelisting if exposed publicly.

"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import make_aware, is_naive
from datetime import datetime
import os
import json
from .models import RDSClient


@csrf_exempt
def sync_clients(request):
    """
    Endpoint to sync a client from Supabase to RDS.

    Receives a webhook with the client data and updates/inserts it into RDS.
    Validates requests using the WEBHOOK_SECRET to ensure only authorized requests are processed.
    """
    # Validate the Authorization header
    if request.headers.get('Authorization') != f"Bearer {os.getenv('WEBHOOK_SECRET')}":
        return JsonResponse({"error": "Unauthorized"}, status=401)

    if request.method == 'POST':
        try:
            payload = json.loads(request.body)

            # Parse `createdat` to a timezone-aware datetime
            createdat = payload.get('createdat')
            if createdat:
                createdat = datetime.fromisoformat(createdat)  # Convert ISO 8601 string to datetime
                if is_naive(createdat):  # Only make it aware if it is naive
                    createdat = make_aware(createdat)

            # Insert or update the client in RDS
            RDSClient.objects.update_or_create(
                clientid=payload['clientid'],
                defaults={
                    "clientname": payload['clientname'],
                    "aqueductclientnumber": payload['aqueductclientnumber'],
                    "dba": payload.get('dba', ''),
                    "streetaddress": payload.get('streetaddress', ''),
                    "city": payload.get('city', ''),
                    "state": payload.get('state', ''),
                    "zip": payload.get('zip', ''),
                    "country": payload.get('country', ''),
                    "createdat": createdat,
                },
            )
            return JsonResponse({"message": "Client synced successfully!"}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid method"}, status=405)