document.addEventListener("DOMContentLoaded", () => {
  const expenseOverviewLineChart = document
    .getElementById("expense-overview-line-chart")
    .getContext("2d");
  plotOverviewLineChart(expenseOverviewLineChart, "/expense/get-last-30-days/");

  const incomeOverviewLineChart = document
    .getElementById("income-overview-line-chart")
    .getContext("2d");
  plotOverviewLineChart(incomeOverviewLineChart, "/income/get-last-30-days/");

  const renderer = new BudgetRenderer('categories-container', '/budget/get-budget-rankings/');
  renderer.fetchAndRender();
});

async function plotOverviewLineChart(ctx, endpointUrl) {
  try {
    const response = await fetch(endpointUrl);
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    const chartData = await response.json();
    const dataset = chartData.datasets[0];
    const myLineChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: chartData.labels,
        datasets: [
          {
            label: dataset.label,
            data: dataset.data,
            backgroundColor: dataset.backgroundColor,
            borderColor: dataset.borderColor,
            borderWidth: dataset.borderWidth,
            fill: false,
            tension: 0.3,
            pointRadius: 0,
            pointHoverRadius: 0,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            display: false,
          },
          y: {
            display: false,
          },
        },
        plugins: {
          legend: {
            display: false,
          },
        },
        animation: {
          x: {
            from: 0,
          },
          y: {
            from: 50,
          },
        },
      },
    });
  } catch (error) {
    console.error("Error fetching or plotting data:", error);
  }
}
