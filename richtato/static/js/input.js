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
descriptionInput.addEventListener("blur", () => {
  const description = descriptionInput.value;
  guessCategoryFromDescription(description);
});

document.addEventListener("DOMContentLoaded", () => {
  const expenseLineChart = document
    .getElementById("expenseLineChart")
    .getContext("2d");
  plotExpenseLineChart(expenseLineChart, "/expense/get_line_graph_data/");
  const incomeLineChart = document
    .getElementById("incomeLineChart")
    .getContext("2d");
  plotExpenseLineChart(incomeLineChart, "/income/get_line_graph_data/");

  const expenseTable = new Table(
    "expenseTable",
    "/expense/get_recent_entries/",
    document.getElementById("editExpenseTable"),
    "/expense/update/",
    null
  );

  const incomeTable = new Table(
    "incomeTable",
    "/income/get_recent_entries/",
    document.getElementById("editIncomeTable"),
    "/income/update/",
    null
  );
});

async function plotExpenseLineChart(ctx, endpointUrl) {
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
        scales: {
          y: {
            beginAtZero: true,
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
