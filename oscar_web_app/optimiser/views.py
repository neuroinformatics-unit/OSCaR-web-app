from django.http import Http404
from django.shortcuts import redirect
from django.shortcuts import render

from .colony_management import ColonyManagement
from .forms import GenotypeFormSet
from .forms import LineForm


def select_line(request):
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


def select_genotypes(request, line_id):

    # Fetch mutation names to create custom fields in the Genotype forms
    mutations = ColonyManagement().get_line_mutations(line_id)
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

            line_stats = ColonyManagement().get_line_stats(line_name)
            scheme_context = calculate_schemes_from_formset(formset, line_stats)

            context = {"line_stats": line_stats}
            context = context | scheme_context

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


def calculate_schemes_from_formset(formset, line_stats):

    required_genotypes = [form.cleaned_data for form in formset]

    colony_management = ColonyManagement()
    scheme_table, surplus = colony_management.optimise_schemes(
        line_stats, required_genotypes
    )
    scheme_table = scheme_table.to_html(
        classes=["table", "table-striped"], index=False, justify="unset"
    )

    surplus_genotype_table = surplus.create_genotype_df()
    surplus_genotype_table = surplus_genotype_table.to_html(
        classes=["table", "table-striped"], index=False, justify="unset"
    )

    return {
        "scheme_table": scheme_table,
        "total_n": surplus.total_n,
        "total_surplus": surplus.total_n_surplus,
        "surplus_genotype_table": surplus_genotype_table,
    }
