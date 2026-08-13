import pytest
from pytest_django.asserts import assertFormSetError

from oscar_web_app.optimiser.forms import GenotypeFormSet


@pytest.mark.parametrize(
    ("formset_data", "mutation_names"),
    [
        pytest.param(
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
            ["Mut-A"],
            id="1 mutation",
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
                "form-1-DELETE": "on",
            },
            ["Mut-A"],
            id="1 mutation - duplicate genotypes marked for deletion",
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
                "form-1-Mut-A": "HET",
                "form-1-Mut-B": "HET",
                "form-1-count": 10,
            },
            ["Mut-A", "Mut-B"],
            id="2 mutations",
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
                "form-1-DELETE": "on",
            },
            ["Mut-A", "Mut-B"],
            id="2 mutations - duplicate genotypes marked for deletion",
        ),
    ],
)
def test_valid_genotype_formsets(formset_data, mutation_names):
    formset = GenotypeFormSet(
        formset_data,
        form_kwargs={"mutation_names": mutation_names},
    )
    assert formset.is_valid()
    assert sorted(formset[0].fields.keys()) == sorted(
        ["DELETE", "count", *mutation_names]
    )


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
            ["Mut-A"],
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
