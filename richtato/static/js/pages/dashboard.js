// Dashboard JavaScript - Common Personal Finance Graphs

document.addEventListener("DOMContentLoaded", function () {
  initializeDashboard();
});

function initializeDashboard() {
  // Initialize all charts and components
  // initCashFlowChart();
  initIncomeExpenseChart();
  initSavingsChart();
  initTopCategories();
  initExpensePieChart();
  initBudgetProgress();
  initAssetsSection();
  initSankeyChart();
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
                    return `${context.label
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
  console.log(year, month);
  dashboardBudgetRenderer.fetchAndRender({ year, month });
}

function initAssetsSection() {
  const tableContainer = document.getElementById("assets-table");
  if (!tableContainer) return;

  function fetchAndRenderAssets() {
    fetch("/api/accounts/")
      .then((response) => response.json())
      .then((data) => {
        const assets = data.rows || [];
        let tableHTML = '<table class="categories-table">';
        if (data.columns && data.columns.length) {
          tableHTML += "<thead><tr>";
          data.columns.forEach((col) => {
            if (col.field !== "id" && !col.field.includes("entity")) {
              tableHTML += `<th>${col.title}</th>`;
            }
          });
          tableHTML += "</tr></thead>";
        }
        tableHTML += "<tbody>";
        assets.forEach((asset) => {
          tableHTML += '<tr class="category-row">';
          data.columns.forEach((col) => {
            if (col.field !== "id" && !col.field.includes("entity")) {
              tableHTML += `<td>${asset[col.field] ?? ""}</td>`;
            }
          });
          tableHTML += "</tr>";
        });
        tableHTML += "</tbody></table>";
        tableContainer.innerHTML = tableHTML;
      })
      .catch((error) => {
        console.error("Error fetching assets data:", error);
      });
  }
  fetchAndRenderAssets();
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
                <div class="category-count">${category.transactions
            } transactions</div>
              </div>
            </div>
          `;
        });

        container.innerHTML = categoryHTML;
      })
      .catch((error) => {
        console.error("Error fetching top categories data:", error);
      });
  }

  // Initial load with default period
  fetchAndRenderCategories("30d");

  // Set initial display state
  const tableContainer = document.getElementById("categories-table");
  if (tableContainer) {
    tableContainer.style.display = "none";
  }
}

// 6. Sankey Chart
function initSankeyChart() {
  const container = document.getElementById("sankey-cash-flow");
  if (!container) return;

  // Load Plotly.js if not already loaded
  if (typeof Plotly === 'undefined') {
    const script = document.createElement('script');
    script.src = 'https://cdn.plot.ly/plotly-latest.min.js';
    script.onload = function () {
      fetchAndRenderSankey();
    };
    document.head.appendChild(script);
  } else {
    fetchAndRenderSankey();
  }

  function fetchAndRenderSankey() {
    fetch('/dashboard/api/sankey-data/')
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          // Get container dimensions for responsive sizing
          const containerWidth = container.clientWidth;
          const containerHeight = container.clientHeight || 500;

          // Update the layout to be responsive
          const layout = {
            ...data.data.layout,
            width: containerWidth, // Use full container width
            height: containerHeight, // Use full container height
            autosize: true,
            margin: { l: 20, r: 20, t: 60, b: 20 }
          };

          // Render the chart
          Plotly.newPlot('sankey-cash-flow', data.data.data, layout, {
            responsive: true,
            displayModeBar: false,
            staticPlot: false,
            scrollZoom: false,
            doubleClick: false,
            showTips: false,
            displaylogo: false,
            autosize: true
          });

          // Handle window resize for responsiveness
          window.addEventListener('resize', function () {
            const newWidth = container.clientWidth;
            const newHeight = container.clientHeight;

            Plotly.relayout('sankey-cash-flow', {
              width: newWidth,
              height: newHeight
            });
          });
        } else {
          console.error('Failed to load Sankey data:', data.error);
          container.innerHTML = '<p>Failed to load cash flow chart</p>';
        }
      })
      .catch(error => {
        console.error('Error fetching Sankey data:', error);
        container.innerHTML = '<p>Error loading cash flow chart</p>';
      });
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
