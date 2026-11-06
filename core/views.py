from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from bikes.models import Bike
from recommendations.models import Recommendation


def landing_page(request):
    if request.user.is_authenticated:
        pass  # still show landing if they navigate to '/', don't force redirect
    featured_bikes = Bike.objects.filter(is_active=True).order_by('-rating')[:6]
    search_bikes = list(
        Bike.objects.filter(is_active=True)
        .select_related('brand')
        .order_by('brand__name', 'model_name')
        .values('id', 'model_name', 'brand__name', 'price')
    )
    for bike in search_bikes:
        bike['name'] = f"{bike['brand__name']} {bike['model_name']}"
        bike['url'] = f"/bikes/{bike['id']}/"

    stats = {
        'total_bikes': Bike.objects.filter(is_active=True).count(),
        'total_users': User.objects.count(),
        'total_recommendations': Recommendation.objects.count(),
        'accuracy': 96,
    }
    return render(request, 'core/landing.html', {
        'featured_bikes': featured_bikes,
        'search_bikes': search_bikes,
        'stats': stats,
    })


def about_page(request):
    return render(request, 'core/about.html')


def contact_page(request):
    if request.method == 'POST':
        messages.success(request, "Thanks for reaching out! Our team will get back to you within 24 hours.")
        return redirect('core:contact')
    return render(request, 'core/contact.html')
