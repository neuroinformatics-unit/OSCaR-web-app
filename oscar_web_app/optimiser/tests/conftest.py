import pytest


@pytest.fixture(autouse=True)
def colony_software_dev(settings):
    """Force use of the DEV colony software"""

    settings.COLONY_SOFTWARE = "DEV"
