from django.urls import path
from . import views

app_name = 'costestimator'

urlpatterns = [
    path('', views.cost_estimator_view, name='estimator'),
    path('download-report/', views.download_report, name='download_report'),
]
