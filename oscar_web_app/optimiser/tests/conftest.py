import pytest


@pytest.fixture
def colony_software_pyrat(settings):
    """Use the PYRAT colony software"""

    settings.COLONY_SOFTWARE = "PYRAT"
