from django.contrib import admin

from .models import BikeDealer


@admin.register(BikeDealer)
class BikeDealerAdmin(admin.ModelAdmin):
    list_display = ('dealer_name', 'brand', 'city', 'phone')
    search_fields = ('dealer_name', 'brand', 'city')
    list_filter = ('brand', 'state')
