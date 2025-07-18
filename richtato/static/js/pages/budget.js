document.addEventListener("DOMContentLoaded", () => {
  const yearSelect = document.getElementById("year");
  const monthSelect = document.getElementById("month");
  const year = yearSelect.value;
  const month = monthSelect.value;

  const renderer = new BudgetRenderer(
    "categories-container",
    "/get-budget-rankings/"
  );
  renderer.fetchAndRender({ year, month });

  yearSelect.addEventListener("change", () => {
    renderer.fetchAndRender({
      year: yearSelect.value,
      month: monthSelect.value,
    });
  });
  monthSelect.addEventListener("change", () => {
    renderer.fetchAndRender({
      year: yearSelect.value,
      month: monthSelect.value,
    });
  });
});
