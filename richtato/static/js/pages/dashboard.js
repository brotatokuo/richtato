document.addEventListener("DOMContentLoaded", () => {
  const expenseGraph = new BackgroundTimeseriesGraph(
    "expense-overview-line-chart",
    "/api/expenses/graph/?range=30d"
  );
  expenseGraph.render();

  const incomeGraph = new BackgroundTimeseriesGraph(
    "income-overview-line-chart",
    "/api/incomes/graph/?range=30d"
  );
  incomeGraph.render();

  const renderer = new BudgetRenderer(
    "categories-container",
    "/get-budget-rankings/"
  );
  renderer.fetchAndRender({ count: 3 });
});
