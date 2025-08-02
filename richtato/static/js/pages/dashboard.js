// Dashboard JavaScript - Common Personal Finance Graphs

function getAccountTypeIcon(typeCode) {
  const typeIcons = {
    'checking': 'fas fa-university',
    'savings': 'fas fa-piggy-bank',
    'retirement': 'fas fa-chart-line',
    'investment': 'fas fa-chart-pie'
  };
  return typeIcons[typeCode] || 'fas fa-university';
}

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
          // Show consistent no-data message
          const msg = document.createElement("div");
          msg.className = "no-data-message";
          msg.innerHTML = `
            <i class="fa-solid fa-chart-pie" style="font-size: 2rem; color: var(--title-color); opacity: 0.5; margin-bottom: 10px;"></i>
            <p style="color: var(--title-color); text-align: center; margin: 0; font-size: 14px;">
              No expense data for selected period
            </p>
            <p style="color: var(--title-color); text-align: center; margin: 5px 0 0 0; font-size: 12px; opacity: 0.7;">
              Try selecting a different month or year
            </p>
          `;
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
        const chartContainer = ctx.parentElement;
        // Remove previous message if any
        const prevMsg = chartContainer.querySelector(".no-data-message");
        if (prevMsg) prevMsg.remove();

        if (expensePieChart) {
          expensePieChart.destroy();
          expensePieChart = null;
        }

        // Show error message
        const msg = document.createElement("div");
        msg.className = "no-data-message";
        msg.innerHTML = `
          <i class="fa-solid fa-exclamation-triangle" style="font-size: 2rem; color: var(--red-color); opacity: 0.7; margin-bottom: 10px;"></i>
          <p style="color: var(--title-color); text-align: center; margin: 0; font-size: 14px;">
            Unable to load expense breakdown
          </p>
          <p style="color: var(--title-color); text-align: center; margin: 5px 0 0 0; font-size: 12px; opacity: 0.7;">
            Please try refreshing the page
          </p>
        `;
        chartContainer.appendChild(msg);
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
  const containers = {
    checking: document.getElementById("checking-accounts-dashboard"),
    savings: document.getElementById("savings-accounts-dashboard"),
    investment: document.getElementById("investment-accounts-dashboard"),
    retirement: document.getElementById("retirement-accounts-dashboard")
  };

  // Check if containers exist
  const missingContainers = Object.entries(containers)
    .filter(([type, container]) => !container)
    .map(([type]) => type);

  if (missingContainers.length > 0) {
    console.error('Dashboard account containers not found:', missingContainers);
    return;
  }

  function fetchAndRenderAssets() {
    fetch("/api/accounts/")
      .then((response) => response.json())
      .then((data) => {
        const assets = data.rows || [];

        // Clear all containers first
        Object.values(containers).forEach(container => {
          container.innerHTML = '';
        });

        if (assets.length === 0) {
          // Show "no accounts" message in the first container
          containers.checking.innerHTML = `
            <div class="no-data-message">
              <i class="fa-solid fa-university" style="font-size: 2rem; color: var(--title-color); opacity: 0.5; margin-bottom: 10px;"></i>
              <p style="color: var(--title-color); text-align: center; margin: 0; font-size: 14px;">
                No accounts found
              </p>
              <p style="color: var(--title-color); text-align: center; margin: 5px 0 0 0; font-size: 12px; opacity: 0.7;">
                Add your first account to get started
              </p>
            </div>
          `;
          return;
        }

        // Group accounts by type
        const groupedAssets = {
          checking: [],
          savings: [],
          investment: [],
          retirement: []
        };

        assets.forEach(asset => {
          const type = asset.type?.toLowerCase();
          if (groupedAssets[type]) {
            groupedAssets[type].push(asset);
          } else {
            // Default to checking if type is unknown
            groupedAssets.checking.push(asset);
          }
        });

        // Render accounts in each group
        Object.entries(groupedAssets).forEach(([type, typeAssets]) => {
          const container = containers[type];

          if (typeAssets.length === 0) {
            container.innerHTML = `
              <div class="no-accounts-message" style="text-align: center; padding: 20px; color: var(--title-color); opacity: 0.6;">
                <p style="margin: 0; font-size: 14px;">No ${type} accounts</p>
              </div>
            `;
            return;
          }

          let tilesHTML = '';
          typeAssets.forEach((asset) => {
            const accountType = asset.type?.toLowerCase() || 'bank';
            const isCard = accountType.includes('card') || accountType.includes('credit');
            const tileClass = isCard ? 'account-tile card-account-tile' : 'account-tile';
            const iconClass = isCard ? 'card' : 'bank';
            const icon = isCard ? 'fa-credit-card' : getAccountTypeIcon(accountType);

            const balance = asset.balance && asset.balance !== '$0.00' ? asset.balance : 'No balance';

            tilesHTML += `
              <div class="${tileClass}" data-account-id="${asset.id || ''}" onclick="openAccountChart(${asset.id})" style="cursor: pointer;">
                <div class="account-tile-header">
                  <div class="account-tile-icon ${iconClass}">
                    <i class="fa-solid ${icon}"></i>
                  </div>
                  <div class="account-tile-info">
                    <h3>${asset.name || 'Unknown Account'}</h3>
                    <p>${asset.entity || 'Financial Institution'}</p>
                  </div>
                </div>
                <div class="account-tile-body">
                  <div class="account-tile-balance">${balance}</div>
                  <div class="account-tile-type">${asset.type || 'Account'}</div>
                </div>
                <div class="account-tile-footer">
                  <div class="account-tile-status">${asset.date ? `Updated ${asset.date}` : 'No recent update'}</div>
                </div>
              </div>
            `;
          });

          container.innerHTML = tilesHTML;
        });
      })
      .catch((error) => {
        console.error("Error fetching assets data:", error);
        // Show error in first container
        containers.checking.innerHTML = `
          <div class="no-data-message">
            <i class="fa-solid fa-exclamation-triangle" style="font-size: 2rem; color: var(--red-color); opacity: 0.7; margin-bottom: 10px;"></i>
            <p style="color: var(--title-color); text-align: center; margin: 0; font-size: 14px;">
              Unable to load accounts
            </p>
            <p style="color: var(--title-color); text-align: center; margin: 5px 0 0 0; font-size: 12px; opacity: 0.7;">
              Please try refreshing the page
            </p>
          </div>
        `;
      });
  }
  fetchAndRenderAssets();
}

// Function to open account transaction chart
function openAccountChart(accountId) {
  if (accountId) {
    window.location.href = `/accounts/${accountId}/chart/`;
  }
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
          container.innerHTML = `
            <div class="no-data-message">
              <i class="fa-solid fa-exclamation-triangle" style="font-size: 2rem; color: var(--red-color); opacity: 0.7; margin-bottom: 10px;"></i>
              <p style="color: var(--title-color); text-align: center; margin: 0; font-size: 14px;">
                Unable to load spending categories
              </p>
              <p style="color: var(--title-color); text-align: center; margin: 5px 0 0 0; font-size: 12px; opacity: 0.7;">
                Please try refreshing the page
              </p>
            </div>
          `;
          return;
        }

        const categories = data.categories || [];

        // Check if there are no categories
        if (categories.length === 0) {
          container.innerHTML = `
            <div class="no-data-message">
              <i class="fa-solid fa-chart-line" style="font-size: 2rem; color: var(--title-color); opacity: 0.5; margin-bottom: 10px;"></i>
              <p style="color: var(--title-color); text-align: center; margin: 0; font-size: 14px;">
                No spending data for the selected period
              </p>
              <p style="color: var(--title-color); text-align: center; margin: 5px 0 0 0; font-size: 12px; opacity: 0.7;">
                Add some expenses to see your top categories
              </p>
            </div>
          `;
          return;
        }

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
      })
      .catch((error) => {
        console.error("Error fetching top categories data:", error);
        container.innerHTML = `
          <div class="no-data-message">
            <i class="fa-solid fa-wifi" style="font-size: 2rem; color: var(--red-color); opacity: 0.7; margin-bottom: 10px;"></i>
            <p style="color: var(--title-color); text-align: center; margin: 0; font-size: 14px;">
              Connection error
            </p>
            <p style="color: var(--title-color); text-align: center; margin: 5px 0 0 0; font-size: 12px; opacity: 0.7;">
              Check your internet connection and try again
            </p>
          </div>
        `;
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

  // Set container dimensions for proper containment
  container.style.width = "100%";
  container.style.height = "500px";
  container.style.position = "relative";
  container.style.overflow = "hidden";
  // Load Plotly.js if not already loaded
  if (typeof Plotly === "undefined") {
    const script = document.createElement("script");
    script.src = "https://cdn.plot.ly/plotly-2.27.0.min.js";
    script.onload = function () {
      fetchAndRenderSankey();
    };
    document.head.appendChild(script);
  } else {
    fetchAndRenderSankey();
  }

  function fetchAndRenderSankey() {
    fetch("/dashboard/api/sankey-data/")
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          // Get container dimensions with padding adjustment
          const containerWidth = container.clientWidth - 20; // Account for padding
          const containerHeight = container.clientHeight - 20; // Account for padding

          // Update the layout to be properly contained
          const layout = {
            ...data.data.layout,
            width: containerWidth,
            height: containerHeight,
            autosize: false, // Disable autosize to prevent overflow
            margin: { l: 20, r: 20, t: 40, b: 20 }, // Reduced margins
            paper_bgcolor: "rgba(0,0,0,0)",
            plot_bgcolor: "rgba(0,0,0,0)",
            font: {
              size: 12,
              color: "#ffffff",
              family: "Open Sans, sans-serif"
            },
            hoverlabel: {
              bgcolor: "#2d2d2d",
              bordercolor: "#98cc2c",
              font: { color: "#ffffff", family: "Open Sans, sans-serif" }
            },
          };

          // Calculate node-local percentages for each link
          const sankeyData = data.data.data[0];
          const values = sankeyData.link.value;
          const sources = sankeyData.link.source;
          // Sum outgoing values for each source node
          const sourceTotals = {};
          sources.forEach((src, i) => {
            sourceTotals[src] = (sourceTotals[src] || 0) + values[i];
          });
          // Calculate percentage for each link relative to its source node
          sankeyData.link.customdata = values.map((v, i) => {
            const pct = sourceTotals[sources[i]]
              ? (v / sourceTotals[sources[i]]) * 100
              : 0;
            return pct.toFixed(1) + "%";
          });
          sankeyData.link.hovertemplate =
            "%{source.label} → %{target.label}<br>Value: %{value}<br>Percent: %{customdata}<extra></extra>";

          // Render the chart with proper containment
          Plotly.newPlot("sankey-cash-flow", data.data.data, layout, {
            responsive: false, // Disable responsive to prevent overflow
            displayModeBar: false,
            staticPlot: false,
            scrollZoom: false,
            doubleClick: false,
            showTips: false,
            displaylogo: false,
            autosize: false, // Disable autosize
            modeBarButtonsToRemove: ['zoom2d', 'pan2d', 'select2d', 'lasso2d', 'autoScale2d'],
          });

          // Handle window resize for responsiveness
          let resizeTimeout;
          window.addEventListener("resize", function () {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
              const newWidth = container.clientWidth - 20;
              const newHeight = container.clientHeight - 20;

              if (newWidth > 0 && newHeight > 0) {
                Plotly.relayout("sankey-cash-flow", {
                  width: newWidth,
                  height: newHeight,
                });
              }
            }, 250); // Debounce the resize event
          });
        } else {
          console.error("Failed to load Sankey data:", data.error);
          container.innerHTML = "<p>Failed to load cash flow chart</p>";
        }
      })
      .catch((error) => {
        console.error("Error fetching Sankey data:", error);
        container.innerHTML = "<p>Error loading cash flow chart</p>";
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
