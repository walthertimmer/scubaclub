from django.core.management.base import BaseCommand
from scubaclub.website.models import Country, CountryTranslation, Language


class Command(BaseCommand):
    help = 'Create Country objects with ISO3 codes and translations for English and Dutch.'

    def handle(self, *args, **options):
        # Sample list of countries with ISO3 codes and names in English and Dutch
        # Expand this list as needed (source: ISO 3166-1 alpha-3)
        countries_data = [
            {'iso_code': 'NLD', 'en': 'Netherlands', 'nl': 'Nederland'},
            {'iso_code': 'BEL', 'en': 'Belgium', 'nl': 'België'},
            {'iso_code': 'DEU', 'en': 'Germany', 'nl': 'Duitsland'},
            {'iso_code': 'FRA', 'en': 'France', 'nl': 'Frankrijk'},
            {'iso_code': 'GBR', 'en': 'United Kingdom', 'nl': 'Verenigd Koninkrijk'},
            {'iso_code': 'USA', 'en': 'United States', 'nl': 'Verenigde Staten'},
            {'iso_code': 'CAN', 'en': 'Canada', 'nl': 'Canada'},
            {'iso_code': 'ESP', 'en': 'Spain', 'nl': 'Spanje'},
            {'iso_code': 'ITA', 'en': 'Italy', 'nl': 'Italië'},
            {'iso_code': 'AUS', 'en': 'Australia', 'nl': 'Australië'},
        ]

        en_lang = Language.objects.get(code='en')
        nl_lang = Language.objects.get(code='nl')

        for data in countries_data:
            country, created = Country.objects.get_or_create(
                iso_code=data['iso_code'],
                defaults={'created_at': None}  # auto_now_add handles this
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created country "{data["iso_code"]}"'))
            else:
                self.stdout.write(f'Country "{data["iso_code"]}" already exists')

            # Create or update English translation
            CountryTranslation.objects.get_or_create(
                country=country,
                language=en_lang,
                defaults={'name': data['en']}
            )

            # Create or update Dutch translation
            CountryTranslation.objects.get_or_create(
                country=country,
                language=nl_lang,
                defaults={'name': data['nl']}
            )

        self.stdout.write(self.style.SUCCESS('Country creation and translations completed.'))
