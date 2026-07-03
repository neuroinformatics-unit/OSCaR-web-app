const addButton = document.getElementById("add-genotype");
const genotypeForms = document.getElementById("genotype-forms");
const totalForms = document.getElementById("id_form-TOTAL_FORMS");
const emptyTemplate = document.getElementById("empty-form")

addButton.addEventListener("click", addGenotype);

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
