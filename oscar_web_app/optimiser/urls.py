from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = "optimiser"
urlpatterns = [
    path("", views.select_line, name="select_line"),
    path("<int:line_id>/genotypes", views.select_genotypes, name="select_genotypes"),
    path(
        "line_stats",
        TemplateView.as_view(template_name="optimiser/line_stats.html"),
        name="line_stats",
    ),
    path(
        "validation",
        TemplateView.as_view(template_name="optimiser/validation.html"),
        name="validation",
    ),
    path(
        "rules",
        TemplateView.as_view(template_name="optimiser/rules.html"),
        name="rules",
    ),
]
