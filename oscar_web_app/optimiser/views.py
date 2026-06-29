from django.shortcuts import render


def select_genotypes(request):
    context = {"test": "test"}
    return render(request, "optimiser/select_genotypes.html", context)
