import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from bikes.models import Bike
from .utils import estimate_ownership_cost


@login_required
def cost_estimator_view(request):
    bikes = Bike.objects.filter(is_active=True).select_related('brand')
    selected_bike = None
    result = None

    bike_id = request.GET.get('bike_id') or request.POST.get('bike_id')
    if bike_id:
        selected_bike = get_object_or_404(Bike, id=bike_id)

    if request.method == 'POST' and selected_bike:
        years = int(request.POST.get('years', 5))
        daily_km = float(request.POST.get('daily_km', 20))
        fuel_price = float(request.POST.get('fuel_price', 105))
        insurance = request.POST.get('insurance')
        service_cost = request.POST.get('service_cost')

        result = estimate_ownership_cost(
            bike=selected_bike,
            years=years,
            daily_km=daily_km,
            fuel_price_per_litre=fuel_price,
            annual_insurance=float(insurance) if insurance else None,
            annual_service_cost=float(service_cost) if service_cost else None,
        )
        result['chart_labels_json'] = json.dumps(result['chart_labels'])
        result['chart_values_json'] = json.dumps(result['chart_values'])

        request.session['last_cost_estimate'] = {
            'bike_id': selected_bike.id,
            'bike_name': str(selected_bike),
            **{k: v for k, v in result.items() if k not in ('chart_labels', 'chart_values')},
        }

    context = {
        'bikes': bikes,
        'selected_bike': selected_bike,
        'result': result,
    }
    return render(request, 'costestimator/estimator.html', context)


@login_required
def download_report(request):
    """Generates a simple PDF ownership-cost report using reportlab."""
    data = request.session.get('last_cost_estimate')
    if not data:
        return redirect('costestimator:estimator')

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="ownership_cost_report.pdf"'

    c = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    y = height - 30 * mm

    c.setFont("Helvetica-Bold", 18)
    c.drawString(20 * mm, y, "BikeAI - Ownership Cost Report")
    y -= 12 * mm
    c.setFont("Helvetica", 11)
    c.drawString(20 * mm, y, f"Bike: {data.get('bike_name')}")
    y -= 8 * mm
    c.drawString(20 * mm, y, f"Ownership period: {data.get('years')} years  |  Daily distance: {data.get('daily_km')} km")
    y -= 12 * mm

    rows = [
        ("Ex-showroom Price", data.get('price')),
        ("Fuel / Charging Cost", data.get('fuel_cost')),
        ("Insurance (total)", data.get('insurance_total')),
        ("Maintenance (total)", data.get('maintenance_total')),
        (f"Depreciation ({data.get('depreciation_rate_pct')}%)", data.get('depreciation_amount')),
        ("EMI Interest", data.get('emi_interest')),
        ("Registration Fee", data.get('registration_fee')),
        ("Road Tax", data.get('road_tax')),
    ]
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, y, "Cost Breakdown")
    y -= 8 * mm
    c.setFont("Helvetica", 11)
    for label, value in rows:
        c.drawString(22 * mm, y, str(label))
        c.drawRightString(180 * mm, y, f"Rs. {value:,.0f}")
        y -= 7 * mm

    y -= 4 * mm
    c.setFont("Helvetica-Bold", 13)
    c.drawString(20 * mm, y, "Total Ownership Cost")
    c.drawRightString(180 * mm, y, f"Rs. {data.get('total_ownership_cost'):,.0f}")

    c.showPage()
    c.save()
    return response
