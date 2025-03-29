document.addEventListener("DOMContentLoaded", () => {
    const tableDropdown = document.getElementById("tableOption");
    let tableOption = tableDropdown.value;
    let pageNumber = 1;

    let fullTable = new Table(
        "fullTable",
        `/get-table-data/?option=${encodeURIComponent(tableOption)}&page=${pageNumber}`,
        document.getElementById("editTable"),
        "",
        null
    );

    setupPageNavigation();

    tableDropdown.addEventListener("change", () => {
        tableOption = tableDropdown.value; // Get the updated option value
        pageNumber = 1; // Reset to first page on option change
        fullTable.tableUrl = `/get-table-data/?option=${encodeURIComponent(tableOption)}&page=${pageNumber}`;
        fullTable.loadTableData();
    });

    function setupPageNavigation() {
        const prevPage = document.getElementById("prevPage");
        const nextPage = document.getElementById("nextPage");

        prevPage.addEventListener("click", () => {
            if (pageNumber > 1) {
                pageNumber--;
                updateTablePage();
            }
        });

        nextPage.addEventListener("click", () => {
            pageNumber++;
            updateTablePage();
        });
    }

    function updateTablePage() {
        fullTable.tableUrl = `/get-table-data/?option=${encodeURIComponent(tableOption)}&page=${pageNumber}`;
        fullTable.loadTableData();
        console.log(`Updated to page number: ${pageNumber}`);
    }
});
