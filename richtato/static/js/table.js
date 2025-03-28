document.addEventListener("DOMContentLoaded", () => {
    const tableOption = document.getElementById("tableOption").value;
    let pageNumber = 1;

    setupPageNavigation();


    const fullTable = new Table(
        "fullTable",
        `/get-table-data/?option=${encodeURIComponent(tableOption)}&page=${pageNumber}`,
        document.getElementById("editTable"),
        "",
        null
    );

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
        // fullTable.update(pageNumber);
        console.log(pageNumber);
        fullTable.tableUrl = `/get-table-data/?option=${encodeURIComponent(tableOption)}&page=${pageNumber}`;
        fullTable.loadTableData()
    }
});
