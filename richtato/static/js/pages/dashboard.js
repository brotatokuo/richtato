// Dashboard JavaScript - Common Personal Finance Graphs

document.addEventListener("DOMContentLoaded", function () {
  initializeDashboard();
});

function initializeDashboard() {
  // Initialize all charts and components
  initCashFlowChart();
  initIncomeExpenseChart();
  initSavingsChart();
  initTopCategories();
  initExpensePieChart();
  initBudgetProgress();
}

function initCashFlowChart() {
  const ctx = document.getElementById("cashFlowChart");
  if (!ctx) return;

  let cashFlowChart = null;

  // Function to fetch and render cash flow data
  function fetchAndRenderCashFlow(period = "6m") {
    const url = `/dashboard/api/cash-flow/?period=${period}`;

    fetch(url)
      .then((response) => response.json())
      .then((data) => {
        if (data.error) {
          console.error("Error fetching cash flow data:", data.error);
          return;
        }

        // Destroy existing chart if it exists
        if (cashFlowChart) {
          cashFlowChart.destroy();
        }

        cashFlowChart = new Chart(ctx, {
          type: "line",
          data: data,
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: "top",
                labels: {
                  color: getComputedStyle(
                    document.documentElement
                  ).getPropertyValue("--text-color"),
                },
              },
            },
            scales: {
              x: {
                ticks: {
                  color: getComputedStyle(
                    document.documentElement
                  ).getPropertyValue("--text-color"),
                },
                grid: {
                  color: "rgba(255, 255, 255, 0.1)",
                },
              },
              y: {
                beginAtZero: true,
                ticks: {
                  color: getComputedStyle(
                    document.documentElement
                  ).getPropertyValue("--text-color"),
                  callback: function (value) {
                    return "$" + value.toLocaleString();
                  },
                },
                grid: {
                  color: "rgba(255, 255, 255, 0.1)",
                },
              },
            },
          },
        });
      })
      .catch((error) => {
        console.error("Error fetching cash flow data:", error);
      });
  }

  // Initial load with default period
  fetchAndRenderCashFlow("6m");

  // Add event listener for period dropdown
  const periodSelect = document.getElementById("cashflow-period");
  if (periodSelect) {
    periodSelect.addEventListener("change", function () {
      const selectedPeriod = this.value;
      fetchAndRenderCashFlow(selectedPeriod);
    });
  }
}

function initExpensePieChart() {
  const ctx = document.getElementById("expensePieChart");
  if (!ctx) return;

  let expensePieChart = null;

  function fetchAndRenderExpensePie(year, month) {
    let url = `/dashboard/api/expense-categories/?`;
    if (year) url += `year=${year}&`;
    if (month) url += `month=${month}`;
    fetch(url)
      .then((response) => response.json())
      .then((data) => {
        const chartContainer = ctx.parentElement;
        // Remove previous message if any
        const prevMsg = chartContainer.querySelector(".no-data-message");
        if (prevMsg) prevMsg.remove();
        if (
          !data.labels ||
          !data.datasets ||
          !data.labels.length ||
          !data.datasets.length ||
          !data.datasets[0].data.length ||
          data.datasets[0].data.every((v) => v === 0)
        ) {
          if (expensePieChart) {
            expensePieChart.destroy();
            expensePieChart = null;
          }
          // Show message
          const msg = document.createElement("div");
          msg.className = "no-data-message";
          msg.textContent = "No data for Year and Month";
          msg.style.textAlign = "center";
          msg.style.padding = "40px 0";
          msg.style.color = "#aaa";
          msg.style.fontSize = "1.1rem";
          chartContainer.appendChild(msg);
          return;
        }
        if (expensePieChart) {
          expensePieChart.destroy();
        }
        expensePieChart = new Chart(ctx, {
          type: "doughnut",
          data: data,
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: "bottom",
                labels: {
                  padding: 20,
                  usePointStyle: true,
                  color: getComputedStyle(
                    document.documentElement
                  ).getPropertyValue("--text-color"),
                },
              },
              tooltip: {
                callbacks: {
                  label: function (context) {
                    const value = context.parsed;
                    const total = context.dataset.data.reduce(
                      (a, b) => a + b,
                      0
                    );
                    const percentage = ((value / total) * 100).toFixed(1);
                    return `${
                      context.label
                    }: $${value.toLocaleString()} (${percentage}%)`;
                  },
                },
              },
            },
          },
        });
      })
      .catch((error) => {
        console.error("Error fetching expense categories data:", error);
      });
  }

  const yearSelect = document.getElementById("expense-categories-year");
  const monthSelect = document.getElementById("expense-categories-month");

  // Dynamically populate year dropdown from backend and render chart after years are loaded
  fetch("/dashboard/api/expense-years/")
    .then((response) => response.json())
    .then((data) => {
      if (data.years && data.years.length > 0) {
        // Fill dropdown in descending order
        yearSelect.innerHTML = data.years
          .map((year) => `<option value="${year}">${year}</option>`)
          .join("");
        // Default to latest year
        yearSelect.value = data.years[0];
        // Set month to current month if not already set
        const now = new Date();
        monthSelect.value = (now.getMonth() + 1).toString();
        // Initial chart render
        fetchAndRenderExpensePie(yearSelect.value, monthSelect.value);
      }
    });

  // Add event listeners for year and month dropdowns
  if (yearSelect && monthSelect) {
    yearSelect.addEventListener("change", function () {
      fetchAndRenderExpensePie(yearSelect.value, monthSelect.value);
    });
    monthSelect.addEventListener("change", function () {
      fetchAndRenderExpensePie(yearSelect.value, monthSelect.value);
    });
  }
}

function initIncomeExpenseChart() {
  const ctx = document.getElementById("incomeExpenseChart");
  if (!ctx) return;

  // Fetch real data from backend
  fetch("/dashboard/api/income-expenses/")
    .then((response) => response.json())
    .then((data) => {
      if (data.error) {
        console.error("Error fetching income vs expenses data:", data.error);
        return;
      }

      new Chart(ctx, {
        type: "bar",
        data: data,
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: "top",
              labels: {
                color: getComputedStyle(
                  document.documentElement
                ).getPropertyValue("--text-color"),
              },
            },
          },
          scales: {
            x: {
              ticks: {
                color: getComputedStyle(
                  document.documentElement
                ).getPropertyValue("--text-color"),
              },
              grid: {
                color: "rgba(255, 255, 255, 0.1)",
              },
            },
            y: {
              beginAtZero: true,
              ticks: {
                color: getComputedStyle(
                  document.documentElement
                ).getPropertyValue("--text-color"),
                callback: function (value) {
                  return "$" + value.toLocaleString();
                },
              },
              grid: {
                color: "rgba(255, 255, 255, 0.1)",
              },
            },
          },
        },
      });
    })
    .catch((error) => {
      console.error("Error fetching income vs expenses data:", error);
    });
}

function initSavingsChart() {
  const ctx = document.getElementById("savingsChart");
  if (!ctx) return;

  // Fetch real data from backend
  fetch("/dashboard/api/savings/")
    .then((response) => response.json())
    .then((data) => {
      if (data.error) {
        console.error("Error fetching savings data:", data.error);
        return;
      }

      new Chart(ctx, {
        type: "line",
        data: data,
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: "top",
              labels: {
                color: getComputedStyle(
                  document.documentElement
                ).getPropertyValue("--text-color"),
              },
            },
          },
          scales: {
            x: {
              ticks: {
                color: getComputedStyle(
                  document.documentElement
                ).getPropertyValue("--text-color"),
              },
              grid: {
                color: "rgba(255, 255, 255, 0.1)",
              },
            },
            y: {
              beginAtZero: true,
              ticks: {
                color: getComputedStyle(
                  document.documentElement
                ).getPropertyValue("--text-color"),
                callback: function (value) {
                  return "$" + value.toLocaleString();
                },
              },
              grid: {
                color: "rgba(255, 255, 255, 0.1)",
              },
            },
          },
        },
      });
    })
    .catch((error) => {
      console.error("Error fetching savings data:", error);
    });
}

function initBudgetProgress() {
  const dashboardBudgetRenderer = new BudgetRenderer(
    "categories-container",
    "/get-budget-rankings/"
  );
  let year, month;
  const yearSelect = document.getElementById("dashboard-budget-year");
  const monthSelect = document.getElementById("dashboard-budget-month");
  if (yearSelect && monthSelect) {
    year = yearSelect.value;
    month = monthSelect.value;
  } else {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth() + 1;
  }
  console.log(year, month)
  dashboardBudgetRenderer.fetchAndRender({ year, month });
}

// 5. Top Categories List
function initTopCategories() {
  const container = document.getElementById("top-categories");
  if (!container) return;

  // Function to fetch and render categories data
  function fetchAndRenderCategories(period = "30d") {
    const url = `/dashboard/api/top-categories/?period=${period}`;

    fetch(url)
      .then((response) => response.json())
      .then((data) => {
        if (data.error) {
          console.error("Error fetching top categories data:", data.error);
          return;
        }

        const categories = data.categories || [];

        // Render list view
        let categoryHTML = "";
        categories.forEach((category, index) => {
          categoryHTML += `
            <div class="category-item">
              <div class="category-rank">#${index + 1}</div>
              <div class="category-info">
                <div class="category-name">${category.name}</div>
              </div>
              <div class="category-stats">
                <div class="category-amount">$${category.amount.toLocaleString()}</div>
                <div class="category-count">${
                  category.transactions
                } transactions</div>
              </div>
            </div>
          `;
        });

        container.innerHTML = categoryHTML;

        // Render table view
        const tableContainer = document.getElementById("categories-table");
        if (tableContainer) {
          let tableHTML = `
            <table class="categories-table">
              <thead>
                <tr>
                  <th>Category</th>
                  <th>Transactions</th>
                  <th>Amount</th>
                </tr>
              </thead>
              <tbody>
          `;

          categories.forEach((category, index) => {
            tableHTML += `
              <tr class="category-row">
                <td class="category-name-cell">
                  <div class="category-rank-small">#${index + 1}</div>
                  <span>${category.name}</span>
                </td>
                <td class="category-transactions-cell">${
                  category.transactions
                }</td>
                <td class="category-amount-cell">$${category.amount.toLocaleString()}</td>
              </tr>
            `;
          });

          tableHTML += `
              </tbody>
            </table>
          `;

          tableContainer.innerHTML = tableHTML;
        }
      })
      .catch((error) => {
        console.error("Error fetching top categories data:", error);
      });
  }

  // Add CSS for category list and table if not already added
  if (!document.getElementById("category-list-styles")) {
    const style = document.createElement("style");
    style.id = "category-list-styles";
    style.textContent = `
            .category-item {
                display: flex;
                align-items: center;
                padding: 15px 0;
                border-bottom: 1px solid var(--main-color);
            }
            .category-item:last-child {
                border-bottom: none;
            }
            .category-rank {
                width: 30px;
                height: 30px;
                background: var(--green-color);
                color: #000;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 600;
                font-size: 0.8rem;
                margin-right: 15px;
            }
            .category-info {
                flex: 1;
            }
            .category-name {
                font-weight: 500;
                margin-bottom: 3px;
            }
            .category-description {
                font-size: 0.8rem;
                color: var(--text-color);
            }
            .category-stats {
                text-align: right;
            }
            .category-amount {
                font-weight: 600;
                color: var(--title-color);
            }
            .category-count {
                font-size: 0.8rem;
                color: var(--text-color);
            }

            /* Table Styles */
            .categories-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                background: var(--main-color);
                border-radius: var(--secondary-radius);
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .categories-table thead {
                background: var(--green-color);
                color: #000;
            }
            .categories-table th {
                padding: 15px;
                text-align: left;
                font-weight: 600;
                font-size: 0.9rem;
            }
            .categories-table td {
                padding: 12px 15px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                color: var(--text-color);
            }
            .categories-table tr:last-child td {
                border-bottom: none;
            }
            .categories-table tr:hover {
                background: rgba(255, 255, 255, 0.05);
            }
            .category-name-cell {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .category-rank-small {
                width: 24px;
                height: 24px;
                background: var(--green-color);
                color: #000;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 600;
                font-size: 0.7rem;
            }
            .category-transactions-cell {
                text-align: center;
                font-weight: 500;
            }
            .category-amount-cell {
                text-align: right;
                font-weight: 600;
                color: var(--title-color);
            }

            /* View Toggle Styles */
            .view-toggle {
                display: flex;
                gap: 5px;
                margin-left: 15px;
            }
            .view-btn {
                background: var(--main-color);
                border: 1px solid var(--green-color);
                color: var(--green-color);
                padding: 8px 12px;
                border-radius: 6px;
                cursor: pointer;
                transition: all 0.3s ease;
                font-size: 0.9rem;
            }
            .view-btn:hover {
                background: var(--green-color);
                color: #000;
            }
            .view-btn.active {
                background: var(--green-color);
                color: #000;
            }
            .card-controls {
                display: flex;
                align-items: center;
            }

            /* Responsive Design */
            @media (max-width: 768px) {
                .card-controls {
                    flex-direction: column;
                    gap: 10px;
                    align-items: flex-start;
                }
                .view-toggle {
                    margin-left: 0;
                }
                .categories-table {
                    font-size: 0.8rem;
                }
                .categories-table th,
                .categories-table td {
                    padding: 8px 10px;
                }
            }
        `;
    document.head.appendChild(style);
  }

  // Initial load with default period
  fetchAndRenderCategories("30d");

  // Set initial display state
  const tableContainer = document.getElementById("categories-table");
  if (tableContainer) {
    tableContainer.style.display = "none";
  }

  // Add event listener for period dropdown
  const periodSelect = document.getElementById("categories-period");
  if (periodSelect) {
    periodSelect.addEventListener("change", function () {
      const selectedPeriod = this.value;
      fetchAndRenderCategories(selectedPeriod);
    });
  }

  // Add event listeners for view toggle
  const viewButtons = document.querySelectorAll(".view-btn");
  viewButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const view = this.getAttribute("data-view");

      // Update active button
      viewButtons.forEach((btn) => btn.classList.remove("active"));
      this.classList.add("active");

      // Show/hide views
      const listContainer = document.getElementById("top-categories");
      const tableContainer = document.getElementById("categories-table");

      if (view === "list") {
        listContainer.style.display = "block";
        tableContainer.style.display = "none";
      } else {
        listContainer.style.display = "none";
        tableContainer.style.display = "block";
      }
    });
  });
}

// function addDashboardBudgetControls() {
//   const container = document.getElementById("dashboard-budget-categories");
//   if (!container) return;

//   // Create controls wrapper
//   const controls = document.createElement("div");
//   controls.className = "budget-controls";

//   // Year dropdown
//   const yearSelect = document.createElement("select");
//   yearSelect.className = "budget-dropdown";
//   yearSelect.id = "dashboard-budget-year";

//   // Month dropdown
//   const monthSelect = document.createElement("select");
//   monthSelect.className = "budget-dropdown";
//   monthSelect.id = "dashboard-budget-month";

//   // Populate months
//   const months = [
//     "January",
//     "February",
//     "March",
//     "April",
//     "May",
//     "June",
//     "July",
//     "August",
//     "September",
//     "October",
//     "November",
//     "December",
//   ];
//   months.forEach((month, idx) => {
//     const opt = document.createElement("option");
//     opt.value = idx + 1;
//     opt.textContent = month;
//     monthSelect.appendChild(opt);
//   });

//   controls.appendChild(yearSelect);
//   controls.appendChild(monthSelect);
//   container.parentNode.insertBefore(controls, container);

//   // Fetch years from backend
//   fetch("/dashboard/api/expense-years/")
//     .then((response) => response.json())
//     .then((data) => {
//       if (data.years && data.years.length > 0) {
//         yearSelect.innerHTML = data.years
//           .map((year) => `<option value="${year}">${year}</option>`)
//           .join("");
//         // Default to latest year
//         yearSelect.value = data.years[0];
//         // Set month to current month
//         const now = new Date();
//         monthSelect.value = (now.getMonth() + 1).toString();
//         // Initial render
//         window.initBudgetProgress();
//       }
//     });

//   // Add event listeners
//   yearSelect.addEventListener("change", window.initBudgetProgress);
//   monthSelect.addEventListener("change", window.initBudgetProgress);
// }
