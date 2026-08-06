from typing import TYPE_CHECKING
from typing import Any

import pandas as pd
from django.http import Http404
from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render

from .colony_management import get_colony
from .forms import GenotypeFormSet
from .forms import LineForm

if TYPE_CHECKING:
    from oscar_colony.breeding_scheme import BreedingScheme
    from oscar_colony.historical_stats import LineStatistics
    from oscar_colony.optimise.surplus_summary import SurplusSummary


def select_line(request: HttpRequest) -> HttpResponse:

    if request.method == "POST":
        form = LineForm(request.POST)
        if form.is_valid():
            line_id = int(form.cleaned_data["line"])
            line_name = dict(form.fields["line"].choices)[line_id]
            request.session[line_id] = line_name
            return redirect("optimiser:select_genotypes", line_id=line_id)

    else:
        form = LineForm()

    return render(request, "optimiser/select_line.html", {"form": form})


def select_genotypes(request: HttpRequest, line_id: int) -> HttpResponse:

    # Fetch mutation names to create custom fields in the Genotype forms
    mutations = get_colony().get_line_mutations(line_id)
    if len(mutations) == 0:
        msg = "No mutations found for chosen line"
        raise Http404(msg)

    error_messages = {"too_few_forms": "Please provide at least one genotype"}

    if request.method == "POST":
        formset = GenotypeFormSet(
            request.POST,
            form_kwargs={"mutation_names": mutations},
            error_messages=error_messages,
        )
        if formset.is_valid():
            # Fetch line name from session data. If not present, fetch
            # via the colony software API
            line_name = request.session.get(str(line_id))
            if line_name is None:
                line_name = get_colony().get_line_name(line_id)

            # Run optimisation calculations and render the results
            context = create_result_page_context(line_name, formset)
            return render(
                request,
                "optimiser/result.html",
                context,
            )

    else:
        formset = GenotypeFormSet(
            form_kwargs={"mutation_names": mutations}, error_messages=error_messages
        )

    return render(request, "optimiser/select_genotypes.html", {"formset": formset})


def _strip_decimal_places(input_value: float) -> str:
    return f"{input_value:.0f}"


def _convert_to_html_table(
    df: pd.DataFrame, *, format_float_as_int: bool = False
) -> str:
    """Convert a Pandas DataFrame into an HTML table.

    Parameters
    ----------
    df : pd.DataFrame
        Pandas DataFrame to convert
    format_float_as_int : bool, optional
        If True, decimal places will be stripped from all float values e.g.
        6.0 -> 6

    Returns
    -------
    str
        HTML table
    """

    float_format = _strip_decimal_places if format_float_as_int else None

    return df.to_html(
        classes=[
            "table",
            "table-striped",
            "table-bordered",
            "text-center",
            "align-middle",
        ],
        index=False,
        justify="center",
        na_rep="",
        float_format=float_format,
    )


def create_result_page_context(
    line_name: str, formset: GenotypeFormSet
) -> dict[str, Any]:
    """
    Run the optimisation calculations for the given line_name, and create
    a context dict with required values for the results page.

    Parameters
    ----------
    line_name : str
        Name of the line
    formset : GenotypeFormSet
        The completed genotype formset for this line

    Returns
    -------
    dict[str, Any]
        Context required for results page
    """
    colony_management = get_colony()
    line_stats = colony_management.get_line_stats(line_name)
    schemes, surplus = colony_management.optimise_schemes(line_stats, formset)

    stats_context = create_line_stats_context(line_stats)
    scheme_context = create_schemes_context(schemes, surplus)

    return stats_context | scheme_context


def create_line_stats_context(
    line_stats: LineStatistics, decimal_places: int = 2
) -> dict[str, Any]:
    """Create context with values from the given LineStatistics.

    Parameters
    ----------
    line_stats : LineStatistics
        Historical stats for the line.
    decimal_places : int, optional
        Number of decimal places to round values to.

    Returns
    -------
    dict[str, Any]
        Context dict
    """

    n_per_genotype_df = _convert_to_html_table(line_stats.create_n_per_genotype_df())
    scheme_summary_df = _convert_to_html_table(
        line_stats.create_scheme_summary_df(decimal_places)
    )
    scheme_number_df = _convert_to_html_table(
        line_stats.create_scheme_number_df(), format_float_as_int=True
    )
    scheme_proportion_df = _convert_to_html_table(
        line_stats.create_scheme_proportion_df(decimal_places)
    )

    return {
        "line_name": line_stats.line_name,
        "mutations": line_stats.mutations,
        "stats_total_n": line_stats.total_n_offspring,
        "stats_genotyped_n": line_stats.total_n_genotyped_offspring,
        "stats_matings_n": line_stats.total_n_successful_matings,
        "stats_litter_size": round(line_stats.average_litter_size, decimal_places),
        "stats_genotype_table": n_per_genotype_df,
        "stats_scheme_summary_table": scheme_summary_df,
        "stats_scheme_number_table": scheme_number_df,
        "stats_scheme_proportion_table": scheme_proportion_df,
    }


def create_schemes_context(
    schemes: dict[BreedingScheme, int], surplus: SurplusSummary, decimal_places: int = 2
) -> dict[str, Any]:
    """Create context with values from calculated breeding schemes / surplus.

    Parameters
    ----------
    schemes : dict[BreedingScheme, int]
        Calculated breeding schemes
    surplus : SurplusSummary
        Calculated surplus
    decimal_places : int, optional
        Number of decimal places to round values to.

    Returns
    -------
    dict[str, Any]
        Context dict
    """

    # Convert breeding schemes into a table for easier viewing
    scheme_table = pd.DataFrame(
        schemes.items(),
        columns=("Scheme", "N matings"),
        dtype=str,
    )
    scheme_table = _convert_to_html_table(scheme_table)

    surplus_genotype_table = surplus.create_genotype_df(decimal_places)
    surplus_genotype_table = _convert_to_html_table(surplus_genotype_table)

    return {
        "scheme_table": scheme_table,
        "total_n": round(surplus.total_n, decimal_places),
        "total_surplus": round(surplus.total_n_surplus, decimal_places),
        "required_n": round(surplus.total_n - surplus.total_n_surplus, decimal_places),
        "surplus_genotype_table": surplus_genotype_table,
    }
