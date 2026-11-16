const addButton = document.querySelector("#add-genotype");
const genotypeFormsContainer = document.querySelector("#genotype-forms");
const genotypeForms = document.querySelectorAll(".genotype-form");
const totalForms = document.querySelector("#id_form-TOTAL_FORMS");
const emptyTemplate = document.querySelector("#empty-form")


if (addButton) {
    addButton.addEventListener("click", addGenotype);
}
if (genotypeFormsContainer) {
    genotypeFormsContainer.addEventListener("click", removeGenotype);
}
genotypeForms.forEach(setupCountTypeToggle);

// Add a new, empty genotype form to the genotypeForms container
function addGenotype() {
    const nForms = Number(totalForms.value);
    const emptyForm = emptyTemplate.content.cloneNode(true);

    // Replace __prefix__ with the current form number
    emptyForm.querySelectorAll("*").forEach(el => {
    for (const attr of el.attributes) {
        attr.value = attr.value.replace(/__prefix__/g, nForms);
        }
    });
    const genotypeForm = emptyForm.querySelector(".genotype-form");

    genotypeFormsContainer.append(emptyForm);
    totalForms.value = nForms + 1;
    setupCountTypeToggle(genotypeForm);
}

// Mark a genotype row for deletion, and hide it from the user
function removeGenotype(e) {

    // Retrieve the clicked button
    const button = e.target.closest('.remove-genotype');
    if (!button) return;

    const row = button.closest(".row")
    const deleteCheckbox = row.querySelector("input[name$='-DELETE']")
    if (deleteCheckbox) {
        deleteCheckbox.checked = true;
        row.classList.add("deleted");
    }
}

// Setup toggling of total count vs male / female count
function setupCountTypeToggle(form) {
  const typeDropdown = form.querySelector("select[name$='-count_type']");
  const totalCount = form.querySelectorAll(".count-any-sex");
  const maleFemaleCount = form.querySelectorAll(".count-specific-sex");

  function sync() {
    const countType = typeDropdown.value;
    totalCount.forEach(el => el.classList.toggle("d-none", countType !== "any_sex"));
    maleFemaleCount.forEach(el => el.classList.toggle("d-none", countType == "any_sex"));
  }

  typeDropdown.addEventListener("change", sync);
  sync();
}
