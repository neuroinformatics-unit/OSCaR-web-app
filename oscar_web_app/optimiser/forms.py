from django import forms
from django.forms import BaseFormSet
from django.forms import formset_factory
from oscar_colony.breeding_scheme import Genotype
from oscar_colony.colony_management.pyrat.api import get_pyrat_lines


def _fetch_line_choices():
    # Start with an empty default choice
    lines = [("", "--------")]

    for line_df in get_pyrat_lines():
        lines.extend([(row.id, row.name) for row in line_df.itertuples(index=False)])

    return lines


class LineForm(forms.Form):
    line = forms.ChoiceField(
        label="Line",
        choices=_fetch_line_choices,
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


# A formset where the can_delete checkbox is hidden by default
class HiddenDeleteFormSet(BaseFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        if "DELETE" in form.fields:
            form.fields["DELETE"].widget = forms.HiddenInput()


GenotypeFormSet = formset_factory(
    GenotypeForm, formset=HiddenDeleteFormSet, extra=1, can_delete=True
)
