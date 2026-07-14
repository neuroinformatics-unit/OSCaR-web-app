import os
from enum import StrEnum

import pandas as pd
from oscar_colony.colony_management.pyrat.api import get_pyrat_line_mutations
from oscar_colony.colony_management.pyrat.api import get_pyrat_lines


class ColonySoftware(StrEnum):
    """Supported colony management software"""

    DEV = "DEV"  # dev return fake colony data
    PYRAT = "PYRAT"


class ColonyManagement:
    """
    Class to interface with different colony management software
    via oscar_colony
    """

    def __init__(self):
        colony_env = os.environ.get("COLONY_SOFTWARE", "DEV")
        if colony_env in ColonySoftware:
            self.colony_software = ColonySoftware[colony_env]
        else:
            msg = (
                f"COLONY_SOFTWARE should be set to one of "
                f"{[software.name for software in ColonySoftware]}"
            )
            raise NotImplementedError(msg)

    def get_lines(self):
        """Get names and ids of available lines"""

        if self.colony_software == ColonySoftware.PYRAT:
            lines = get_pyrat_lines()
        else:
            lines = [
                pd.DataFrame({"name": ["Line-A", "Line-B", "Line-C"], "id": [1, 2, 3]})
            ]

        return lines

    def get_line_mutations(self, line_id):
        """Get names of mutations for the given line"""

        if self.colony_software == ColonySoftware.PYRAT:
            lines = get_pyrat_line_mutations(line_id)
        elif line_id == 1:
            lines = ["Mut-A"]
        elif line_id == 2:  # noqa: PLR2004
            lines = ["Mut-A", "Mut-B"]
        else:
            lines = ["Mut-A", "Mut-B", "Mut-C"]

        return lines
