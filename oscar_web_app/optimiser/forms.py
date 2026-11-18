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
from django.forms.formsets import DELETION_FIELD_NAME

from .colony_management import get_colony


def _fetch_line_choices():
    """Fetch available line choices to populate dropdown menu"""

    # Start with an empty default choice
    lines = [("", "--------")]

    for line_df in get_colony().get_lines():
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

    count_any_sex = forms.IntegerField(label="# total", min_value=1, initial=1)
    count_males = forms.IntegerField(label="# males", min_value=1, initial=1)
    count_females = forms.IntegerField(label="# females", min_value=1, initial=1)

    count_type = forms.ChoiceField(
        choices=[("any_sex", "any sex"), ("specific_sex", "# males/females")],
        initial="any_sex",
        label="Required sex",
    )

    def __init__(self, *args, mutation_names: list[str] | None = None, **kwargs):
        """
        Create a ChoiceField for each provided mutation_name and setup form
        layout.
        """
        super().__init__(*args, **kwargs)
        self.mutation_names = mutation_names if mutation_names is not None else []

        # mutations is a kwarg
        for mutation_name in self.mutation_names:
            self.fields[mutation_name] = forms.ChoiceField(
                label=mutation_name,
                choices=(
                    ("WT", "WT"),
                    ("HET", "HET"),
                    ("HOM", "HOM"),
                ),
            )

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            Row(
                *(Column(name) for name in self.mutation_names),
                Column("count_type", css_class="col-xl-2 col-md-3"),
                Column("count_any_sex", css_class="col-xl-2 col-md-4 count-any-sex"),
                Column("count_males", css_class="col-xl-1 col-md-2 count-specific-sex"),
                Column(
                    "count_females", css_class="col-xl-1 col-md-2 count-specific-sex"
                ),
                Column(
                    StrictButton(
                        "X",
                        type="button",
                        css_class="btn btn-secondary remove-genotype",
                    ),
                    css_class="col-md-1 mb-3 d-flex align-items-end",
                ),
                Column("DELETE", css_class="d-none"),  # Hide django's deletion checkbox
                css_class="genotype-form bg-light rounded-4 p-1 my-2",
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
        mutation_fields = self.forms[0].mutation_names

        for form in self.forms:
            # ignore forms marked for deletion
            if self.can_delete and form.cleaned_data.get(DELETION_FIELD_NAME, False):
                continue

            genotype = tuple(
                form.cleaned_data.get(mutation_field)
                for mutation_field in mutation_fields
            )

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
