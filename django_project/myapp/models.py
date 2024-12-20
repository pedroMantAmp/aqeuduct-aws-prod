"""
Models for Supabase and RDS Client Tables.

Defines the structure of the `clients` table in both Supabase and RDS databases
with a shared base model to avoid duplication.
"""

from django.db import models


class AbstractClient(models.Model):
    """
    Abstract model representing a shared structure for client records.
    """
    clientid = models.AutoField(primary_key=True)
    clientname = models.CharField(max_length=255)
    aqueductclientnumber = models.CharField(max_length=20, unique=True)
    dba = models.CharField(max_length=255, null=True, blank=True)
    streetaddress = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    createdat = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class RDSClient(AbstractClient):
    """
    Model representing a client record in the RDS database.
    """
    class Meta:
        db_table = 'clients'
        managed = True
        app_label = 'django_project'


class SupabaseClient(AbstractClient):
    """
    Model representing a client record in the Supabase database.
    """
    class Meta:
        db_table = 'clients'
        managed = True
        app_label = 'django_project'