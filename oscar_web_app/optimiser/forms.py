from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column
from crispy_forms.layout import Div
from crispy_forms.layout import Layout
from crispy_forms.layout import Row
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
        label="Line name",
        choices=_fetch_line_choices,
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(Div("line", css_class="border-bottom mb-3"))


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

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            Row(
                *(Column(name) for name in mutation_names),
                Column("count"),
                Column(
                    StrictButton(
                        "X", type="button", css_class="btn btn-primary remove-genotype"
                    ),
                    css_class="col-md-1 mb-3 d-flex align-items-end",
                ),
                css_class="bg-light rounded-4 p-1 my-2",
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
