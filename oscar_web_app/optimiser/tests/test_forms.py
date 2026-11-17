import pytest
from pytest_django.asserts import assertFormSetError

from oscar_web_app.optimiser.forms import GenotypeFormSet
from oscar_web_app.optimiser.forms import LineForm
from tests.helpers import create_formset_data


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
                {
                    "Mut-A": "WT",
                    "count_type": "any_sex",
                    "count_any_sex": 5,
                    "count_males": 1,
                    "count_females": 1,
                },
                {
                    "Mut-A": "HET",
                    "count_type": "any_sex",
                    "count_any_sex": 10,
                    "count_males": 1,
                    "count_females": 1,
                },
            ],
            ["Mut-A"],
            id="1 mutation (any sex)",
        ),
        pytest.param(
            [
                {
                    "Mut-A": "WT",
                    "count_type": "specific_sex",
                    "count_any_sex": 1,
                    "count_males": 10,
                    "count_females": 20,
                },
                {
                    "Mut-A": "HET",
                    "count_type": "specific_sex",
                    "count_any_sex": 1,
                    "count_males": 10,
                    "count_females": 20,
                },
            ],
            ["Mut-A"],
            id="1 mutation (specific sex)",
        ),
        pytest.param(
            [
                {
                    "Mut-A": "WT",
                    "count_type": "any_sex",
                    "count_any_sex": 1,
                    "count_males": 1,
                    "count_females": 1,
                },
                {
                    "Mut-A": "HET",
                    "count_type": "specific_sex",
                    "count_any_sex": 1,
                    "count_males": 1,
                    "count_females": 1,
                },
            ],
            ["Mut-A"],
            id="1 mutation (mixed sex)",
        ),
        pytest.param(
            [
                {
                    "Mut-A": "HET",
                    "count_type": "any_sex",
                    "count_any_sex": 5,
                    "count_males": 1,
                    "count_females": 1,
                },
                {
                    "Mut-A": "HET",
                    "count_type": "any_sex",
                    "count_any_sex": 20,
                    "count_males": 1,
                    "count_females": 1,
                    "DELETE": "on",
                },
            ],
            ["Mut-A"],
            id="1 mutation - duplicate genotypes marked for deletion",
        ),
        pytest.param(
            [
                {
                    "Mut-A": "WT",
                    "Mut-B": "HET",
                    "count_type": "any_sex",
                    "count_any_sex": 5,
                    "count_males": 1,
                    "count_females": 1,
                },
                {
                    "Mut-A": "HET",
                    "Mut-B": "HET",
                    "count_type": "any_sex",
                    "count_any_sex": 10,
                    "count_males": 1,
                    "count_females": 1,
                },
            ],
            ["Mut-A", "Mut-B"],
            id="2 mutations",
        ),
        pytest.param(
            [
                {
                    "Mut-A": "WT",
                    "Mut-B": "HET",
                    "count_type": "any_sex",
                    "count_any_sex": 5,
                    "count_males": 1,
                    "count_females": 1,
                },
                {
                    "Mut-A": "WT",
                    "Mut-B": "HET",
                    "count_type": "any_sex",
                    "DELETE": "on",
                    "count_any_sex": 10,
                    "count_males": 1,
                    "count_females": 1,
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
    ("formset_params", "mutation_names", "expected_msg"),
    [
        pytest.param(
            [
                {
                    "Mut-A": "WT",
                    "count_type": "any_sex",
                    "count_any_sex": 1,
                    "count_males": 1,
                    "count_females": 1,
                    "DELETE": "on",
                },
            ],
            ["Mut-A"],
            "Please submit at least 1 form.",
            id="All forms marked deleted",
        ),
        pytest.param(
            [
                {
                    "Mut-A": "HET",
                    "count_type": "any_sex",
                    "count_any_sex": 5,
                    "count_males": 1,
                    "count_females": 1,
                },
                {
                    "Mut-A": "HET",
                    "count_type": "any_sex",
                    "count_any_sex": 20,
                    "count_males": 1,
                    "count_females": 1,
                },
            ],
            ["Mut-A"],
            "All genotypes must be unique",
            id="1 mutation (any sex) - duplicate genotypes",
        ),
        pytest.param(
            [
                {
                    "Mut-A": "HET",
                    "count_type": "specific_sex",
                    "count_any_sex": 1,
                    "count_males": 20,
                    "count_females": 30,
                },
                {
                    "Mut-A": "HET",
                    "count_type": "specific_sex",
                    "count_any_sex": 1,
                    "count_males": 20,
                    "count_females": 30,
                },
            ],
            ["Mut-A"],
            "All genotypes must be unique",
            id="1 mutation (specific sex) - duplicate genotypes",
        ),
        pytest.param(
            [
                {
                    "Mut-A": "HET",
                    "count_type": "any_sex",
                    "count_any_sex": 1,
                    "count_males": 1,
                    "count_females": 1,
                },
                {
                    "Mut-A": "HET",
                    "count_type": "specific_sex",
                    "count_any_sex": 1,
                    "count_males": 1,
                    "count_females": 1,
                },
            ],
            ["Mut-A"],
            "All genotypes must be unique",
            id="1 mutation (mixed sex) - duplicate genotypes",
        ),
        pytest.param(
            [
                {
                    "Mut-A": "WT",
                    "Mut-B": "HET",
                    "count_type": "any_sex",
                    "count_any_sex": 5,
                    "count_males": 1,
                    "count_females": 1,
                },
                {
                    "Mut-A": "WT",
                    "Mut-B": "HET",
                    "count_type": "any_sex",
                    "count_any_sex": 10,
                    "count_males": 1,
                    "count_females": 1,
                },
            ],
            ["Mut-A", "Mut-B"],
            "All genotypes must be unique",
            id="2 mutations (any sex) - duplicate genotypes",
        ),
    ],
)
def test_invalid_genotype_formsets(formset_params, mutation_names, expected_msg):

    formset_data = create_formset_data(formset_params)
    formset = GenotypeFormSet(
        formset_data,
        form_kwargs={"mutation_names": mutation_names},
    )

    assertFormSetError(formset, form_index=None, field=None, errors=[expected_msg])
