document.addEventListener("DOMContentLoaded", () => {
  const tableConfig = {
    paging: true,
    searching: true,
    info: false,
    lengthChange: false,
  };

  const tableDropdown = document.getElementById("tableOption");

  const loadTable = () => {
    if (tableDropdown.value == "expense") {
      new RichTable(
        "#fullTable",
        "/api/expenses/",
        ["date", "description", "amount", "account", "category"],
        null,
        tableConfig
      );
    } else if (tableDropdown.value == "income") {
      new RichTable(
        "#fullTable",
        "/api/incomes/",
        ["date", "description", "amount", "account"],
        null,
        tableConfig
      );
    } else {
      console.error("Invalid table option selected.");
    }
  };

  loadTable();
  tableDropdown.addEventListener("change", loadTable);
});
