from abc import ABC
from abc import abstractmethod
from enum import StrEnum
from typing import TYPE_CHECKING

import pandas as pd
from django.conf import settings
from django.http import Http404
from oscar_colony.breeding_scheme import BreedingScheme
from oscar_colony.breeding_scheme import Genotype
from oscar_colony.colony_management.pyrat.api import get_pyrat_data
from oscar_colony.colony_management.pyrat.api import get_pyrat_line_mutations
from oscar_colony.colony_management.pyrat.api import get_pyrat_line_name
from oscar_colony.colony_management.pyrat.api import get_pyrat_lines
from oscar_colony.colony_management.pyrat.standardise import standardise_pyrat_csv
from oscar_colony.historical_stats import BreedingSchemeStatistics
from oscar_colony.historical_stats import LineStatistics
from oscar_colony.historical_stats import calculate_historical_stats_for_line
from oscar_colony.optimise.optimal_scheme_calculator import SurplusSummary
from oscar_colony.optimise.optimal_scheme_calculator import calculate_optimal_scheme

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .forms import GenotypeFormSet


class ColonySoftware(StrEnum):
    """Supported colony management software"""

    DEV = "DEV"  # dev return fake colony data
    PYRAT = "PYRAT"


def get_colony() -> ColonyManagement:
    """
    Return the ColonyManagement class matching the COLONY_SOFTWARE setting.
    """

    match settings.COLONY_SOFTWARE:
        case ColonySoftware.DEV:
            return ColonyDev()

        case ColonySoftware.PYRAT:
            return ColonyPyRAT()

        case _:
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
    def get_line_name(self, line_id: int) -> str:
        pass

    @abstractmethod
    def get_line_mutations(self, line_id: int) -> list[str]:
        pass

    @abstractmethod
    def get_line_stats(self, line_name: str) -> LineStatistics:
        pass

    def optimise_schemes(
        self, line_stats: LineStatistics, genotype_formset: GenotypeFormSet
    ) -> tuple[dict[BreedingScheme, int], SurplusSummary]:
        """
        Calculate optimal breeding schemes for the given line.

        Parameters
        ----------
        line_stats : LineStatistics
            Historical stats for the line.
        genotype_formset : GenotypeFormset
            The completed genotype formset for this line.

        Returns
        -------
        tuple[dict[BreedingScheme, int], SurplusSummary]
            Returns 2 items:
            - optimal number of matings per breeding scheme
            - a summary of the surplus numbers for this optimal scheme
              combination
        """

        # Get names of line mutations. This is the mutation order
        # we must match in required_n_per_genotype
        mutation_names = line_stats.mutations

        # Take genotype form data and re-arrange it into the format
        # required for calculate_optimal_scheme
        required_n_per_genotype = {}
        genotype_form_data = [form.cleaned_data for form in genotype_formset]

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

        return breeding_schemes, surplus


class ColonyPyRAT(ColonyManagement):
    """
    Class to interact with colony data from pyRAT.
    """

    def get_lines(self) -> Iterator[pd.DataFrame]:
        """Get names and ids of available lines"""
        return get_pyrat_lines()

    def get_line_name(self, line_id: int) -> str:
        return get_pyrat_line_name(line_id)

    def get_line_mutations(self, line_id: int) -> list[str]:
        """Get names of mutations for the given line"""

        return get_pyrat_line_mutations(line_id)

    def get_line_stats(self, line_name: str) -> LineStatistics:
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

    _line_id_to_stats = {
        1: LineStatistics(
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
        ),
        2: LineStatistics(
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
        ),
        3: LineStatistics(
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
        ),
    }

    def get_lines(self) -> Iterator[pd.DataFrame]:
        """Get names and ids of available lines"""

        columns = {"name": [], "id": []}
        for line_id, line_stats in self._line_id_to_stats.items():
            columns["name"].append(line_stats.line_name)
            columns["id"].append(line_id)

        return [pd.DataFrame(columns)]

    def get_line_name(self, line_id: int) -> str:
        return self._line_id_to_stats[line_id].line_name

    def get_line_mutations(self, line_id: int) -> list[str]:
        """Get names of mutations for the given line"""

        return self._line_id_to_stats[line_id].mutations

    def get_line_stats(self, line_name: str) -> LineStatistics:
        """Get historical stats for the given line"""

        for line_stats in self._line_id_to_stats.values():
            if line_stats.line_name == line_name:
                return line_stats

        msg = f"line stats not found for line name: {line_name}"
        raise ValueError(msg)
