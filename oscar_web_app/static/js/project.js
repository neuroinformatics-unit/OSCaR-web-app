const addButton = document.getElementById("add-genotype");
const removeButtons = document.querySelectorAll(".remove-genotype");
const genotypeForms = document.getElementById("genotype-forms");
const totalForms = document.getElementById("id_form-TOTAL_FORMS");
const emptyTemplate = document.getElementById("empty-form")

addButton.addEventListener("click", addGenotype);
genotypeForms.addEventListener('click', removeGenotype);

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


function removeGenotype(e) {

    // Retrieve the clicked button
    const button = e.target.closest('.remove-genotype');
    if (!button) return;

    const row = button.closest(".form-row")
    const deleteCheckbox = row.querySelector("input[name$='-DELETE']")
    if (deleteCheckbox) {
        deleteCheckbox.checked = true;
    }
    row.style.display = "none";

    // const nForms = Number(totalForms.value);

    // row.remove()
    // totalForms.value = nForms - 1;

    // // Renumber all remaining forms, so they are consecutive
    // const rows = genotypeForms.querySelector(".form-row")
    // rows.forEach((row, index) => {
    //     row.querySelectorAll("*").forEach(el => {
    //     for (const attr of el.attributes) {
    //         attr.value = attr.value.replace(/form-\d+-/, `form-${index}-`);
    //         }
    //     });
    // });
}
