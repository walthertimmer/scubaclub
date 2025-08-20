"""python manage.py test_email user@mailprovider.com"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Test email configuration'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email address to send test email to')

    def handle(self, *args, **options):
        email = options['email']

        # Debug output
        self.stdout.write(f"EMAIL_HOST: {settings.EMAIL_HOST}")
        self.stdout.write(f"EMAIL_PORT: {settings.EMAIL_PORT}")
        self.stdout.write(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        self.stdout.write(f"EMAIL_HOST_PASSWORD: {'***set***' if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
        self.stdout.write(f"EMAIL_USE_SSL: {getattr(settings, 'EMAIL_USE_SSL', False)}")
        self.stdout.write(f"EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', False)}")
        self.stdout.write(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

        try:
            send_mail(
                'Test Email from ScubaDuikers',
                'This is a test email to verify email configuration.',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully sent test email to {email}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to send email: {e}')
            )
