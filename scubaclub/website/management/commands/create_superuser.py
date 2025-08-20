from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import os


class Command(BaseCommand):
    help = 'Create a superuser from environment variables'

    def handle(self, *args, **options):
        username = os.getenv('DJANGO_SUPERUSER_USERNAME', '')
        email = os.getenv('DJANGO_SUPERUSER_EMAIL', '')
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD', '')
        
        if not password:
            self.stdout.write(
                self.style.ERROR('DJANGO_SUPERUSER_PASSWORD environment variable is required')
            )
            return
        
        if User.objects.filter(username=username).exists():
            self.stdout.write(f'Superuser "{username}" already exists')
            return
        
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created superuser "{username}"')
        )
