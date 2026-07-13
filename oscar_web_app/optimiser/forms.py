from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column
from crispy_forms.layout import Div
from crispy_forms.layout import Layout
from crispy_forms.layout import Row
from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseFormSet
from django.forms import formset_factory
from oscar_colony.breeding_scheme import Genotype
from oscar_colony.colony_management.pyrat.api import get_pyrat_lines


def _fetch_line_choices():
    """Fetch list of available lines via oscar_colony"""

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
    count = forms.IntegerField(min_value=1, initial=1)

    def __init__(self, *args, mutation_names=None, **kwargs):
        super().__init__(*args, **kwargs)

        if mutation_names is None:
            mutation_names = []

        # mutations is a kwarg
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
                        "X",
                        type="button",
                        css_class="btn btn-secondary remove-genotype",
                    ),
                    css_class="col-md-1 mb-3 d-flex align-items-end",
                ),
                Column("DELETE", css_class="d-none"),  # Hide django's deletion checkbox
                css_class="bg-light rounded-4 p-1 my-2",
            )
        )


# A formset where the can_delete checkbox is hidden by default
class BaseGenotypeFormset(BaseFormSet):
    def clean(self):
        """Checks all provided genotypes are unique"""

        # Check individual genotype forms are valid
        if any(self.errors):
            return

        genotypes = set()
        mutation_fields = [
            field_name
            for field_name in self.forms[0].cleaned_data
            if field_name != "Count"
        ]

        for form in self.forms:
            # ignore forms marked for deletion
            if self.can_delete and self._should_delete_form(form):
                continue

            genotype = [
                form.cleaned_data.get(mutation_field)
                for mutation_field in mutation_fields
            ]
            genotype = tuple(genotype)

            if genotype in genotypes:
                msg = "All genotypes must be unique"
                raise ValidationError(msg)
            genotypes.add(genotype)


GenotypeFormSet = formset_factory(
    GenotypeForm,
    formset=BaseGenotypeFormset,
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
