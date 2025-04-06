// document.addEventListener("DOMContentLoaded", () => {
//     const tableDropdown = document.getElementById("tableOption");
//     let tableOption = tableDropdown.value;
//     let pageNumber = 1;

//     let fullTable = new Table(
//         "fullTable",
//         `/get-table-data/?option=${encodeURIComponent(tableOption)}&page=${pageNumber}`,
//         document.getElementById("editTable"),
//         "",
//         null
//     );

//     setupPageNavigation();

//     tableDropdown.addEventListener("change", () => {
//         tableOption = tableDropdown.value; // Get the updated option value
//         pageNumber = 1; // Reset to first page on option change
//         fullTable.tableUrl = `/get-table-data/?option=${encodeURIComponent(tableOption)}&page=${pageNumber}`;
//         fullTable.loadTableData();
//     });

//     function setupPageNavigation() {
//         const prevPage = document.getElementById("prevPage");
//         const nextPage = document.getElementById("nextPage");

//         prevPage.addEventListener("click", () => {
//             if (pageNumber > 1) {
//                 pageNumber--;
//                 updateTablePage();
//             }
//         });

//         nextPage.addEventListener("click", () => {
//             pageNumber++;
//             updateTablePage();
//         });
//     }

//     function updateTablePage() {
//         fullTable.tableUrl = `/get-table-data/?option=${encodeURIComponent(tableOption)}&page=${pageNumber}`;
//         fullTable.loadTableData();
//         console.log(`Updated to page number: ${pageNumber}`);
//     }
// });

document.addEventListener('DOMContentLoaded', () => {
    const tableConfig = {
        paging: true,
        searching: true,
        info: false,
        lengthChange: false,
    };

    const tableDropdown = document.getElementById("tableOption");
    let tableOption = tableDropdown.value;
    var tableUrl = `/get-table-data/?option=${encodeURIComponent(tableOption)}`;
    console.log(tableUrl);
    let fullTable = new NewTable('#fullTable', tableUrl, tableConfig);

    tableDropdown.addEventListener("change", () => {
        tableOption = tableDropdown.value; // Get the updated option value
        console.log("Selected option:", tableOption);
        var tableUrl = `/get-table-data/?option=${encodeURIComponent(tableOption)}`;
        fullTable = new NewTable('#fullTable', tableUrl, tableConfig);
    });

});