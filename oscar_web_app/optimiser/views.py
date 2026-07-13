from django.shortcuts import redirect
from django.shortcuts import render
from oscar_colony.colony_management.pyrat.api import get_pyrat_line_mutations

from .forms import GenotypeFormSet
from .forms import LineForm


def select_line(request):
    if request.method == "POST":
        form = LineForm()
        if form.is_valid():
            line_id = form.cleaned_data["line"]
            return redirect("select_genotypes", line_id=line_id)

    else:
        form = LineForm()

    return render(request, "optimiser/select_line.html", {"form": form})


def select_genotypes(request, line_id):

    if request.method != "POST":
        line_form = LineForm()
        return render(
            request, "optimiser/select_genotypes.html", {"line_form": line_form}
        )

    # Handle POST requests
    line_form = LineForm(request.POST)
    line_id = None
    if line_form.is_valid():
        line_id = line_form.cleaned_data["line"]

    # The form was submitted via the optimise schemes button
    if (request.POST.get("action") == "optimise") and (line_id is not None):
        mutations = get_pyrat_line_mutations(line_id)
        genotype_formset = GenotypeFormSet(
            request.POST, request.FILES, form_kwargs={"mutation_names": mutations}
        )

        if genotype_formset.is_valid():
            return render(
                request,
                "optimiser/calculate_genotypes.html",
                {"formset": genotype_formset},
            )

    # The form was submitted by changing the dropdown
    elif line_id is not None:
        # Fetches mutations from API
        mutations = get_pyrat_line_mutations(line_id)
        genotype_formset = GenotypeFormSet(form_kwargs={"mutation_names": mutations})

    return render(
        request,
        "optimiser/select_genotypes.html",
        {"line_form": line_form, "formset": genotype_formset},
    )
