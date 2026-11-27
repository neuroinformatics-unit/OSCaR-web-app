import math
from typing import TYPE_CHECKING
from typing import Any

import pandas as pd
from django.contrib import messages
from django.shortcuts import redirect
from django.shortcuts import render

from oscar_web_app.optimiser.colony_management import ProcessingError

from .colony_management import get_colony
from .forms import GenotypeFormSet
from .forms import LineForm
from .forms import LineStatisticsForm

if TYPE_CHECKING:
    from django.http import HttpRequest
    from django.http import HttpResponse

    from .colony_management import BaseFormSet
    from .colony_management import GenotypeForm


def select_line(request: HttpRequest) -> HttpResponse:

    if request.method == "POST":
        form = LineForm(request.POST)

        if form.is_valid():
            line_id = form.cleaned_data["line"]

            # If the blank option is selected - render select genotypes with no context.
            # This will clear both the genotype form + results area.
            if line_id == "":
                return render(
                    request,
                    "optimiser/breeding_plan/genotype_section.html",
                    {},
                )

            line_id = int(form.cleaned_data["line"])
            line_name = dict(form.fields["line"].choices)[line_id]  # type: ignore[attr-defined]
            request.session[str(line_id)] = line_name
            return redirect("optimiser:select_genotypes", line_id=line_id)

    else:
        form = LineForm()

    return render(request, "optimiser/breeding_plan/breeding_plan.html", {"form": form})


def select_genotypes(request: HttpRequest, line_id: int) -> HttpResponse:

    # Fetch mutation names to create custom fields in the Genotype forms
    mutations = get_colony().get_line_mutations(line_id)
    if len(mutations) == 0:
        messages.error(request, "No mutations found for chosen line")
        return render(request, "optimiser/breeding_plan/genotype_section.html", {})

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
            context = _create_optimisation_result_context(request, line_name, formset)
            return render(
                request,
                "optimiser/breeding_plan/optimisation_result.html",
                context,
            )

        # show the invalid formset with any errors displayed
        response = render(
            request,
            "optimiser/breeding_plan/genotype_section.html",
            {"formset": formset},
        )
        response["HX-Retarget"] = "#genotype-form-container"
        return response

    # show the empty formset
    formset = GenotypeFormSet(
        form_kwargs={"mutation_names": mutations}, error_messages=error_messages
    )
    return render(
        request, "optimiser/breeding_plan/genotype_section.html", {"formset": formset}
    )


def line_statistics(request: HttpRequest) -> HttpResponse:

    if request.method == "POST":
        form = LineStatisticsForm(request.POST)
        if form.is_valid():
            # Run line statistics calculations and render the results
            context = _create_line_stats_context(request, form)
            return render(
                request,
                "optimiser/line_stats/result.html",
                context,
            )

        # show the invalid form with any errors displayed
        response = render(
            request, "optimiser/line_stats/form_section.html", {"form": form}
        )
        response["HX-Retarget"] = "#line-stats-form-container"
        return response

    # show the empty form
    form = LineStatisticsForm()
    return render(request, "optimiser/line_stats/line_stats.html", {"form": form})


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


def _create_optimisation_result_context(
    request: HttpRequest,
    line_name: str,
    formset: BaseFormSet[GenotypeForm],
    decimal_places: int = 2,
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
    decimal_places: int
        Number of decimal places to round values to.

    Returns
    -------
    dict[str, Any]
        Context required for results page
    """
    colony_management = get_colony()
    context = {"formset": formset}

    try:
        line_stats = colony_management.get_line_stats(line_name)
    except ProcessingError as e:
        messages.error(request, str(e))
        return context

    try:
        schemes, surplus = colony_management.optimise_schemes(line_stats, formset)
    except ProcessingError as e:
        messages.error(request, str(e))
        return context

    # Convert breeding schemes into a table for easier viewing
    scheme_table = pd.DataFrame(
        schemes.items(),
        columns=("Scheme", "N matings"),
        dtype=str,
    )
    scheme_table = _convert_to_html_table(scheme_table)

    surplus_genotype_table = _convert_to_html_table(
        surplus.create_genotype_df(
            decimal_places=decimal_places, round_up_total_surplus=True
        )
    )

    return context | {
        "scheme_table": scheme_table,
        "total_n": round(surplus.total_n, decimal_places),
        "total_surplus": math.ceil(surplus.total_n_surplus),
        # required_n is always a whole number, so int() to display like
        # 35, rather than 35.0
        "required_n": int(surplus.total_n - surplus.total_n_surplus),
        "surplus_genotype_table": surplus_genotype_table,
    }


def _create_line_stats_context(
    request: HttpRequest, line_stats_form: LineStatisticsForm, decimal_places: int = 2
) -> dict[str, Any]:
    """
    Run line statistics calculations, and create a context dict with required
    values for the results page.

    Parameters
    ----------
    line_stats_form : LineStatisticsForm
        The completed line statistics form
    decimal_places: int
            Number of decimal places to round values to.

    Returns
    -------
    dict[str, Any]
        Context dict for line statistics results
    """
    context = {"form": line_stats_form}
    line_name = line_stats_form.cleaned_data["line"]
    start_date = line_stats_form.cleaned_data["start_date"]
    end_date = line_stats_form.cleaned_data["end_date"]

    colony_management = get_colony()
    try:
        line_stats = colony_management.get_line_stats(
            line_name=line_name, start_date=start_date, end_date=end_date
        )
    except ProcessingError as e:
        messages.error(request, str(e))
        return context

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

    return context | {
        "stats_total_n": line_stats.total_n_offspring,
        "stats_genotyped_n": line_stats.total_n_genotyped_offspring,
        "stats_sexed_n": line_stats.total_n_sexed_offspring,
        "stats_matings_n": line_stats.total_n_successful_matings,
        "stats_litter_size": round(line_stats.average_litter_size, decimal_places),
        "stats_proportion_male": round(line_stats.proportion_male, decimal_places),
        "stats_genotype_table": n_per_genotype_df,
        "stats_scheme_summary_table": scheme_summary_df,
        "stats_scheme_number_table": scheme_number_df,
        "stats_scheme_proportion_table": scheme_proportion_df,
    }
