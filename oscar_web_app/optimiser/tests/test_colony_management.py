import re

import pytest
from django.http import Http404
from oscar_colony.historical_stats import LineStatistics

from oscar_web_app.optimiser.colony_management import ColonyDev
from oscar_web_app.optimiser.colony_management import ColonyPyRAT
from oscar_web_app.optimiser.colony_management import get_colony
from oscar_web_app.optimiser.forms import GenotypeFormSet


@pytest.mark.parametrize(
    ("colony_software", "expected_colony"), [("DEV", ColonyDev), ("PYRAT", ColonyPyRAT)]
)
def test_get_valid_colony(colony_software, expected_colony, settings):
    settings.COLONY_SOFTWARE = colony_software
    colony = get_colony()

    assert isinstance(colony, expected_colony)


def test_get_invalid_colony(settings):
    settings.COLONY_SOFTWARE = "FAKE-COLONY"

    error_msg = re.escape("COLONY_SOFTWARE should be set to one of ['DEV', 'PYRAT']")
    with pytest.raises(NotImplementedError, match=error_msg):
        get_colony()


def test_optimise_invalid_scheme():
    """
    Test failed optimisations raise a 404 exception with an
    appropriate message.
    """

    line_name = "Line-A"
    mutation_names = ["Mut-A"]

    # line statistics with default, empty values
    line_stats = LineStatistics(line_name=line_name, mutations=mutation_names)

    # formset asking for 5 WT
    formset_data = {
        "form-TOTAL_FORMS": 1,
        "form-INITIAL_FORMS": 0,
        "form-MIN_NUM_FORMS": 1,
        "form-MAX_NUM_FORMS": 1000,
        "form-0-Mut-A": "WT",
        "form-0-count": 5,
    }
    formset = GenotypeFormSet(
        formset_data,
        form_kwargs={"mutation_names": mutation_names},
    )
    formset.is_valid()

    error_msg = "Optimisation failed for this line / genotypes combination"
    with pytest.raises(Http404, match=error_msg):
        get_colony().optimise_schemes(line_stats, formset)


@pytest.mark.usefixtures("colony_software_pyrat")
def test_get_pyrat_lines(mocker):
    mocker.patch(
        "oscar_web_app.optimiser.colony_management.ColonyPyRAT.get_lines",
        return_value=["Line-A", "Line-B"],
    )

    # check called once
    get_colony().get_lines()
