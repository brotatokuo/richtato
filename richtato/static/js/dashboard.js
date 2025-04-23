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

  // const incomeOverviewLineChart = document
  //   .getElementById("income-overview-line-chart")
  //   .getContext("2d");
  // plotOverviewLineChart(incomeOverviewLineChart, "/income/get-last-30-days/");

  const renderer = new BudgetRenderer(
    "categories-container",
    "/budget/get-budget-rankings/"
  );
  renderer.fetchAndRender({ count: 3 });
});
