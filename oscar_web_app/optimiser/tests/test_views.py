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


@pytest.fixture(autouse=True)
def colony_software_dev(settings):
    """Force use of the DEV colony software"""

    settings.COLONY_SOFTWARE = "DEV"


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
