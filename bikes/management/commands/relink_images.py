"""
Management command: relink_images
---------------------------------
Scans media/bikes/ folder and re-links image files to Bike records.

Default behaviour  : SAFE — only fixes bikes whose image file is missing
                     or not set. Manually uploaded images are NEVER touched.
--force            : Also re-links bikes that have an image but the filename
                     doesn't match the Brand_ModelName pattern.
--dry-run          : Preview what would change, no DB writes.

Usage:
    python manage.py relink_images              # safe — skips manual images
    python manage.py relink_images --force      # re-links everything
    python manage.py relink_images --dry-run    # preview only
"""

import os
from django.core.management.base import BaseCommand
from django.conf import settings
from bikes.models import Bike


class Command(BaseCommand):
    help = 'Re-links media/bikes/ images to Bike records (safe by default).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without saving to the database.',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Override manually set images too (use with caution).',
        )

    def handle(self, *args, **opts):
        dry_run = opts['dry_run']
        force   = opts['force']
        bikes_media_dir = os.path.join(settings.MEDIA_ROOT, 'bikes')

        if not os.path.isdir(bikes_media_dir):
            self.stderr.write(self.style.ERROR(
                f'Directory not found: {bikes_media_dir}\n'
                'Make sure your media/bikes/ folder exists.'
            ))
            return

        # Collect all image files in media/bikes/
        image_files = [
            f for f in os.listdir(bikes_media_dir)
            if os.path.isfile(os.path.join(bikes_media_dir, f))
            and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif'))
        ]
        self.stdout.write(f'Found {len(image_files)} image(s) in media/bikes/\n')

        if force:
            self.stdout.write(self.style.WARNING(
                'WARNING: --force is ON. Manually set images may be overwritten.\n'
            ))
        else:
            self.stdout.write(
                'Safe mode: manually set images that exist on disk will be kept.\n'
                'Use --force to override them.\n'
            )

        # Build lookup: normalised stem -> filename
        # e.g. "tvs_apache_rr_310" -> "TVS_Apache_RR_310.webp"
        def normalise(name):
            stem = os.path.splitext(name)[0]
            return stem.lower().replace(' ', '_').replace('-', '_')

        file_map = {normalise(f): f for f in image_files}

        linked        = 0
        kept_manual   = 0
        already_ok    = 0
        no_match      = []
        manual_kept_list = []

        for bike in Bike.objects.select_related('brand').all():

            current_name = bike.image.name if bike.image else ''
            current_path = os.path.join(settings.MEDIA_ROOT, current_name) if current_name else ''
            current_exists = current_name and os.path.isfile(current_path)

            # --- SAFE MODE: bike already has a working image file on disk ---
            if current_exists and not force:
                self.stdout.write(f'  [KEPT]   {bike} -> {current_name}  (manual/existing)')
                kept_manual += 1
                manual_kept_list.append(str(bike))
                continue

            # Try to match by "Brand_ModelName"
            candidate = normalise(f'{bike.brand.name}_{bike.model_name}')
            matched_file = file_map.get(candidate)

            # Fallback: try just the model name
            if not matched_file:
                candidate2 = normalise(bike.model_name)
                matched_file = file_map.get(candidate2)

            if matched_file:
                new_path = f'bikes/{matched_file}'

                if current_name == new_path:
                    self.stdout.write(f'  [OK]     {bike} -> {matched_file}')
                    already_ok += 1
                else:
                    was = f'  (was: {current_name or "empty"})' if current_name else ''
                    self.stdout.write(
                        self.style.SUCCESS(f'  [LINK]   {bike} -> {matched_file}') + was
                    )
                    if not dry_run:
                        bike.image = new_path
                        bike.save(update_fields=['image'])
                    linked += 1
            else:
                self.stdout.write(self.style.WARNING(f'  [NO IMG] {bike}'))
                no_match.append(str(bike))

        # Summary
        self.stdout.write('\n' + '-' * 50)
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - no changes were saved.'))
        self.stdout.write(self.style.SUCCESS(f'Linked       : {linked}'))
        self.stdout.write(f'Already OK   : {already_ok}')
        self.stdout.write(self.style.SUCCESS(f'Kept (manual): {kept_manual}'))
        self.stdout.write(self.style.WARNING(f'No match     : {len(no_match)}'))

        if no_match:
            self.stdout.write('\nBikes with no matching image file:')
            for name in no_match:
                self.stdout.write(f'  - {name}')
            self.stdout.write(
                '\nTip: Add an image named "BrandName_ModelName.ext" '
                'to media/bikes/ and run this command again.'
            )
