from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column
from crispy_forms.layout import Layout
from crispy_forms.layout import Row
from crispy_forms.layout import Submit
from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseFormSet
from django.forms import formset_factory
from django.forms.formsets import DELETION_FIELD_NAME
from django.urls import reverse
from django.utils import timezone

from .colony_management import get_colony


def _fetch_line_choices(*, return_ids: bool = True) -> list[tuple[int | str, str]]:
    """Fetch available line choices to populate dropdown menu

    Parameters
    ----------
    return_ids : bool, optional
        When true, return the line ids as the values. Otherwise, return
        line names.

    Returns
    -------
    list[tuple[int | str, str]
        A list of (returned_value, displayed_value) pairs
    """

    # Start with an empty default choice
    lines = [("", "--------")]

    for line_df in get_colony().get_lines():
        if not line_df.empty:
            lines.extend(
                [
                    (row.id, row.name) if return_ids else (row.name, row.name)
                    for row in line_df.itertuples(index=False)
                ]
            )

    return lines


class LineForm(forms.Form):
    """Form to select a specific line"""

    line = forms.ChoiceField(
        label="Line name",
        choices=_fetch_line_choices(return_ids=True),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["line"].widget.attrs.update(
            {
                "hx-post": reverse("optimiser:select_line"),
                "hx-target": "#genotype-form-container",
                "hx-indicator": "#genotypes-spinner",
            }
        )
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Column("line", css_class="mx-auto"),
        )


class LineStatisticsForm(forms.Form):
    """Form to select line and date range for calculating historical statistics."""

    line = forms.ChoiceField(
        label="Line name",
        choices=_fetch_line_choices(return_ids=False),
        required=True,
    )

    start_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        required=False,
        label="start date (optional)",
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        required=False,
        label="end date (optional)",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        date_fields = ["start_date", "end_date"]
        today = timezone.localdate()
        for field in date_fields:
            self.fields[field].widget.attrs["max"] = today

        self.helper = FormHelper()
        self.helper.attrs = {
            "hx-post": reverse("optimiser:line_stats"),
            "hx-target": "#line-stats-container",
            "hx-indicator": "#line-stats-spinner",
        }
        self.helper.layout = Layout(
            Row(
                Column("line", css_class="col-md-4"),
                Column("start_date", css_class="col-auto"),
                Column("end_date", css_class="col-auto"),
                Column(
                    Submit("submit", "Calculate", css_class="btn btn-primary mb-3"),
                    css_class="col-auto",
                ),
                css_class="justify-content-center align-items-end mt-5",
            )
        )


class GenotypeForm(forms.Form):
    """Form to specify required number of animals of one genotype"""

    count_any_sex = forms.IntegerField(label="# total", min_value=1, initial=1)
    count_males = forms.IntegerField(label="# males", min_value=0, initial=1)
    count_females = forms.IntegerField(label="# females", min_value=0, initial=1)

    count_type = forms.ChoiceField(
        choices=[("any_sex", "any sex"), ("specific_sex", "# males/females")],
        initial="any_sex",
        label="Required sex",
    )

    def clean(self):
        """Error if count_males AND count_females are 0 for this form."""

        cleaned_data = super().clean()
        if (cleaned_data is None) or (cleaned_data.get("count_type") != "specific_sex"):
            return

        n_males = cleaned_data.get("count_males", 0)
        n_females = cleaned_data.get("count_females", 0)

        if (n_males == 0) and (n_females == 0):
            # Highlight male / female fields
            self.add_error("count_males", "")
            self.add_error("count_females", "")

            # Show error message on top of form
            msg = "Must request at least one animal per row"
            raise ValidationError(msg)

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
