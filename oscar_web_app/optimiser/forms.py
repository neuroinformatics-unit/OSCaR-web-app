from django import forms
from django.forms import formset_factory
from oscar_colony.breeding_scheme import Genotype


class LineForm(forms.Form):
    line = forms.ChoiceField(
        label="Line",
        choices=(("a", "option-a"), ("b", "option-b"), ("c", "option-c")),
        required=True,
    )


class GenotypeForm(forms.Form):
    count = forms.IntegerField()

    def __init__(self, mutation_names=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # mutations is a kwarg
        if mutation_names:
            for mutation_name in mutation_names:
                self.fields[mutation_name] = forms.ChoiceField(
                    choices=(
                        (Genotype.WT, "WT"),
                        (Genotype.HET, "HET"),
                        (Genotype.HOM, "HOM"),
                    )
                )


GenotypeFormSet = formset_factory(GenotypeForm, extra=2, can_delete=True)
