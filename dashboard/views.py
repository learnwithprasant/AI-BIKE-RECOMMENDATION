import json
from collections import Counter
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta

from bikes.models import Bike, Brand
from recommendations.models import RecommendationQuery, Recommendation, Wishlist, Feedback


@login_required
def user_dashboard(request):
    user = request.user
    queries = RecommendationQuery.objects.filter(user=user)
    recommendations = Recommendation.objects.filter(user=user)
    wishlist_count = Wishlist.objects.filter(user=user).count()

    # Favorite brands chart
    brand_counter = Counter(r.bike.brand.name for r in recommendations.select_related('bike__brand'))
    favorite_brands = {
        'labels': list(brand_counter.keys())[:6] or ['No data'],
        'values': list(brand_counter.values())[:6] or [0],
    }

    # Budget distribution
    budget_buckets = {'< ₹1L': 0, '₹1L - ₹2L': 0, '₹2L - ₹3L': 0, '> ₹3L': 0}
    for q in queries:
        if q.budget_max < 100000:
            budget_buckets['< ₹1L'] += 1
        elif q.budget_max < 200000:
            budget_buckets['₹1L - ₹2L'] += 1
        elif q.budget_max < 300000:
            budget_buckets['₹2L - ₹3L'] += 1
        else:
            budget_buckets['> ₹3L'] += 1

    # Fuel preference
    fuel_counter = Counter(q.fuel_type for q in queries)

    # Monthly searches (last 6 months)
    today = timezone.now()
    months = []
    monthly_counts = []
    for i in range(5, -1, -1):
        month_date = (today.replace(day=1) - timedelta(days=1)) if i == 0 else today
        target = (today.replace(day=1) - timedelta(days=30 * i))
        months.append(target.strftime('%b'))
        monthly_counts.append(queries.filter(
            created_at__year=target.year, created_at__month=target.month
        ).count())

    recent_recommendations = recommendations.select_related('bike', 'bike__brand', 'query').order_by('-created_at')[:5]
    recent_queries = queries.order_by('-created_at')[:5]

    avg_match_score = recommendations.aggregate(avg=Avg('match_score'))['avg'] or 0

    context = {
        'total_recommendations': recommendations.count(),
        'total_searches': queries.count(),
        'wishlist_count': wishlist_count,
        'avg_match_score': round(avg_match_score, 1),
        'favorite_brands_json': json.dumps(favorite_brands),
        'budget_distribution_json': json.dumps({'labels': list(budget_buckets.keys()), 'values': list(budget_buckets.values())}),
        'fuel_preference_json': json.dumps({'labels': list(fuel_counter.keys()) or ['No data'], 'values': list(fuel_counter.values()) or [0]}),
        'monthly_searches_json': json.dumps({'labels': months, 'values': monthly_counts}),
        'recent_recommendations': recent_recommendations,
        'recent_queries': recent_queries,
    }
    return render(request, 'dashboard/user_dashboard.html', context)


def is_admin(user):
    return user.is_staff or user.is_superuser


@user_passes_test(is_admin, login_url='accounts:login')
def admin_dashboard(request):
    total_users = User.objects.count()
    total_bikes = Bike.objects.count()
    total_recommendations = Recommendation.objects.count()
    total_feedback = Feedback.objects.count()
    estimated_revenue = Bike.objects.filter(recommendations__isnull=False).distinct().aggregate(
        total=Count('id'))['total'] or 0
    estimated_revenue = estimated_revenue * 5000  # notional referral-commission style metric

    # User growth (last 6 months)
    today = timezone.now()
    months, user_growth = [], []
    for i in range(5, -1, -1):
        target = (today.replace(day=1) - timedelta(days=30 * i))
        months.append(target.strftime('%b'))
        user_growth.append(User.objects.filter(date_joined__year=target.year, date_joined__month=target.month).count())

    # Bike popularity (top 6 by recommendation count)
    popular_bikes = Bike.objects.annotate(rec_count=Count('recommendations')).order_by('-rec_count')[:6]
    popularity = {
        'labels': [f'{b.brand.name} {b.model_name}' for b in popular_bikes] or ['No data'],
        'values': [b.rec_count for b in popular_bikes] or [0],
    }

    # Recommendation accuracy (avg match score trend over months, using created_at)
    accuracy_trend = []
    for i in range(5, -1, -1):
        target = (today.replace(day=1) - timedelta(days=30 * i))
        avg = Recommendation.objects.filter(
            created_at__year=target.year, created_at__month=target.month
        ).aggregate(avg=Avg('match_score'))['avg'] or 0
        accuracy_trend.append(round(avg, 1))

    # Monthly activity (queries per month)
    monthly_activity = []
    for i in range(5, -1, -1):
        target = (today.replace(day=1) - timedelta(days=30 * i))
        monthly_activity.append(RecommendationQuery.objects.filter(
            created_at__year=target.year, created_at__month=target.month
        ).count())

    context = {
        'total_users': total_users,
        'total_bikes': total_bikes,
        'total_recommendations': total_recommendations,
        'total_feedback': total_feedback,
        'estimated_revenue': estimated_revenue,
        'user_growth_json': json.dumps({'labels': months, 'values': user_growth}),
        'bike_popularity_json': json.dumps(popularity),
        'accuracy_trend_json': json.dumps({'labels': months, 'values': accuracy_trend}),
        'monthly_activity_json': json.dumps({'labels': months, 'values': monthly_activity}),
        'recent_feedback': Feedback.objects.select_related('user').order_by('-created_at')[:6],
        'total_brands': Brand.objects.count(),
    }
    return render(request, 'dashboard/admin_dashboard.html', context)
