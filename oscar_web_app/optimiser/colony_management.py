import os
from abc import ABC
from abc import abstractmethod
from enum import StrEnum
from typing import TYPE_CHECKING

import pandas as pd
from django.http import Http404
from oscar_colony.breeding_scheme import BreedingScheme
from oscar_colony.breeding_scheme import Genotype
from oscar_colony.colony_management.pyrat.api import get_pyrat_data
from oscar_colony.colony_management.pyrat.api import get_pyrat_line_mutations
from oscar_colony.colony_management.pyrat.api import get_pyrat_lines
from oscar_colony.colony_management.pyrat.standardise import standardise_pyrat_csv
from oscar_colony.historical_stats import BreedingSchemeStatistics
from oscar_colony.historical_stats import LineStatistics
from oscar_colony.historical_stats import calculate_historical_stats_for_line
from oscar_colony.optimise.optimal_scheme_calculator import calculate_optimal_scheme

if TYPE_CHECKING:
    from collections.abc import Iterator


class ColonySoftware(StrEnum):
    """Supported colony management software"""

    DEV = "DEV"  # dev return fake colony data
    PYRAT = "PYRAT"


def get_colony() -> ColonyManagement:
    """
    Return the ColonyManagement class matching the COLONY_SOFTWARE env variable.
    """

    colony_env = os.environ.get("COLONY_SOFTWARE", "DEV")
    if colony_env == ColonySoftware.DEV:
        return ColonyDev()
    if colony_env == ColonySoftware.PYRAT:
        return ColonyPyRAT()

    msg = (
        f"COLONY_SOFTWARE should be set to one of "
        f"{[software.name for software in ColonySoftware]}"
    )
    raise NotImplementedError(msg)


class ColonyManagement(ABC):
    """
    Abstract base class to interface with different colony management software
    via oscar_colony
    """

    @abstractmethod
    def get_lines(self) -> Iterator[pd.DataFrame]:
        pass

    @abstractmethod
    def get_line_mutations(self, line_id) -> list[str]:
        pass

    @abstractmethod
    def get_line_stats(self, line_name) -> LineStatistics:
        pass

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


class ColonyPyRAT(ColonyManagement):
    """
    Class to interact with colony data from pyRAT.
    """

    def get_lines(self) -> Iterator[pd.DataFrame]:
        """Get names and ids of available lines"""

        return get_pyrat_lines()

    def get_line_mutations(self, line_id) -> list[str]:
        """Get names of mutations for the given line"""

        return get_pyrat_line_mutations(line_id)

    def get_line_stats(self, line_name) -> LineStatistics:
        """Get historical stats for the given line"""

        # Fetch all available animal data for the line (no date restrictions)
        animal_data = get_pyrat_data(
            species_name="Mouse",
            line_name=line_name,
        )

        # Standardise all fetched data
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

        # Calculate historical stats across all standardised data
        return calculate_historical_stats_for_line(merged_df, line_name)


class ColonyDev(ColonyManagement):
    """
    For development, this class returns fake colony data.
    """

    def get_lines(self) -> Iterator[pd.DataFrame]:
        """Get names and ids of available lines"""

        return [
            pd.DataFrame({"name": ["Line-A", "Line-AB", "Line-ABC"], "id": [1, 2, 3]})
        ]

    def get_line_mutations(self, line_id) -> list[str]:
        """Get names of mutations for the given line"""

        if line_id == 1:
            return ["Mut-A"]
        if line_id == 2:  # noqa: PLR2004
            return ["Mut-A", "Mut-B"]
        return ["Mut-A", "Mut-B", "Mut-C"]

    def get_line_stats(self, line_name) -> LineStatistics:

        if line_name == "Line-A":
            return LineStatistics(
                line_name="Line-A",
                mutations=["Mut-A"],
                n_mutations=1,
                total_n_offspring=18,
                total_n_genotyped_offspring=18,
                total_n_offspring_per_genotype={
                    (Genotype.WT,): 6,
                    (Genotype.HET,): 10,
                    (Genotype.HOM,): 2,
                },
                total_n_successful_matings=9,
                average_litter_size=2,
                stats_per_breeding_scheme={
                    BreedingScheme("wt", "het"): BreedingSchemeStatistics(
                        n_breeding_pairs=2,
                        n_successful_matings=3,
                        average_litter_size=2.666,
                        average_n_litters_per_pair=1.5,
                        total_n_offspring=8,
                        total_n_genotyped_offspring=8,
                        n_offspring_per_genotype={
                            (Genotype.WT,): 4,
                            (Genotype.HET,): 4,
                        },
                        proportion_offspring_per_genotype={
                            (Genotype.WT,): 0.5,
                            (Genotype.HET,): 0.5,
                        },
                    ),
                    BreedingScheme("wt", "hom"): BreedingSchemeStatistics(
                        n_breeding_pairs=2,
                        n_successful_matings=2,
                        average_litter_size=2,
                        average_n_litters_per_pair=1.0,
                        total_n_offspring=4,
                        total_n_genotyped_offspring=4,
                        n_offspring_per_genotype={(Genotype.HET,): 4},
                        proportion_offspring_per_genotype={(Genotype.HET,): 1.0},
                    ),
                    BreedingScheme("het", "het"): BreedingSchemeStatistics(
                        n_breeding_pairs=2,
                        n_successful_matings=2,
                        average_litter_size=2,
                        average_n_litters_per_pair=1.0,
                        total_n_offspring=4,
                        total_n_genotyped_offspring=4,
                        n_offspring_per_genotype={
                            (Genotype.WT,): 2,
                            (Genotype.HET,): 1,
                            (Genotype.HOM,): 1,
                        },
                        proportion_offspring_per_genotype={
                            (Genotype.WT,): 0.5,
                            (Genotype.HET,): 0.25,
                            (Genotype.HOM,): 0.25,
                        },
                    ),
                    BreedingScheme("het", "hom"): BreedingSchemeStatistics(
                        n_breeding_pairs=2,
                        n_successful_matings=2,
                        average_litter_size=1.0,
                        average_n_litters_per_pair=1.0,
                        total_n_offspring=2,
                        total_n_genotyped_offspring=2,
                        n_offspring_per_genotype={
                            (Genotype.HET,): 1,
                            (Genotype.HOM,): 1,
                        },
                        proportion_offspring_per_genotype={
                            (Genotype.HET,): 0.5,
                            (Genotype.HOM,): 0.5,
                        },
                    ),
                },
            )

        if line_name == "Line-AB":
            return LineStatistics(
                line_name="Line-AB",
                mutations=["Mut-A", "Mut-B"],
                n_mutations=2,
                total_n_offspring=20,
                total_n_genotyped_offspring=20,
                total_n_offspring_per_genotype={
                    (Genotype.HOM, Genotype.HOM): 2,
                    (Genotype.HET, Genotype.HOM): 6,
                    (Genotype.HOM, Genotype.HET): 4,
                    (Genotype.HET, Genotype.WT): 2,
                    (Genotype.WT, Genotype.HET): 2,
                    (Genotype.HET, Genotype.HET): 4,
                },
                total_n_successful_matings=10,
                average_litter_size=2,
                stats_per_breeding_scheme={
                    BreedingScheme("het_hom", "hom_het"): BreedingSchemeStatistics(
                        n_breeding_pairs=2,
                        n_successful_matings=3,
                        average_litter_size=2.666,
                        average_n_litters_per_pair=1.5,
                        total_n_offspring=8,
                        total_n_genotyped_offspring=8,
                        n_offspring_per_genotype={
                            (Genotype.HOM, Genotype.HOM): 2,
                            (Genotype.HET, Genotype.HOM): 6,
                        },
                        proportion_offspring_per_genotype={
                            (Genotype.HOM, Genotype.HOM): 0.25,
                            (Genotype.HET, Genotype.HOM): 0.75,
                        },
                    ),
                    BreedingScheme("hom_wt", "het_het"): BreedingSchemeStatistics(
                        n_breeding_pairs=2,
                        n_successful_matings=2,
                        average_litter_size=2.0,
                        average_n_litters_per_pair=1.0,
                        total_n_offspring=4,
                        total_n_genotyped_offspring=4,
                        n_offspring_per_genotype={
                            (
                                Genotype.HOM,
                                Genotype.HET,
                            ): 4
                        },
                        proportion_offspring_per_genotype={
                            (
                                Genotype.HOM,
                                Genotype.HET,
                            ): 1.0
                        },
                    ),
                    BreedingScheme("het_wt", "wt_het"): BreedingSchemeStatistics(
                        n_breeding_pairs=2,
                        n_successful_matings=2,
                        average_litter_size=1.5,
                        average_n_litters_per_pair=1.0,
                        total_n_offspring=3,
                        total_n_genotyped_offspring=3,
                        n_offspring_per_genotype={
                            (Genotype.HET, Genotype.WT): 2,
                            (Genotype.WT, Genotype.HET): 1,
                        },
                        proportion_offspring_per_genotype={
                            (Genotype.HET, Genotype.WT): 0.666,
                            (Genotype.WT, Genotype.HET): 0.333,
                        },
                    ),
                    BreedingScheme("het_wt", "wt_hom"): BreedingSchemeStatistics(
                        n_breeding_pairs=2,
                        n_successful_matings=2,
                        average_litter_size=1.0,
                        average_n_litters_per_pair=1.0,
                        total_n_offspring=2,
                        total_n_genotyped_offspring=2,
                        n_offspring_per_genotype={
                            (
                                Genotype.WT,
                                Genotype.HET,
                            ): 1,
                            (
                                Genotype.HET,
                                Genotype.HET,
                            ): 1,
                        },
                        proportion_offspring_per_genotype={
                            (Genotype.WT, Genotype.HET): 0.5,
                            (Genotype.HET, Genotype.HET): 0.5,
                        },
                    ),
                    BreedingScheme("hom_wt", "wt_hom"): BreedingSchemeStatistics(
                        n_breeding_pairs=1,
                        n_successful_matings=1,
                        average_litter_size=3.0,
                        average_n_litters_per_pair=1.0,
                        total_n_offspring=3,
                        total_n_genotyped_offspring=3,
                        n_offspring_per_genotype={
                            (
                                Genotype.HET,
                                Genotype.HET,
                            ): 3,
                        },
                        proportion_offspring_per_genotype={
                            (Genotype.HET, Genotype.HET): 1,
                        },
                    ),
                },
            )

        return LineStatistics(
            line_name="Line-ABC",
            mutations=["Mut-A", "Mut-B", "Mut-C"],
            n_mutations=3,
            total_n_offspring=20,
            total_n_genotyped_offspring=20,
            total_n_offspring_per_genotype={
                (Genotype.HET, Genotype.WT, Genotype.HOM): 10,
                (Genotype.WT, Genotype.HET, Genotype.HOM): 2,
                (Genotype.WT, Genotype.WT, Genotype.HET): 1,
                (Genotype.HET, Genotype.WT, Genotype.HET): 1,
                (Genotype.WT, Genotype.HET, Genotype.WT): 2,
                (Genotype.WT, Genotype.HET, Genotype.HET): 1,
                (Genotype.HET, Genotype.HET, Genotype.WT): 2,
                (Genotype.HET, Genotype.HET, Genotype.HET): 1,
            },
            total_n_successful_matings=10,
            average_litter_size=2,
            stats_per_breeding_scheme={
                BreedingScheme("wt_wt_het", "het_het_het"): BreedingSchemeStatistics(
                    n_breeding_pairs=2,
                    n_successful_matings=3,
                    average_litter_size=2.666,
                    average_n_litters_per_pair=1.5,
                    total_n_offspring=8,
                    total_n_genotyped_offspring=8,
                    n_offspring_per_genotype={
                        (Genotype.HET, Genotype.WT, Genotype.HOM): 6,
                        (Genotype.WT, Genotype.HET, Genotype.HOM): 2,
                    },
                    proportion_offspring_per_genotype={
                        (Genotype.HET, Genotype.WT, Genotype.HOM): 0.75,
                        (Genotype.WT, Genotype.HET, Genotype.HOM): 0.25,
                    },
                ),
                BreedingScheme("wt_het_het", "het_het_hom"): BreedingSchemeStatistics(
                    n_breeding_pairs=2,
                    n_successful_matings=2,
                    average_litter_size=2.0,
                    average_n_litters_per_pair=1.0,
                    total_n_offspring=4,
                    total_n_genotyped_offspring=4,
                    n_offspring_per_genotype={
                        (Genotype.HET, Genotype.WT, Genotype.HOM): 4
                    },
                    proportion_offspring_per_genotype={
                        (Genotype.HET, Genotype.WT, Genotype.HOM): 1.0,
                    },
                ),
                BreedingScheme("het_wt_wt", "wt_het_hom"): BreedingSchemeStatistics(
                    n_breeding_pairs=2,
                    n_successful_matings=2,
                    average_litter_size=1.5,
                    average_n_litters_per_pair=1.0,
                    total_n_offspring=3,
                    total_n_genotyped_offspring=3,
                    n_offspring_per_genotype={
                        (Genotype.WT, Genotype.WT, Genotype.HET): 1,
                        (Genotype.HET, Genotype.WT, Genotype.HET): 1,
                        (Genotype.WT, Genotype.HET, Genotype.HET): 1,
                    },
                    proportion_offspring_per_genotype={
                        (Genotype.WT, Genotype.WT, Genotype.HET): 0.333,
                        (Genotype.HET, Genotype.WT, Genotype.HET): 0.333,
                        (Genotype.WT, Genotype.HET, Genotype.HET): 0.333,
                    },
                ),
                BreedingScheme("het_wt_wt", "wt_hom_het"): BreedingSchemeStatistics(
                    n_breeding_pairs=2,
                    n_successful_matings=2,
                    average_litter_size=1.0,
                    average_n_litters_per_pair=1.0,
                    total_n_offspring=2,
                    total_n_genotyped_offspring=2,
                    n_offspring_per_genotype={
                        (Genotype.WT, Genotype.HET, Genotype.WT): 2,
                    },
                    proportion_offspring_per_genotype={
                        (Genotype.WT, Genotype.HET, Genotype.WT): 1.0,
                    },
                ),
                BreedingScheme("wt_hom_het", "hom_wt_wt"): BreedingSchemeStatistics(
                    n_breeding_pairs=1,
                    n_successful_matings=1,
                    average_litter_size=3.0,
                    average_n_litters_per_pair=1.0,
                    total_n_offspring=3,
                    total_n_genotyped_offspring=3,
                    n_offspring_per_genotype={
                        (Genotype.HET, Genotype.HET, Genotype.WT): 2,
                        (Genotype.HET, Genotype.HET, Genotype.HET): 1,
                    },
                    proportion_offspring_per_genotype={
                        (Genotype.HET, Genotype.HET, Genotype.WT): 0.666,
                        (Genotype.HET, Genotype.HET, Genotype.HET): 0.333,
                    },
                ),
            },
        )
