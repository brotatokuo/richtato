document.addEventListener("DOMContentLoaded", function () {
  // Card Accounts Table
  const cardAccountsTable = new TableManager(
    "settings-card-table",
    "get-cards/",
    document.getElementById("settingsCardEditButton"),
    "update-cards/"
  );

  cardAccountsTable.loadTableData();
  document.getElementById("settingsCardEditButton").onclick = function () {
    cardAccountsTable.toggleEditMode();
  };

  // Accounts Table
  const accountsTable = new TableManager(
    "settings-accounts-table",
    "get-accounts/",
    document.getElementById("settingsAccountEditButton"),
    "update-accounts/"
  );

  accountsTable.loadTableData();
  document.getElementById("settingsAccountEditButton").onclick = function () {
    accountsTable.toggleEditMode();
  };

  // Categories Table
  const categoriesTable = new TableManager(
    "settings-categories-table",
    "get-categories/",
    document.getElementById("settingsCategoryEditButton"),
    "update-categories/"
  );

  categoriesTable.loadTableData();
  document.getElementById("settingsCategoryEditButton").onclick = function () {
    categoriesTable.toggleEditMode();
  };
});
