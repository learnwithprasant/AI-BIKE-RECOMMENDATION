from django.urls import path
from . import views

app_name = 'bikes'

urlpatterns = [
    path('<int:pk>/', views.bike_details, name='details'),
    path('compare/', views.compare_bikes, name='compare'),
    path('compare/search/', views.compare_search, name='compare_search'),
]
