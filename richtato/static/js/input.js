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
  const expenseLineChart = document
    .getElementById("expenseLineChart")
    .getContext("2d");
  plotLineChart(expenseLineChart, "/expense/get_line_graph_data/");
  const incomeLineChart = document
    .getElementById("incomeLineChart")
    .getContext("2d");
  plotLineChart(incomeLineChart, "/income/get_line_graph_data/");

  const visibleColumns = ["date", "description", "amount"];

  const expenseTableUrl = "/api/expenses/?limit=5";
  let expenseTable = new RichTable("#expenseTable", expenseTableUrl, ["date", "description", "amount", "account", "category"]);

  const incomeTableUrl = "/get-table-data/?option=income&limit=5";
  // let incomeTable = new RichTable(
  //   '#incomeTable', incomeTableUrl, {}, visibleColumns
  // )
});

async function plotLineChart(ctx, endpointUrl) {
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
        labels: chartData.labels, // Use the labels from the response
        datasets: [
          {
            label: dataset.label,
            data: dataset.data, // Use the data from the response
            backgroundColor: dataset.backgroundColor, // Semi-transparent background color
            borderColor: dataset.borderColor, // Border color for the line
            borderWidth: dataset.borderWidth,
            fill: dataset.fill !== undefined ? dataset.fill : true,
            tension: dataset.tension !== undefined ? dataset.tension : 0.1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            beginAtZero: true,
            ticks: {
              color:
                getComputedStyle(document.documentElement)
                  .getPropertyValue("--text-color")
                  .trim() || "#fff",
            },
            grid: {
              color: "rgba(255, 255, 255, 0.2)", // Light grid lines for dark mode
            },
          },
          y: {
            beginAtZero: true,
            ticks: {
              color:
                getComputedStyle(document.documentElement)
                  .getPropertyValue("--text-color")
                  .trim() || "#fff",
              callback: function (value, index, values) {
                const roundedValue = Math.round(value);
                return new Intl.NumberFormat("en-US", {
                  style: "currency",
                  currency: "USD",
                  maximumFractionDigits: 0, // Ensure no decimal places are shown
                }).format(roundedValue);
              },
            },
            grid: {
              color: "rgba(255, 255, 255, 0.2)", // Light grid lines for dark mode
            },
          },
        },
        plugins: {
          legend: {
            display: false, // Set to true if you want to display the legend
          },
        },
      },
    });
  } catch (error) {
    console.error("Error fetching or plotting data:", error);
  }
}

function guessCategoryFromDescription(description) {
  console.log("Guessing category for:", description);
  // Encode the description before sending it
  const url = `/expense/guess-category/?description=${encodeURIComponent(
    description
  )}`;

  fetch(url)
    .then((response) => response.json())
    .then((data) => {
      if (data.category) {
        console.log("Category found:", data.category);
        const categoryInput = document.getElementById("category");
        categoryInput.value = data.category;
      } else {
        console.log("No category found");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
    });
}

function computeBalance(balance) {
  if (balance.startsWith("=")) {
    try {
      balance = eval(balance.slice(1));
      console.log("Evaluated formula:", balance);
    } catch (error) {
      console.error("Invalid formula:", error);
      return;
    }
  } else {
    balance = eval(balance);
  }
  balance = parseFloat(balance).toFixed(2);
  return balance;
}
