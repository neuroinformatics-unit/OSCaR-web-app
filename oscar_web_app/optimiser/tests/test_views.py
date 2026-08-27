from http import HTTPStatus

import pandas as pd
import pytest
from django.http import Http404
from django.urls import reverse
from oscar_colony.breeding_scheme import Genotype
from oscar_colony.optimise.optimal_scheme_calculator import calculate_optimal_scheme
from pytest_django.asserts import assertRaisesMessage
from pytest_django.asserts import assertRedirects
from pytest_django.asserts import assertTemplateUsed

from oscar_web_app.optimiser.colony_management import get_colony
from oscar_web_app.optimiser.forms import GenotypeFormSet
from oscar_web_app.optimiser.forms import LineForm
from oscar_web_app.optimiser.views import select_genotypes
from tests.helpers import convert_html_to_df


@pytest.fixture
def logged_in_client(client, django_user_model):
    user = django_user_model.objects.create_user(
        email="fake.email",
        password="fake-pass",  # noqa: S106
    )
    client.force_login(user)
    return client


def test_select_line_get(logged_in_client):
    """Test the select line form is shown on GET"""

    response = logged_in_client.get(reverse("optimiser:select_line"))
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.context["form"], LineForm)
    assertTemplateUsed(response=response, template_name="optimiser/select_line.html")


@pytest.mark.parametrize(
    ("line_id", "line_name"),
    [(1, "Line-A"), (2, "Line-AB"), (3, "Line-ABC")],
)
def test_select_line_post(logged_in_client, line_id, line_name):
    """Test POST with specific line ids, saves the correct line name"""

    assert line_id not in logged_in_client.session

    response = logged_in_client.post(
        reverse("optimiser:select_line"), {"line": line_id}
    )

    assert logged_in_client.session[str(line_id)] == line_name
    assertRedirects(response, reverse("optimiser:select_genotypes", args=[line_id]))


@pytest.mark.parametrize(
    ("line_id", "mutations"),
    [(1, ["Mut-A"]), (2, ["Mut-A", "Mut-B"]), (3, ["Mut-A", "Mut-B", "Mut-C"])],
)
def test_select_genotypes_get(logged_in_client, line_id, mutations):
    """Test select genotypes form is shown with correct mutations."""

    response = logged_in_client.get(
        reverse("optimiser:select_genotypes", args=[line_id])
    )

    assert response.status_code == HTTPStatus.OK
    formset = response.context["formset"]
    assert isinstance(formset, GenotypeFormSet)
    assert len(formset) == 1
    assert sorted(formset[0].fields.keys()) == ["DELETE", *mutations, "count"]

    assertTemplateUsed(
        response=response, template_name="optimiser/select_genotypes.html"
    )


def test_select_line_with_no_mutations(rf, mocker):
    """Test that the absence of mutations triggers a 404 response."""

    mocker.patch(
        "oscar_web_app.optimiser.colony_management.ColonyDev.get_line_mutations",
        return_value=[],
    )

    request = rf.get(reverse("optimiser:select_genotypes", args=[1]))

    with assertRaisesMessage(Http404, "No mutations found for chosen line"):
        select_genotypes(request, line_id=1)


@pytest.mark.parametrize(
    ("line_id", "form_params", "required_n_per_genotype"),
    [
        pytest.param(
            1,
            {
                "form-TOTAL_FORMS": 2,
                "form-0-Mut-A": "WT",
                "form-0-count": 5,
                "form-1-Mut-A": "HET",
                "form-1-count": 10,
            },
            {(Genotype.WT,): 5, (Genotype.HET,): 10},
            id="1 mutation",
        )
    ],
)
def test_select_genotypes_post(
    logged_in_client, line_id, form_params, required_n_per_genotype
):
    """
    Test submission of select genotypes form renders results page with
    correct context values.
    """

    # Form params that are the same for all cases
    default_params = {
        "form-INITIAL_FORMS": 0,
        "form-MIN_NUM_FORMS": 1,
        "form-MAX_NUM_FORMS": 1000,
    }
    response = logged_in_client.post(
        reverse("optimiser:select_genotypes", args=[line_id]),
        default_params | form_params,
    )

    assert response.status_code == HTTPStatus.OK
    assertTemplateUsed(response=response, template_name="optimiser/result.html")

    # Values should match those in the given line stats
    line_stats = get_colony().get_line_stats("Line-A")

    # Line stats context
    assert response.context["line_name"] == line_stats.line_name
    assert response.context["mutations"] == line_stats.mutations
    assert response.context["stats_total_n"] == line_stats.total_n_offspring
    assert (
        response.context["stats_genotyped_n"] == line_stats.total_n_genotyped_offspring
    )
    assert response.context["stats_matings_n"] == line_stats.total_n_successful_matings
    assert response.context["stats_litter_size"] == line_stats.average_litter_size

    pd.testing.assert_frame_equal(
        convert_html_to_df(response.context["stats_genotype_table"]),
        line_stats.create_n_per_genotype_df().astype(str),
    )
    pd.testing.assert_frame_equal(
        convert_html_to_df(response.context["stats_scheme_summary_table"]),
        line_stats.create_scheme_summary_df(decimal_places=2).astype(str),
    )
    pd.testing.assert_frame_equal(
        convert_html_to_df(
            response.context["stats_scheme_number_table"], numeric_as_float=True
        ),
        line_stats.create_scheme_number_df().astype(str),
    )
    pd.testing.assert_frame_equal(
        convert_html_to_df(response.context["stats_scheme_proportion_table"]),
        line_stats.create_scheme_proportion_df(decimal_places=2).astype(str),
    )

    breeding_schemes, surplus = calculate_optimal_scheme(
        required_n_per_genotype, line_stats=line_stats, default_litter_size=6
    )

    # optimisation result context
    assert response.context["total_n"] == round(surplus.total_n, 2)
    assert response.context["total_surplus"] == round(surplus.total_n_surplus, 2)
    assert response.context["required_n"] == surplus.total_n - surplus.total_n_surplus

    pd.testing.assert_frame_equal(
        convert_html_to_df(response.context["scheme_table"]),
        pd.DataFrame(
            breeding_schemes.items(), columns=("Scheme", "N matings"), dtype=str
        ),
    )
    pd.testing.assert_frame_equal(
        convert_html_to_df(response.context["surplus_genotype_table"]),
        surplus.create_genotype_df(decimal_places=2).astype(str),
    )
