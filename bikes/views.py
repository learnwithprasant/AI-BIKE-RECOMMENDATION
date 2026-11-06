from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from .models import Bike


def bike_details(request, pk):
    bike = get_object_or_404(Bike, pk=pk, is_active=True)
    similar_bikes = Bike.objects.filter(
        category=bike.category, is_active=True
    ).exclude(pk=bike.pk)[:4]

    is_wishlisted = False
    if request.user.is_authenticated:
        from recommendations.models import Wishlist
        is_wishlisted = Wishlist.objects.filter(user=request.user, bike=bike).exists()

    context = {
        'bike': bike,
        'similar_bikes': similar_bikes,
        'is_wishlisted': is_wishlisted,
    }
    return render(request, 'bikes/details.html', context)


def compare_bikes(request):
    ids = request.GET.get('ids', '')
    bike_ids = [int(i) for i in ids.split(',') if i.strip().isdigit()][:3]
    bikes = list(Bike.objects.filter(id__in=bike_ids, is_active=True))
    # preserve requested order
    bikes.sort(key=lambda b: bike_ids.index(b.id))

    fields = [
        ('Price (₹)', 'price', 'lower'),
        ('Mileage (km)', 'mileage', 'higher'),
        ('Engine (cc)', 'engine_cc', 'higher'),
        ('Power (bhp)', 'power_bhp', 'higher'),
        ('Weight (kg)', 'weight_kg', 'lower'),
        ('Seat Height (mm)', 'seat_height_mm', 'lower'),
        ('Ground Clearance (mm)', 'ground_clearance_mm', 'higher'),
        ('Fuel Tank (L)', 'fuel_tank_litres', 'higher'),
        ('Top Speed (km/h)', 'top_speed_kmph', 'higher'),
        ('Warranty (yrs)', 'warranty_years', 'higher'),
    ]

    comparison_rows = []
    for label, attr, best in fields:
        values = [getattr(b, attr) for b in bikes]
        if not values:
            best_val = None
        elif best == 'higher':
            best_val = max(values)
        else:
            best_val = min(values)
        comparison_rows.append({
            'label': label,
            'attr': attr,
            'values': values,
            'best_val': best_val,
        })

    context = {
        'bikes': bikes,
        'comparison_rows': comparison_rows,
    }
    return render(request, 'bikes/compare.html', context)


def compare_search(request):
    """AJAX endpoint used by the compare page search box."""
    q = request.GET.get('q', '').strip()
    results = []
    if q:
        qs = Bike.objects.filter(
            Q(model_name__icontains=q) | Q(brand__name__icontains=q), is_active=True
        )[:8]
        results = [
            {'id': b.id, 'name': f'{b.brand.name} {b.model_name}', 'price': b.price}
            for b in qs
        ]
    return JsonResponse({'results': results})
