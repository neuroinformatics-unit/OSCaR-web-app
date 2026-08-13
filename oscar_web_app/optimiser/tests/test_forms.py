from pytest_django.asserts import assertFormSetError

from oscar_web_app.optimiser.forms import GenotypeFormSet

# ruff: noqa: PLR2004


def test_valid_genotype_formset():
    data = {
        "form-TOTAL_FORMS": 2,
        "form-INITIAL_FORMS": 0,
        "form-MIN_NUM_FORMS": 1,
        "form-MAX_NUM_FORMS": 1000,
        "form-0-Mut-A": "WT",
        "form-0-count": 5,
        "form-1-Mut-A": "HET",
        "form-1-count": 10,
    }

    formset = GenotypeFormSet(
        data,
        form_kwargs={"mutation_names": ["Mut-A"]},
    )
    assert formset.is_valid()
    assert len(formset) == 2


def test_not_enough_genotype_forms():
    data = {
        "form-TOTAL_FORMS": 1,
        "form-INITIAL_FORMS": 0,
        "form-MIN_NUM_FORMS": 1,
        "form-MAX_NUM_FORMS": 1000,
        "form-0-Mut-A": "WT",
        "form-0-count": 1,
        "form-0-DELETE": "on",
    }

    formset = GenotypeFormSet(
        data,
        form_kwargs={"mutation_names": ["Mut-A"]},
    )

    assertFormSetError(
        formset, form_index=None, field=None, errors=["Please submit at least 1 form."]
    )


def test_duplicate_genotypes():
    data = {
        "form-TOTAL_FORMS": 2,
        "form-INITIAL_FORMS": 0,
        "form-MIN_NUM_FORMS": 1,
        "form-MAX_NUM_FORMS": 1000,
        "form-0-Mut-A": "HET",
        "form-0-count": 5,
        "form-1-Mut-A": "HET",
        "form-1-count": 20,
    }

    formset = GenotypeFormSet(
        data,
        form_kwargs={"mutation_names": ["Mut-A"]},
    )

    assertFormSetError(
        formset, form_index=None, field=None, errors=["All genotypes must be unique"]
    )


def test_duplicate_genotypes_no_deleted():
    data = {
        "form-TOTAL_FORMS": 2,
        "form-INITIAL_FORMS": 0,
        "form-MIN_NUM_FORMS": 1,
        "form-MAX_NUM_FORMS": 1000,
        "form-0-Mut-A": "HET",
        "form-0-count": 5,
        "form-1-Mut-A": "HET",
        "form-1-count": 20,
        "form-1-DELETE": "on",
    }

    formset = GenotypeFormSet(
        data,
        form_kwargs={"mutation_names": ["Mut-A"]},
    )

    assertFormSetError(
        formset, form_index=None, field=None, errors=["All genotypes must be unique"]
    )
