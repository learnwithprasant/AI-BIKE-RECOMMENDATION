from django.contrib import admin, messages
from .models import Brand, Category, Bike
from .services.serpapi_images import SerpApiError, fetch_and_save_image


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')


@admin.register(Bike)
class BikeAdmin(admin.ModelAdmin):
    list_display = ('model_name', 'brand', 'category', 'price', 'mileage', 'fuel_type', 'is_active', 'rating')
    list_filter = ('brand', 'category', 'fuel_type', 'transmission', 'abs_available', 'is_active')
    search_fields = ('model_name', 'brand__name')
    list_editable = ('is_active',)
    actions = ['fetch_images_serpapi']

    @admin.action(description='Fetch image from SerpApi')
    def fetch_images_serpapi(self, request, queryset):
        done = 0
        for bike in queryset.select_related('brand'):
            try:
                if fetch_and_save_image(bike):
                    done += 1
            except SerpApiError as exc:
                self.message_user(request, str(exc), level=messages.ERROR)
                return
        self.message_user(request, f'Image saved for {done} of {queryset.count()} bikes.')
