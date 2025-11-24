from django.core.management.base import BaseCommand
from scubaclub.website.models import DiveClub
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Create slugs for DiveClub objects that do not have one.'

    def handle(self, *args, **options):
        clubs_without_slug = DiveClub.objects.filter(slug='')
        for club in clubs_without_slug:
            club.slug = slugify(club.name) or f"club-{club.id}"  # Fallback to ID if name is empty
            club.save()
            self.stdout.write(self.style.SUCCESS(f'Created slug "{club.slug}" for club "{club.name}"'))
        
        if not clubs_without_slug:
            self.stdout.write(self.style.SUCCESS('No clubs found without slugs.'))
            