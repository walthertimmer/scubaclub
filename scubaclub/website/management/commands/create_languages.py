from django.core.management.base import BaseCommand
from scubaclub.website.models import Language


class Command(BaseCommand):
    help = 'Create Language objects if they do not exist.'

    def handle(self, *args, **options):
        codes = ['en', 'nl']
        for code in codes:
            if not Language.objects.filter(code=code).exists():
                Language.objects.create(code=code)
                self.stdout.write(self.style.SUCCESS(f'Created language "{code}"'))
            else:
                self.stdout.write(f'Language "{code}" already exists')
