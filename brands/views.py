from django.http import Http404
from django.shortcuts import render
from django.utils.text import slugify

from bikes.models import Bike, Brand


def _brand_theme_color(name):
    """Return a deterministic fallback color for a brand hero/avatar."""
    palette = [
        '#1E6FE0', '#E10600', '#7C3AED', '#0891B2',
        '#16A34A', '#D97706', '#DB2777', '#4F46E5',
    ]
    return palette[sum(ord(char) for char in name.lower()) % len(palette)]


def _brand_data(brand):
    bikes = brand.bikes.filter(is_active=True)
    return {
        'id': brand.id,
        'name': brand.name,
        'slug': slugify(brand.name),
        'bike_count': bikes.count(),
        'logo_url': brand.logo.url if brand.logo else None,
        'theme_color': _brand_theme_color(brand.name),
    }


def _brand_for_slug(slug):
    for brand in Brand.objects.all():
        if slugify(brand.name).lower() == slug.lower():
            return brand
    raise Http404('That bike brand could not be found.')


def brand_list(request):
    """Browse all brands using the existing Brand and Bike database models."""
    brands = [
        _brand_data(brand)
        for brand in Brand.objects.all()
        if brand.bikes.filter(is_active=True).exists()
    ]
    brands.sort(key=lambda item: item['name'].casefold())

    return render(request, 'brands/brands_list.html', {'brands': brands})


def brand_detail(request, slug):
    """Show all active bikes belonging to one existing Brand record."""
    brand = _brand_for_slug(slug)
    bikes = list(
        Bike.objects.filter(brand=brand, is_active=True)
        .select_related('brand')
        .order_by('model_name')
    )

    wishlisted_ids = set()
    if request.user.is_authenticated:
        from recommendations.models import Wishlist
        wishlisted_ids = set(
            Wishlist.objects.filter(
                user=request.user,
                bike__in=bikes,
            ).values_list('bike_id', flat=True)
        )

    context = {
        'brand': brand,
        'brand_info': _brand_data(brand),
        'bikes': bikes,
        'wishlisted_ids': wishlisted_ids,
    }
    return render(request, 'brands/brand_detail.html', context)
