#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def main():
    """
    Run administrative tasks such as starting the server, running migrations, or custom commands.
    """
    # ========================
    # Load Environment Variables
    # ========================
    BASE_DIR = Path(__file__).resolve().parent
    env_file = BASE_DIR / ".env"

    if env_file.exists():
        load_dotenv(dotenv_path=env_file)
        print(f"[INFO] Environment variables loaded from: {env_file}")
    else:
        print("[WARNING] .env file not found. Using system environment variables.")

    # ========================
    # Set Django Settings Module
    # ========================
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
    except KeyError as e:
        print(f"[ERROR] Missing required environment variable: {e}")
        sys.exit(1)

    # ========================
    # Run Management Command
    # ========================
    try:
        from django.core.management import execute_from_command_line
        execute_from_command_line(sys.argv)
    except ImportError as exc:
        raise ImportError(
            "[ERROR] Couldn't import Django. Is it installed and available on your PYTHONPATH? "
            "Did you forget to activate a virtual environment?"
        ) from exc
    except Exception as e:
        print(f"[ERROR] An error occurred while running the command: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
