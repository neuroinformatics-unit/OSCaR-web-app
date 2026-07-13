from django.shortcuts import redirect
from django.shortcuts import render

from .colony_management import ColonyManagement
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

    mutations = ColonyManagement().get_line_mutations(line_id)
    error_messages = {"too_few_forms": "Please provide at least one genotype"}

    if request.method == "POST":
        formset = GenotypeFormSet(
            request.POST,
            form_kwargs={"mutation_names": mutations},
            error_messages=error_messages,
        )
        if formset.is_valid():
            return redirect("optimiser:calculate_schemes", line_id=line_id)

    else:
        formset = GenotypeFormSet(
            form_kwargs={"mutation_names": mutations}, error_messages=error_messages
        )

    return render(request, "optimiser/select_genotypes.html", {"formset": formset})


def calculate_schemes(request, line_id):
    return render(request, "optimiser/calculate_schemes.html", {"line_id": line_id})
