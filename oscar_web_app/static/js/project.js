const addButton = document.querySelector("#add-genotype");
const genotypeForms = document.querySelector("#genotype-forms");
const totalForms = document.querySelector("#id_form-TOTAL_FORMS");
const emptyTemplate = document.querySelector("#empty-form")


if (addButton) {
    addButton.addEventListener("click", addGenotype);
}
if (genotypeForms) {
    genotypeForms.addEventListener("click", removeGenotype);
}

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

    genotypeForms.append(emptyForm);
    totalForms.value = nForms + 1;
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
