from django.urls import path

from . import views

app_name = "optimiser"
urlpatterns = [
    path("", views.select_line, name="select_line"),
    path("<int:line_id>/genotypes", views.select_genotypes, name="select_genotypes"),
]
