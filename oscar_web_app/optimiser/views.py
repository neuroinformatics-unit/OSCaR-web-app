from django.shortcuts import render

from .forms import GenotypeFormSet
from .forms import LineForm


def select_genotypes(request):

    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = LineForm(request.POST)

        context = {"form": form}
        line = request.POST.get("line")
        if line:
            # Fetches mutations from API
            mutations = ["Mut-A", "Mut-B", "Mut-C"]
            genotype_formset = GenotypeFormSet(
                form_kwargs={"mutation_names": mutations}
            )
        else:
            genotype_formset = None

    else:
        form = LineForm()
        genotype_formset = None

    context = {"form": form, "genotype_formset": genotype_formset}
    return render(request, "optimiser/select_genotypes.html", context)
