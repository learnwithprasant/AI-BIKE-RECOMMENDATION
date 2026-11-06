# BikeAI Brands App

## Data source

The Brands feature is read-only and uses the existing Django models in `bikes.models`:

- `Brand.name` → brand name
- `Brand.logo` → optional brand logo
- `Bike.brand` → brand relationship
- `Bike.model_name` → bike model name
- `Bike.image` → bike image
- `Bike.price` → price
- `Bike.mileage` → mileage
- `Bike.engine_cc` → engine size
- `Bike.power_bhp` → power
- `Bike.fuel_type` → fuel type
- `Bike.abs_available` → ABS status

Only active bikes (`is_active=True`) are shown.

The CSV at `ml/data/bikes_dataset.csv` was not duplicated into this app because the application's existing database is the source of truth for the browse pages.

## Brand grouping

Brands are grouped from the existing `Brand` table. Brand URLs use Django's `slugify()` on the existing brand name, for example:

- `Royal Enfield` → `/brands/royal-enfield/`
- `Hero Electric` → `/brands/hero-electric/`

The list is sorted alphabetically. A deterministic fallback accent color is generated from the brand name when no logo is uploaded.

## Adding a new brand

Add the brand through the existing BikeAI data/admin workflow, then assign active bikes to that brand. No code change is required.

If a logo is available, upload it to the existing `Brand.logo` field. Otherwise the pages automatically use the brand's letter avatar.

## Rollback

1. Delete the `brands/` folder.
2. Remove `'brands'` from `INSTALLED_APPS` in `bikeproject/settings.py`.
3. Remove `path('brands/', include('brands.urls'))` from `bikeproject/urls.py`.
4. Remove the Brands navigation `<li>` from `templates/partials/navbar.html`.
5. No database migration is required because this app does not create models or database tables.
