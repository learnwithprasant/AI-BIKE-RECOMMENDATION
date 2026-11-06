import csv
import os
from django.conf import settings
from django.core.management.base import BaseCommand
from bikes.models import Brand, Category, Bike

PROS_BANK = [
    "Excellent fuel efficiency", "Comfortable seating position", "Strong resale value",
    "Smooth engine performance", "Great build quality", "Wide dealer/service network",
    "Sporty and aggressive styling", "Good low-end torque", "Reliable braking with ABS",
    "Lightweight and easy to handle",
]
CONS_BANK = [
    "Vibrations at high revs", "Limited storage space", "Firm rear suspension",
    "Average pillion comfort", "Higher maintenance cost", "Basic instrument console",
    "Heavier compared to segment", "Turning radius could be better",
]

REVIEW_TEMPLATE = (
    "The {brand} {model} is a well-rounded {style} bike that suits riders looking for "
    "{purpose} use. With a {cc}cc engine producing {power} bhp and a claimed mileage of "
    "{mileage} km, it strikes a good balance between performance and running costs. "
    "Build quality and ride comfort are class-competitive, making it a solid choice in "
    "its price segment."
)


class Command(BaseCommand):
    help = "Loads the ML-generated bike dataset (ml/data/bikes_dataset.csv) into the database."

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, default=None, help='Path to CSV file')

    def handle(self, *args, **options):
        csv_path = options['file'] or os.path.join(settings.BASE_DIR, 'ml', 'data', 'bikes_dataset.csv')
        if not os.path.exists(csv_path):
            self.stderr.write(self.style.ERROR(f"Dataset not found at {csv_path}. Run: python ml/generate_dataset.py"))
            return

        created_count = 0
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                brand, _ = Brand.objects.get_or_create(name=row['brand'])
                category, _ = Category.objects.get_or_create(name=row['style'])

                import random
                pros = "\n".join(random.sample(PROS_BANK, 3))
                cons = "\n".join(random.sample(CONS_BANK, 2))
                review = REVIEW_TEMPLATE.format(
                    brand=row['brand'], model=row['model'], style=row['style'],
                    purpose=row['best_purposes'].split(',')[0],
                    cc=row['engine_cc'], power=row['power_bhp'], mileage=row['mileage'],
                )

                bike, created = Bike.objects.update_or_create(
                    brand=brand,
                    model_name=row['model'],
                    defaults=dict(
                        category=category,
                        price=int(float(row['price'])),
                        mileage=int(float(row['mileage'])),
                        engine_cc=int(float(row['engine_cc'])),
                        power_bhp=float(row['power_bhp']),
                        fuel_type=row['fuel_type'],
                        transmission=row['transmission'],
                        abs_available=row['abs_available'] == 'True',
                        weight_kg=int(float(row['weight_kg'])),
                        seat_height_mm=int(float(row['seat_height_mm'])),
                        ground_clearance_mm=int(float(row['ground_clearance_mm'])),
                        top_speed_kmph=int(float(row['top_speed_kmph'])),
                        fuel_tank_litres=float(row['fuel_tank_litres']),
                        warranty_years=int(float(row['warranty_years'])),
                        rating=float(row['rating']),
                        best_purposes=row['best_purposes'],
                        pros=pros,
                        cons=cons,
                        expert_review=review,
                        is_active=True,
                    ),
                )
                if created:
                    created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Loaded dataset. {created_count} new bikes created. Total bikes: {Bike.objects.count()}"
        ))
