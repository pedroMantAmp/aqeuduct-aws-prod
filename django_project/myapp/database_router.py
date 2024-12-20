"""
Database router for directing client models to the correct databases.

Routes RDS models to the 'default' database and Supabase models to the 'supabase' database.
"""

import logging

logger = logging.getLogger(__name__)


class ClientRouter:
    """
    A router to control all database operations on models for RDS and Supabase.
    """

    @staticmethod
    def db_for_read(model, **_hints):
        """
        Route read operations to the appropriate database.
        """
        if model.__name__ == 'RDSClient':
            logger.debug("Routing read for RDSClient to 'default'")
            return 'default'
        elif model.__name__ == 'SupabaseClient':
            logger.debug("Routing read for SupabaseClient to 'supabase'")
            return 'supabase'
        return None

    @staticmethod
    def db_for_write(model, **_hints):
        """
        Route write operations to the appropriate database.
        """
        if model.__name__ == 'RDSClient':
            logger.debug("Routing write for RDSClient to 'default'")
            return 'default'
        elif model.__name__ == 'SupabaseClient':
            logger.debug("Routing write for SupabaseClient to 'supabase'")
            return 'supabase'
        return None

    @staticmethod
    def allow_migrate(db, _app_label, model_name=None, **_hints):
        """
        Ensure migrations only apply to the correct database.
        """
        if db == 'default':
            logger.debug(f"Allowing migration for {model_name} on 'default'")
            return model_name == 'rdsclient'
        elif db == 'supabase':
            logger.debug(f"Allowing migration for {model_name} on 'supabase'")
            return model_name == 'supabaseclient'
        return None