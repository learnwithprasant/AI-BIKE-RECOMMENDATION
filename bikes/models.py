from django.db import models
from django.urls import reverse


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(models.Model):
    """Style / category of bike e.g. Commuter, Sports, Cruiser, Adventure, Scooter, Electric"""
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, default='fa-motorcycle', help_text='Font Awesome icon class')

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


FUEL_CHOICES = [
    ('Petrol', 'Petrol'),
    ('Electric', 'Electric'),
]

TRANSMISSION_CHOICES = [
    ('Manual', 'Manual'),
    ('Automatic', 'Automatic'),
]

PURPOSE_CHOICES = [
    ('Office', 'Office Commute'),
    ('College', 'College'),
    ('Racing', 'Racing / Sports'),
    ('Touring', 'Touring'),
    ('Adventure', 'Adventure / Off-road'),
    ('Delivery', 'Delivery'),
]


class Bike(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='bikes')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='bikes')
    model_name = models.CharField(max_length=150)
    image = models.ImageField(upload_to='bikes/', blank=True, null=True)

    price = models.PositiveIntegerField(help_text='Ex-showroom price in INR')
    mileage = models.PositiveIntegerField(help_text='km/l or km per charge')
    engine_cc = models.PositiveIntegerField(default=0)
    power_bhp = models.FloatField(default=0)
    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES, default='Petrol')
    transmission = models.CharField(max_length=20, choices=TRANSMISSION_CHOICES, default='Manual')
    abs_available = models.BooleanField(default=False)

    weight_kg = models.PositiveIntegerField(default=0)
    seat_height_mm = models.PositiveIntegerField(default=0)
    ground_clearance_mm = models.PositiveIntegerField(default=0)
    top_speed_kmph = models.PositiveIntegerField(default=0)
    fuel_tank_litres = models.FloatField(default=0)
    warranty_years = models.PositiveIntegerField(default=2)
    rating = models.FloatField(default=4.0)

    best_purposes = models.CharField(max_length=255, blank=True, help_text='Comma separated: Office,College,Racing...')
    pros = models.TextField(blank=True, help_text='One per line')
    cons = models.TextField(blank=True, help_text='One per line')
    expert_review = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.brand.name} {self.model_name}'

    def get_absolute_url(self):
        return reverse('bikes:details', args=[self.id])

    @property
    def pros_list(self):
        return [p.strip() for p in self.pros.split('\n') if p.strip()]

    @property
    def cons_list(self):
        return [c.strip() for c in self.cons.split('\n') if c.strip()]

    @property
    def purposes_list(self):
        return [p.strip() for p in self.best_purposes.split(',') if p.strip()]
