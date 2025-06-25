document.addEventListener("DOMContentLoaded", () => {
  let cardsTable = new RichTable(
    "#settings-card-table",
    "/api/card-accounts/",
    ["Name", "Bank"]
  );
  let accountsTable = new RichTable(
    "#settings-accounts-table",
    "/api/accounts/",
    ["Name", "Type", "Entity"]
  );

  let categoryTable = new RichTable(
    "#settings-categories-table",
    "/api/categories/",
    ["Name", "Type"]
  );

  let BudgetTable = new RichTable(
    "#settings-budget-table",
    "/api/budget/",
    ["Name", "Type"]
  );
});
