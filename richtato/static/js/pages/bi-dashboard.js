// BI Dashboard JavaScript - Common Personal Finance Graphs

document.addEventListener("DOMContentLoaded", function () {
  initializeDashboard();
});

function initializeDashboard() {
  // Initialize all charts and components
  initCashFlowChart();
  initExpensePieChart();
  initIncomeExpenseChart();
  initSavingsChart();
  initSpendingHeatmap();
  initBudgetProgress();
  initTopCategories();
}

// 1. Cash Flow Trend Chart (Line Chart)
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
                  color: "#ffffff",
                },
              },
              zoom: {
                zoom: {
                  wheel: { enabled: true },
                  pinch: { enabled: true },
                  mode: "x",
                },
                pan: {
                  enabled: true,
                  mode: "x",
                },
              },
            },
            scales: {
              x: {
                ticks: {
                  color: "#ffffff",
                },
                grid: {
                  color: "rgba(255, 255, 255, 0.1)",
                },
              },
              y: {
                beginAtZero: true,
                ticks: {
                  color: "#ffffff",
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

// 2. Expense Categories Pie Chart
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
        if (data.error) {
          console.error("Error fetching expense categories data:", data.error);
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
                  color: "#ffffff",
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

  // Get current year and month
  const now = new Date();
  const currentYear = now.getFullYear();
  const currentMonth = now.getMonth() + 1;

  // Set dropdowns to current year and month
  const yearSelect = document.getElementById("expense-categories-year");
  const monthSelect = document.getElementById("expense-categories-month");
  if (yearSelect) yearSelect.value = currentYear;
  if (monthSelect) monthSelect.value = currentMonth;

  // Initial load
  fetchAndRenderExpensePie(currentYear, currentMonth);

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

// 3. Income vs Expenses Bar Chart
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
                color: "#ffffff",
              },
            },
          },
          scales: {
            x: {
              ticks: {
                color: "#ffffff",
              },
              grid: {
                color: "rgba(255, 255, 255, 0.1)",
              },
            },
            y: {
              beginAtZero: true,
              ticks: {
                color: "#ffffff",
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

// 4. Savings Accumulation Chart
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
                color: "#ffffff",
              },
            },
          },
          scales: {
            x: {
              ticks: {
                color: "#ffffff",
              },
              grid: {
                color: "rgba(255, 255, 255, 0.1)",
              },
            },
            y: {
              beginAtZero: true,
              ticks: {
                color: "#ffffff",
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

// 5. Spending Patterns Heatmap
function initSpendingHeatmap() {
  const container = document.getElementById("spendingHeatmap");
  if (!container) return;

  // Simple heatmap representation
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const categories = ["Food", "Transport", "Shopping", "Entertainment"];

  let heatmapHTML = '<div class="heatmap-grid">';
  heatmapHTML += '<div class="heatmap-header"><div></div>';
  days.forEach((day) => {
    heatmapHTML += `<div class="day-label">${day}</div>`;
  });
  heatmapHTML += "</div>";

  categories.forEach((category) => {
    heatmapHTML += `<div class="heatmap-row">`;
    heatmapHTML += `<div class="category-label">${category}</div>`;
    days.forEach(() => {
      const intensity = Math.random();
      const opacity = 0.2 + intensity * 0.8;
      heatmapHTML += `<div class="heatmap-cell" style="background-color: rgba(152, 204, 44, ${opacity})" title="$${Math.round(
        intensity * 200
      )}"></div>`;
    });
    heatmapHTML += "</div>";
  });
  heatmapHTML += "</div>";

  container.innerHTML = heatmapHTML;

  // Add CSS for heatmap
  const style = document.createElement("style");
  style.textContent = `
        .heatmap-grid {
            display: grid;
            grid-template-columns: 100px repeat(7, 1fr);
            gap: 2px;
        }
        .heatmap-header {
            display: contents;
        }
        .day-label, .category-label {
            font-size: 0.8rem;
            padding: 8px;
            text-align: center;
            font-weight: 500;
        }
        .heatmap-row {
            display: contents;
        }
        .heatmap-cell {
            height: 30px;
            border-radius: 4px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .heatmap-cell:hover {
            transform: scale(1.1);
        }
    `;
  document.head.appendChild(style);
}

// 6. Budget Progress Bars
function initBudgetProgress() {
  const container = document.getElementById("budget-progress");
  if (!container) return;

  // Fetch real budget data from backend
  fetch("/dashboard/api/budget-progress/")
    .then((response) => response.json())
    .then((data) => {
      if (data.error) {
        console.error("Error fetching budget progress data:", data.error);
        return;
      }

      const budgets = data.budgets || [];
      const colors = [
        "#98CC2C",
        "#4CAF50",
        "#81C784",
        "#A5D6A7",
        "#C8E6C9",
        "#E8F5E8",
      ];

      let progressHTML = "";
      budgets.forEach((item, index) => {
        const percentage = item.percentage;
        const status =
          percentage > 90 ? "warning" : percentage > 100 ? "over" : "good";
        const color = colors[index % colors.length];

        progressHTML += `
                    <div class="budget-item">
                        <div class="budget-header">
                            <span class="budget-category">${
                              item.category
                            }</span>
                            <span class="budget-amount">$${item.spent.toLocaleString()} / $${item.budget.toLocaleString()}</span>
                        </div>
                        <div class="budget-bar">
                            <div class="budget-fill ${status}" style="width: ${Math.min(
          percentage,
          100
        )}%; background-color: ${color}"></div>
                        </div>
                        <div class="budget-percentage">${percentage.toFixed(
                          1
                        )}%</div>
                    </div>
                `;
      });

      container.innerHTML = progressHTML;

      // Add CSS for budget progress if not already added
      if (!document.getElementById("budget-progress-styles")) {
        const style = document.createElement("style");
        style.id = "budget-progress-styles";
        style.textContent = `
                    .budget-item {
                        margin-bottom: 20px;
                    }
                    .budget-header {
                        display: flex;
                        justify-content: space-between;
                        margin-bottom: 8px;
                        font-size: 0.9rem;
                    }
                    .budget-category {
                        font-weight: 500;
                    }
                    .budget-amount {
                        color: var(--text-color);
                    }
                    .budget-bar {
                        height: 12px;
                        background: var(--main-color);
                        border-radius: 6px;
                        overflow: hidden;
                        margin-bottom: 5px;
                    }
                    .budget-fill {
                        height: 100%;
                        transition: width 0.3s ease;
                        border-radius: 6px;
                    }
                    .budget-fill.warning {
                        opacity: 0.8;
                    }
                    .budget-fill.over {
                        background-color: #FF6B6B !important;
                    }
                    .budget-percentage {
                        text-align: right;
                        font-size: 0.8rem;
                        color: var(--text-color);
                    }
                `;
        document.head.appendChild(style);
      }
    })
    .catch((error) => {
      console.error("Error fetching budget progress data:", error);
    });
}

// 7. Top Categories List
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
