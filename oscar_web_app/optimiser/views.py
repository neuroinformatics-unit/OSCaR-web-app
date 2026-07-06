from django.shortcuts import render
from oscar_colony.colony_management.pyrat.api import get_pyrat_line_mutations

from .forms import GenotypeFormSet
from .forms import LineForm


def select_genotypes(request):

    context = {}
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        line_form = LineForm(request.POST)

        if line_form.is_valid():
            line_id = line_form.cleaned_data["line"]

            if line_id:
                # Fetches mutations from API
                mutations = get_pyrat_line_mutations(line_id)
                genotype_formset = GenotypeFormSet(
                    form_kwargs={"mutation_names": mutations}
                )
                context["formset"] = genotype_formset
    else:
        line_form = LineForm()

    context["line_form"] = line_form
    return render(request, "optimiser/select_genotypes.html", context)
