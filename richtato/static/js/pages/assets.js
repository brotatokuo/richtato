document.addEventListener("DOMContentLoaded", () => {
  new RichTable(
    "#detailAssetsTable",
    "/api/accounts/details/",
    ["Date", "Amount", "Account"],
    10
  );
});
