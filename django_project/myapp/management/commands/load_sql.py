from django.core.management.base import BaseCommand
from django.db import connection
import os

class Command(BaseCommand):
    help = "Load SQL files into the database"

    def handle(self, *args, **kwargs):
        sql_dir = os.path.join("data")  # Folder where your SQL files are located
        if not os.path.exists(sql_dir):
            self.stderr.write(self.style.ERROR(f"Directory {sql_dir} does not exist."))
            return

        for file in os.listdir(sql_dir):
            if file.endswith(".sql"):
                sql_file = os.path.join(sql_dir, file)
                self.stdout.write(self.style.SUCCESS(f"Loading {sql_file}..."))

                try:
                    with open(sql_file, "r") as f:
                        with connection.cursor() as cursor:
                            cursor.execute(f.read())
                    self.stdout.write(self.style.SUCCESS(f"Successfully loaded {file}"))
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Failed to load {file}: {e}"))
