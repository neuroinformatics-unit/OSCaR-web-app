from typing import Any

import pandas as pd
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from oscar_colony.breeding_scheme import Genotype

from .colony_management import get_colony_management
from .forms import GenotypeFormSet
from .forms import LineForm


def select_line(request) -> HttpResponse:
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


def select_genotypes(request, line_id) -> HttpResponse:

    # Fetch mutation names to create custom fields in the Genotype forms
    mutations = get_colony_management().get_line_mutations(line_id)
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
            # run calculation
            line_name = request.session.get(str(line_id))
            if line_name is None:
                # make request
                pass

            stats_context = create_line_stats_context(line_name)
            scheme_context = create_schemes_context(
                formset, stats_context["line_stats"]
            )

            context = stats_context | scheme_context

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


def _convert_to_html_table(df: pd.DataFrame) -> str:
    return df.to_html(
        classes=["table", "table-striped"], index=False, justify="unset", na_rep=""
    )


def _process_genotype_dfs(df_list: list[pd.DataFrame]) -> str:
    genotype_df = pd.concat(df_list)
    genotype_df = genotype_df.round(decimals=2)
    genotype_df.columns = [
        Genotype.to_string(col_name) if col_name != "Scheme" else col_name
        for col_name in genotype_df.columns
    ]

    # Put scheme as first column, and rest of genotypes in alphabetical order
    sorted_genotype_cols = sorted(
        genotype_df.loc[:, genotype_df.columns != "Scheme"].columns
    )
    genotype_df = genotype_df[["Scheme", *sorted_genotype_cols]]

    return _convert_to_html_table(genotype_df)


def create_line_stats_context(line_name: str) -> dict[str, Any]:

    line_stats = get_colony_management().get_line_stats(line_name)

    n_per_genotype = line_stats.total_n_offspring_per_genotype
    n_per_genotype_df = pd.DataFrame(
        n_per_genotype.items(),
        columns=("Genotype", "N offspring"),
    )
    n_per_genotype_df["Genotype"] = n_per_genotype_df["Genotype"].apply(
        Genotype.to_string
    )
    n_per_genotype_df = _convert_to_html_table(n_per_genotype_df)

    scheme_summary_rows = []
    scheme_number_dfs = []
    scheme_proportion_dfs = []
    for scheme, stats in line_stats.stats_per_breeding_scheme.items():
        scheme_summary_rows.append(
            [
                scheme,
                stats.n_breeding_pairs,
                stats.n_successful_matings,
                round(stats.average_litter_size, 2),
                round(stats.average_n_litters_per_pair, 2),
                stats.total_n_offspring,
                stats.total_n_genotyped_offspring,
            ]
        )

        genotype_dicts = [
            stats.n_offspring_per_genotype,
            stats.proportion_offspring_per_genotype,
        ]
        df_lists = [scheme_number_dfs, scheme_proportion_dfs]

        for genotype_dict, df_list in zip(genotype_dicts, df_lists, strict=True):
            genotype_df = pd.DataFrame([genotype_dict])
            genotype_df["Scheme"] = scheme
            df_list.append(genotype_df)

    scheme_number_df = _process_genotype_dfs(scheme_number_dfs)
    scheme_proportion_df = _process_genotype_dfs(scheme_proportion_dfs)

    scheme_df = pd.DataFrame(
        scheme_summary_rows,
        columns=[
            "Scheme",
            "N breeding pairs",
            "Total successful matings",
            "Average litter size",
            "Average litters per pair",
            "Total offspring",
            "Total genotyped offspring",
        ],
    )
    scheme_df = _convert_to_html_table(scheme_df)

    return {
        "stats_total_n": line_stats.total_n_offspring,
        "stats_genotyped_n": line_stats.total_n_genotyped_offspring,
        "stats_matings_n": line_stats.total_n_successful_matings,
        "stats_litter_size": round(line_stats.average_litter_size, 2),
        "line_stats": line_stats,
        "stats_genotype_table": n_per_genotype_df,
        "stats_scheme_summary_table": scheme_df,
        "stats_scheme_number_table": scheme_number_df,
        "stats_scheme_proportion_table": scheme_proportion_df,
    }


def create_schemes_context(formset, line_stats) -> dict[str, Any]:

    required_genotypes = [form.cleaned_data for form in formset]

    colony_management = get_colony_management()
    scheme_table, surplus = colony_management.optimise_schemes(
        line_stats, required_genotypes
    )
    scheme_table = _convert_to_html_table(scheme_table)

    surplus_genotype_table = surplus.create_genotype_df()
    required_n = (
        surplus_genotype_table["Total N"] - surplus_genotype_table["Total N Surplus"]
    )
    surplus_genotype_table.insert(1, "Required N", required_n)

    surplus_genotype_table = _convert_to_html_table(surplus_genotype_table)

    decimal_places = 2

    return {
        "scheme_table": scheme_table,
        "total_n": round(surplus.total_n, decimal_places),
        "total_surplus": round(surplus.total_n_surplus, decimal_places),
        "required_n": round(surplus.total_n - surplus.total_n_surplus, decimal_places),
        "surplus_genotype_table": surplus_genotype_table,
    }
