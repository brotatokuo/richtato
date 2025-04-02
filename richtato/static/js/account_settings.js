document.addEventListener("DOMContentLoaded", () => {
  const cardsTable = new Table(
    "settings-card-table",
    "/settings/get-cards/",
    document.getElementById("settingsCardEditButton"),
    saveTableEndpoint,
  );
});
