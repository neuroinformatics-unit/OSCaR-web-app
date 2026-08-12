from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects
from pytest_django.asserts import assertTemplateUsed

from oscar_web_app.optimiser.forms import LineForm


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


def test_select_line_post(logged_in_client, settings):

    line_id = 1
    assert line_id not in logged_in_client.session

    settings.COLONY_SOFTWARE = "DEV"
    response = logged_in_client.post(
        reverse("optimiser:select_line"), {"line": line_id}
    )

    assert logged_in_client.session[str(line_id)] == "Line-A"
    assertRedirects(response, reverse("optimiser:select_genotypes", args=[line_id]))
