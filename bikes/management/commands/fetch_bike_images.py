
from django.core.management.base import BaseCommand

from bikes.models import Bike
from bikes.services.serpapi_images import SerpApiError, fetch_and_save_image


class Command(BaseCommand):
    help = 'Fetch bike images from SerpApi for bikes that have no image.'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='Replace existing images too')
        parser.add_argument('--limit', type=int, default=0, help='Max bikes to process (saves API credits)')

    def handle(self, *args, **opts):
        qs = Bike.objects.select_related('brand')
        if not opts['all']:
            qs = qs.filter(image='') | qs.filter(image__isnull=True)
        if opts['limit']:
            qs = qs[:opts['limit']]

        saved, failed = 0, []
        for bike in qs:
            try:
                url = fetch_and_save_image(bike)
            except SerpApiError as exc:
                if exc.fatal:
                    self.stderr.write(self.style.ERROR(f'Stopped: {exc}'))
                    break
                self.stdout.write(self.style.WARNING(f'{bike}: failed ({exc})'))
                failed.append(str(bike))
                continue
            if url:
                saved += 1
                self.stdout.write(self.style.SUCCESS(f'{bike}: saved'))
            else:
                failed.append(str(bike))
                self.stdout.write(self.style.WARNING(f'{bike}: no usable image found'))

        self.stdout.write(f'\nDone. Saved: {saved}, failed: {len(failed)}')
        if failed:
            self.stdout.write('Run the command again (without --all) to retry the failed ones.')