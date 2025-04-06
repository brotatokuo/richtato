document.addEventListener("DOMContentLoaded", () => {
  const tableConfig = {
    paging: false,
    searching: false,
    info: false,
    lengthChange: false,
  };
  let cardsTable = new NewTable("#settings-card-table", "/settings/get-cards/", tableConfig);
});
