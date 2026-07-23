import os
from enum import StrEnum

import pandas as pd
from django.http import Http404
from oscar_colony.breeding_scheme import Genotype
from oscar_colony.colony_management.pyrat.api import get_pyrat_data
from oscar_colony.colony_management.pyrat.api import get_pyrat_line_mutations
from oscar_colony.colony_management.pyrat.api import get_pyrat_lines
from oscar_colony.colony_management.pyrat.standardise import standardise_pyrat_csv
from oscar_colony.historical_stats import calculate_historical_stats_for_line
from oscar_colony.optimise.optimal_scheme_calculator import calculate_optimal_scheme


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

    def get_line_stats(self, line_name):

        # Fetch all available animal data for the line (no date restrictions)
        animal_data = get_pyrat_data(
            species_name="Mouse",
            line_name=line_name,
        )

        standardised_dfs = []
        for animal_df in animal_data:
            if len(standardised_dfs) == 0 and animal_df.empty:
                msg = "No animals found for chosen line"
                raise Http404(msg)

            standard_df = standardise_pyrat_csv(animal_df)
            standardised_dfs.append(standard_df)

        merged_df = pd.concat(standardised_dfs)
        if merged_df.empty:
            msg = "No animals remain for chosen line after standardisation"
            raise Http404(msg)

        return calculate_historical_stats_for_line(merged_df, line_name)

    def optimise_schemes(self, line_stats, genotype_form_data):

        # Get names of line mutations. This is the mutation order
        # we must match in required_n_per_genotype
        mutation_names = line_stats.mutations

        # Take genotype form data and re-arrange it into the format
        # required for calculate_optimal_scheme
        required_n_per_genotype = {}
        for genotype_data in genotype_form_data:
            genotype = []
            for mutation_name in mutation_names:
                mutation_value = genotype_data[mutation_name]
                genotype.append(Genotype[mutation_value])

            required_n_per_genotype[tuple(genotype)] = genotype_data["count"]

        try:
            breeding_schemes, surplus = calculate_optimal_scheme(
                required_n_per_genotype, line_stats=line_stats, default_litter_size=6
            )
        except ValueError as exc:
            msg = "Optimisation failed for this line / genotypes combination."
            raise Http404(msg) from exc

        # Convert breeding schemes into a table for easier viewing
        breeding_schemes = pd.DataFrame(
            breeding_schemes.items(),
            columns=("Scheme", "N matings"),
            dtype=str,
        )

        return breeding_schemes, surplus
