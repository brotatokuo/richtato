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