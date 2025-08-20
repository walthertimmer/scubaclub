import os
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Ensure the database schema exists'

    def handle(self, *args, **options):
        schema_name = os.getenv('DB_SEARCH_PATH', 'scubaclub')
        
        with connection.cursor() as cursor:
            # Check if schema exists
            cursor.execute("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name = %s
            """, [schema_name])
            
            if not cursor.fetchone():
                # Create schema if it doesn't exist
                cursor.execute(f'CREATE SCHEMA IF NOT EXISTS {schema_name}')
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created schema "{schema_name}"'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Schema "{schema_name}" already exists'
                    )
                )
