"""
Cost Prediction Module
=======================
Combines a trained RandomForestRegressor (depreciation model, see
ml/train_cost_model.py) with transparent formula-based components for the
remaining cost buckets, exactly as scoped:
    Output: Fuel Cost, Insurance, Maintenance, Depreciation, EMI Interest,
            Registration, Road Tax, Total Ownership Cost
"""
import functools
from django.conf import settings

_model_cache = None


def _load_model():
    global _model_cache
    if _model_cache is None:
        import joblib
        _model_cache = joblib.load(settings.COST_MODEL_PATH)
    return _model_cache


def estimate_ownership_cost(bike, years, daily_km, fuel_price_per_litre=105.0,
                             annual_insurance=None, annual_service_cost=None,
                             down_payment_pct=20, interest_rate_pct=9.5):
    """
    bike: Bike model instance
    years: ownership period (int)
    daily_km: average km ridden per day
    Returns a dict with every cost bucket + chart-ready breakdown.
    """
    price = bike.price
    engine_cc = bike.engine_cc
    is_electric = bike.fuel_type == 'Electric'

    # ---- 1. Depreciation (ML: RandomForestRegressor) ----
    import pandas as pd
    model = _load_model()
    X = pd.DataFrame([{
        'price': price,
        'engine_cc': engine_cc,
        'years': years,
        'daily_km': daily_km,
        'fuel_type': 1 if is_electric else 0,
    }])
    depreciation_rate = float(model.predict(X)[0])
    depreciation_amount = round(price * depreciation_rate, 2)

    # ---- 2. Fuel / charging cost ----
    total_km = daily_km * 365 * years
    if is_electric:
        # ~0.03 kWh per km average for e-bikes, electricity ~ Rs 8/unit
        units_needed = total_km * 0.03
        fuel_cost = round(units_needed * 8, 2)
    else:
        mileage = bike.mileage or 40
        litres_needed = total_km / mileage
        fuel_cost = round(litres_needed * fuel_price_per_litre, 2)

    # ---- 3. Insurance (reduces ~10%/yr as IDV drops) ----
    if annual_insurance is None:
        annual_insurance = max(1500, price * 0.035)
    insurance_total = 0
    yearly_insurance = annual_insurance
    for _ in range(years):
        insurance_total += yearly_insurance
        yearly_insurance *= 0.9
    insurance_total = round(insurance_total, 2)

    # ---- 4. Maintenance / servicing ----
    if annual_service_cost is None:
        base_service = 1200 if is_electric else (1800 + engine_cc * 2)
        annual_service_cost = base_service
    maintenance_total = round(annual_service_cost * years * (1 + 0.08 * years), 2)

    # ---- 5. EMI interest (if financed) ----
    down_payment = round(price * down_payment_pct / 100, 2)
    loan_amount = price - down_payment
    monthly_rate = interest_rate_pct / 100 / 12
    tenure_months = years * 12
    if loan_amount > 0 and monthly_rate > 0:
        emi = loan_amount * monthly_rate * (1 + monthly_rate) ** tenure_months / (
            ((1 + monthly_rate) ** tenure_months) - 1)
        total_payment = emi * tenure_months
        emi_interest = round(total_payment - loan_amount, 2)
        monthly_emi = round(emi, 2)
    else:
        emi_interest = 0
        monthly_emi = 0

    # ---- 6. Registration & Road Tax (one-time, state-average approx) ----
    registration_fee = round(max(500, price * 0.006), 2)
    road_tax = round(price * (0.02 if is_electric else 0.09), 2)  # EVs get tax rebate

    total_ownership_cost = round(
        fuel_cost + insurance_total + maintenance_total + depreciation_amount +
        emi_interest + registration_fee + road_tax, 2
    )

    return {
        'price': price,
        'years': years,
        'daily_km': daily_km,
        'total_km': round(total_km),
        'fuel_cost': fuel_cost,
        'insurance_total': insurance_total,
        'maintenance_total': maintenance_total,
        'depreciation_rate_pct': round(depreciation_rate * 100, 1),
        'depreciation_amount': depreciation_amount,
        'down_payment': down_payment,
        'loan_amount': loan_amount,
        'monthly_emi': monthly_emi,
        'emi_interest': emi_interest,
        'registration_fee': registration_fee,
        'road_tax': road_tax,
        'total_ownership_cost': total_ownership_cost,
        'chart_labels': ['Fuel/Charging', 'Insurance', 'Maintenance', 'Depreciation', 'EMI Interest', 'Registration', 'Road Tax'],
        'chart_values': [fuel_cost, insurance_total, maintenance_total, depreciation_amount, emi_interest, registration_fee, road_tax],
    }
