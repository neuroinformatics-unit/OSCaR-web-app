from typing import Any

import pytest
from pytest_django.asserts import assertFormSetError

from oscar_web_app.optimiser.forms import GenotypeFormSet
from oscar_web_app.optimiser.forms import LineForm


def create_formset_data(form_params: list[dict[str, str]]) -> dict[str, Any]:
    """Create some test formset data.

    Parameters
    ----------
    form_params : list[dict[str, str]]
        A list of parameters for each generated form. Each set of parameters
        is given as a dict, which will be added as form-{form-number}-{key} = value.

    Returns
    -------
    dict[str, Any]
        Generated formset data.
    """

    data = {
        "form-TOTAL_FORMS": len(form_params),
        "form-INITIAL_FORMS": 0,
        "form-MIN_NUM_FORMS": 1,
        "form-MAX_NUM_FORMS": 1000,
    }
    for i, params in enumerate(form_params):
        if params["count_type"] == "any_sex":
            params["count_any_sex"] = 5
            params["count_males"] = 1
            params["count_females"] = 1
        else:
            params["count_any_sex"] = 1
            params["count_males"] = 23
            params["count_females"] = 13

        for key, value in params.items():
            data[f"form-{i}-{key}"] = value

    return data


def test_line_form():
    """Test line form correctly populates choices from the colony software."""

    line_form = LineForm()
    choices = dict(line_form.fields["line"].choices)  # type: ignore[attr-defined]

    assert choices == {"": "--------", 1: "Line-A", 2: "Line-AB", 3: "Line-ABC"}


@pytest.mark.parametrize(
    ("formset_params", "mutation_names"),
    [
        pytest.param(
            [
                {"Mut-A": "WT", "count_type": "any_sex"},
                {"Mut-A": "HET", "count_type": "any_sex"},
            ],
            ["Mut-A"],
            id="1 mutation (any sex)",
        ),
        pytest.param(
            [
                {"Mut-A": "WT", "count_type": "specific_sex"},
                {"Mut-A": "HET", "count_type": "specific_sex"},
            ],
            ["Mut-A"],
            id="1 mutation (specific sex)",
        ),
        pytest.param(
            [
                {"Mut-A": "WT", "count_type": "any_sex"},
                {"Mut-A": "HET", "count_type": "specific_sex"},
            ],
            ["Mut-A"],
            id="1 mutation (mixed sex)",
        ),
        pytest.param(
            [
                {"Mut-A": "HET", "count_type": "any_sex"},
                {"Mut-A": "HET", "count_type": "any_sex", "DELETE": "on"},
            ],
            ["Mut-A"],
            id="1 mutation - duplicate genotypes marked for deletion",
        ),
        pytest.param(
            [
                {"Mut-A": "WT", "Mut-B": "HET", "count_type": "any_sex"},
                {
                    "Mut-A": "HET",
                    "Mut-B": "HET",
                    "count_type": "any_sex",
                },
            ],
            ["Mut-A", "Mut-B"],
            id="2 mutations",
        ),
        pytest.param(
            [
                {"Mut-A": "WT", "Mut-B": "HET", "count_type": "any_sex"},
                {
                    "Mut-A": "WT",
                    "Mut-B": "HET",
                    "count_type": "any_sex",
                    "DELETE": "on",
                },
            ],
            ["Mut-A", "Mut-B"],
            id="2 mutations - duplicate genotypes marked for deletion",
        ),
    ],
)
def test_valid_genotype_formsets(formset_params, mutation_names):

    formset_data = create_formset_data(formset_params)
    formset = GenotypeFormSet(
        formset_data,
        form_kwargs={"mutation_names": mutation_names},
    )
    assert formset.is_valid()

    for form in formset:
        assert sorted(form.fields.keys()) == sorted(
            [
                "DELETE",
                "count_type",
                "count_any_sex",
                "count_females",
                "count_males",
                *mutation_names,
            ]
        )
        assert form.mutation_names == mutation_names


@pytest.mark.parametrize(
    ("formset_data", "mutation_names", "expected_msg"),
    [
        pytest.param(
            {
                "form-TOTAL_FORMS": 1,
                "form-INITIAL_FORMS": 0,
                "form-MIN_NUM_FORMS": 1,
                "form-MAX_NUM_FORMS": 1000,
                "form-0-Mut-A": "WT",
                "form-0-count": 1,
                "form-0-DELETE": "on",
            },
            ["Mut-A"],
            "Please submit at least 1 form.",
            id="All forms marked deleted",
        ),
        pytest.param(
            {
                "form-TOTAL_FORMS": 2,
                "form-INITIAL_FORMS": 0,
                "form-MIN_NUM_FORMS": 1,
                "form-MAX_NUM_FORMS": 1000,
                "form-0-Mut-A": "HET",
                "form-0-count": 5,
                "form-1-Mut-A": "HET",
                "form-1-count": 20,
            },
            ["Mut-A"],
            "All genotypes must be unique",
            id="1 mutation - duplicate genotypes",
        ),
        pytest.param(
            {
                "form-TOTAL_FORMS": 2,
                "form-INITIAL_FORMS": 0,
                "form-MIN_NUM_FORMS": 1,
                "form-MAX_NUM_FORMS": 1000,
                "form-0-Mut-A": "WT",
                "form-0-Mut-B": "HET",
                "form-0-count": 5,
                "form-1-Mut-A": "WT",
                "form-1-Mut-B": "HET",
                "form-1-count": 10,
            },
            ["Mut-A", "Mut-B"],
            "All genotypes must be unique",
            id="2 mutations - duplicate genotypes",
        ),
    ],
)
def test_invalid_genotype_formsets(formset_data, mutation_names, expected_msg):
    formset = GenotypeFormSet(
        formset_data,
        form_kwargs={"mutation_names": mutation_names},
    )

    assertFormSetError(formset, form_index=None, field=None, errors=[expected_msg])
