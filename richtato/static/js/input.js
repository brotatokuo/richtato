const currencyInputs = document.getElementsByClassName("currency-input");
Array.from(currencyInputs).forEach((currencyInput) => {
  currencyInput.addEventListener("input", () => {
    const value = currencyInput.value;
    const validCharacters = /^[0-9+\-*/().=]*$/;
    if (!validCharacters.test(value)) {
      currencyInput.value = value.replace(/[^0-9+\-*/().=]/g, "");
    }
  });

  currencyInput.addEventListener("blur", () => {
    let balance = currencyInput.value;

    if (balance) {
      let newBalance = computeBalance(balance);

      if (newBalance) {
        currencyInput.value = newBalance;
        console.log("New balance:", newBalance);
      }
    }
  });
});

const descriptionInput = document.getElementById("expense-description");

document.addEventListener("DOMContentLoaded", () => {
  const expenseGraph = new SimpleLineGraph(
    expenseLineChart,
    "/api/expenses/graph"
  );
  expenseGraph.init();

  const incomeGraph = new SimpleLineGraph(
    incomeLineChart,
    "/api/incomes/graph"
  );
  incomeGraph.init();

  const expenseTable = new RichTable(
    "#expenseTable",
    "/api/expenses/",
    ["date", "description", "amount", "account", "category"],
    5
  );

  const incomeTable = new RichTable(
    "#incomeTable",
    "/api/incomes/",
    ["date", "description", "amount", "account"],
    5
  );
});

class SimpleLineGraph {
  constructor(ctx, endpointUrl, options = {}) {
    this.ctx = ctx;
    this.endpointUrl = endpointUrl;
    this.chart = null;
    this.options = options;
  }

  async init() {
    try {
      const chartData = await this.fetchData();
      this.renderChart(chartData);
    } catch (error) {
      console.error("Error initializing chart:", error);
    }
  }

  async fetchData() {
    const response = await fetch(this.endpointUrl);
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    return await response.json();
  }

  renderChart(chartData) {
    const dataset = chartData.datasets[0];

    this.chart = new Chart(this.ctx, {
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
            fill: dataset.fill !== undefined ? dataset.fill : true,
            tension: dataset.tension !== undefined ? dataset.tension : 0.1,
          },
        ],
      },
      options: this.getChartOptions(),
    });
  }

  getChartOptions() {
    const textColor =
      getComputedStyle(document.documentElement)
        .getPropertyValue("--text-color")
        .trim() || "#fff";

    return {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          beginAtZero: true,
          ticks: {
            color: textColor,
          },
          grid: {
            color: "rgba(255, 255, 255, 0.2)",
          },
        },
        y: {
          beginAtZero: true,
          ticks: {
            color: textColor,
            callback: function (value) {
              const roundedValue = Math.round(value);
              return new Intl.NumberFormat("en-US", {
                style: "currency",
                currency: "USD",
                maximumFractionDigits: 0,
              }).format(roundedValue);
            },
          },
          grid: {
            color: "rgba(255, 255, 255, 0.2)",
          },
        },
      },
      plugins: {
        legend: {
          display: this.options.showLegend || false,
        },
      },
    };
  }
}
