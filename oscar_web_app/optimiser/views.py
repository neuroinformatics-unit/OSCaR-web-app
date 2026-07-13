from django.shortcuts import redirect
from django.shortcuts import render
from oscar_colony.colony_management.pyrat.api import get_pyrat_line_mutations

from .forms import GenotypeFormSet
from .forms import LineForm


def select_line(request):
    if request.method == "POST":
        form = LineForm(request.POST)
        if form.is_valid():
            line_id = form.cleaned_data["line"]
            return redirect("optimiser:select_genotypes", line_id=line_id)

    else:
        form = LineForm()

    return render(request, "optimiser/select_line.html", {"form": form})


def select_genotypes(request, line_id):

    mutations = get_pyrat_line_mutations(line_id)

    if request.method == "POST":
        formset = GenotypeFormSet(
            request.POST, form_kwargs={"mutation_names": mutations}
        )
        if formset.is_valid():
            return redirect("optimiser:calculate_schemes", line_id=line_id)

    else:
        formset = GenotypeFormSet(form_kwargs={"mutation_names": mutations})

    return render(request, "optimiser/select_genotypes.html", {"formset": formset})


def calculate_schemes(request, line_id):
    return render(request, "optimiser/calculate_schemes.html", {"line_id": line_id})
