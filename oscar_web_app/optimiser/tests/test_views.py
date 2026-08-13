from http import HTTPStatus

import pytest
from django.http import Http404
from django.urls import reverse
from pytest_django.asserts import assertRaisesMessage
from pytest_django.asserts import assertRedirects
from pytest_django.asserts import assertTemplateUsed

from oscar_web_app.optimiser.forms import GenotypeFormSet
from oscar_web_app.optimiser.forms import LineForm
from oscar_web_app.optimiser.views import select_genotypes

# ruff: noqa: PLR2004


@pytest.fixture
def logged_in_client(client, django_user_model):
    user = django_user_model.objects.create_user(
        email="fake.email",
        password="fake-pass",  # noqa: S106
    )
    client.force_login(user)
    return client


def test_select_line_get(logged_in_client):
    response = logged_in_client.get(reverse("optimiser:select_line"))
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.context["form"], LineForm)
    assertTemplateUsed(response=response, template_name="optimiser/select_line.html")


def test_select_line_post(logged_in_client):

    line_id = 1
    assert line_id not in logged_in_client.session

    response = logged_in_client.post(
        reverse("optimiser:select_line"), {"line": line_id}
    )

    assert logged_in_client.session[str(line_id)] == "Line-A"
    assertRedirects(response, reverse("optimiser:select_genotypes", args=[line_id]))


def test_select_genotypes_get(logged_in_client):
    line_id = 1

    response = logged_in_client.get(
        reverse("optimiser:select_genotypes", args=[line_id])
    )

    assert response.status_code == HTTPStatus.OK
    formset = response.context["formset"]
    assert isinstance(formset, GenotypeFormSet)
    assert len(formset) == 1
    assert sorted(formset[0].fields.keys()) == ["DELETE", "Mut-A", "count"]

    assertTemplateUsed(
        response=response, template_name="optimiser/select_genotypes.html"
    )


def test_select_line_with_no_mutations(rf, mocker):

    mocker.patch(
        "oscar_web_app.optimiser.colony_management.ColonyDev.get_line_mutations",
        return_value=[],
    )

    request = rf.get(reverse("optimiser:select_genotypes", args=[1]))

    with assertRaisesMessage(Http404, "No mutations found for chosen line"):
        select_genotypes(request, line_id=1)


def test_select_genotypes_post(logged_in_client):
    line_id = 1

    # Submit a form for WT=5 and HET=10
    response = logged_in_client.post(
        reverse("optimiser:select_genotypes", args=[line_id]),
        {
            "form-TOTAL_FORMS": 2,
            "form-INITIAL_FORMS": 0,
            "form-MIN_NUM_FORMS": 1,
            "form-MAX_NUM_FORMS": 1000,
            "form-0-Mut-A": "WT",
            "form-0-count": 5,
            "form-1-Mut-A": "HET",
            "form-1-count": 10,
        },
    )

    assert response.status_code == HTTPStatus.OK

    assertTemplateUsed(response=response, template_name="optimiser/result.html")

    # Line stats context
    assert response.context["line_name"] == "Line-A"
    assert response.context["mutations"] == ["Mut-A"]
    assert response.context["stats_total_n"] == 18
    assert response.context["stats_genotyped_n"] == 18
    assert response.context["stats_matings_n"] == 9
    assert response.context["stats_litter_size"] == 2

    # optimisation result context
    assert response.context["total_n"] == 16.66
    assert response.context["total_surplus"] == 1.66
    assert response.context["required_n"] == 15

    # TODO - stats_genotype_table, stats_scheme_summary_table,
    # stats_scheme_number_table, stats_scheme_proportion_table, scheme_table,
    # surplus_genotype_table
