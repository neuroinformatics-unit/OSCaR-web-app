from django.urls import path

from . import views

app_name = "optimiser"
urlpatterns = [path("", views.select_genotypes, name="select_genotypes")]
