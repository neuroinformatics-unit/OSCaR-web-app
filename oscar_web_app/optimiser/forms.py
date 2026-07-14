from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML
from crispy_forms.layout import Column
from crispy_forms.layout import Div
from crispy_forms.layout import Layout
from crispy_forms.layout import Row
from crispy_forms.layout import Submit
from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseFormSet
from django.forms import formset_factory
from oscar_colony.breeding_scheme import Genotype

from .colony_management import ColonyManagement


def _fetch_line_choices():
    """Fetch available line choices to populate dropdown menu"""

    # Start with an empty default choice
    lines = [("", "--------")]

    for line_df in ColonyManagement().get_lines():
        if not line_df.empty:
            lines.extend(
                [(row.id, row.name) for row in line_df.itertuples(index=False)]
            )

    return lines


class LineForm(forms.Form):
    """Form to select a specific line"""

    line = forms.ChoiceField(
        label="Line name",
        choices=_fetch_line_choices,
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(Column("line", css_class="col-md-7 mx-auto")),
            Div(
                HTML(
                    """
                    <a href="{% url 'home' %}" class="btn btn-secondary px-5">Back</a>
                    """
                ),
                Submit("submit", "Next", css_class="btn btn-primary px-5"),
                css_class="d-flex justify-content-center gap-2",
            ),
        )


class GenotypeForm(forms.Form):
    """Form to specify required number of animals of one genotype"""

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
                Column("count", css_class="col-md-2"),
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


class BaseGenotypeFormset(BaseFormSet):
    """Base class for the formset - allows custom formset validation"""

    def clean(self):
        """On form submission, check that all provided genotypes are unique"""

        # Check individual genotype forms are valid
        if any(self.errors):
            return

        genotypes = set()
        mutation_fields = [
            field_name
            for field_name in self.forms[0].cleaned_data
            if field_name not in ["count", "DELETE"]
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
