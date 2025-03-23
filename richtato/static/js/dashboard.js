document.addEventListener("DOMContentLoaded", () => {
  const expenseOverviewLineChart = document
    .getElementById("expense-overview-line-chart")
    .getContext("2d");
  plotOverviewLineChart(expenseOverviewLineChart, "/expense/get-last-30-days/");

  const incomeOverviewLineChart = document
    .getElementById("income-overview-line-chart")
    .getContext("2d");
  plotOverviewLineChart(incomeOverviewLineChart, "/income/get-last-30-days/");
});

async function plotOverviewLineChart(ctx, endpointUrl) {
  try {
    const response = await fetch(endpointUrl);
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    const chartData = await response.json();
    const dataset = chartData.datasets[0];
    console.log(dataset);
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

async function fetchProgress() {
  try {
    // const response = await fetch('/api/progress');
    // if (!response.ok) {
    //   throw new Error('Failed to fetch progress data');
    // }
    // const data = await response.json();
    // return data.progress;
    return 50; // Fallback to 50% for testing
  } catch (error) {
    console.error('Error fetching progress:', error);
    return 0; // Fallback to 0% if there's an error
  }
}

function updateIconBasedOnTitle(containerId) {
  // Get the container
  const container = document.querySelector(`#${containerId}`);

  // Get the title (first <li> inside the ul)
  const titleElement = container.querySelector('.third-box-info ul li:first-child');
  const iconElement = container.querySelector('.icon i');

  // Get the title text
  const title = titleElement.textContent.trim();

  // Set icon class based on title
  switch (title.toLowerCase()) {
    case 'travel':
      iconElement.className = 'fa-solid fa-plane fa-lg';  // Change to a plane icon for Travel
      break;
    case 'shopping':
      iconElement.className = 'fa-solid fa-shopping-cart fa-lg';  // Change to shopping cart icon for Shopping
      break;
    case 'food':
      iconElement.className = 'fa-solid fa-utensils fa-lg';  // Change to utensils icon for Food
      break;
    default:
      iconElement.className = 'fa-solid fa-question fa-lg';  // Default icon if the title is not recognized
  }
}

function updateIconsForAllSections() {
  // Select all elements with the class 'third-box-section2-details'
  const allContainers = document.querySelectorAll('.third-box-section2-details');

  const categoryIcons = {
    'travel': 'fa-plane',
    'shopping': 'fa-shopping-cart',
    'groceries': 'fa-shopping-basket',
    'food': 'fa-utensils',
    'entertainment': 'fa-tv',
    'utilities': 'fa-plug',
    'rent/mortgage': 'fa-home',
    'insurance': 'fa-shield-alt',
    'healthcare': 'fa-hospital',
    'transportation': 'fa-car',
    'education': 'fa-graduation-cap',
    'savings': 'fa-piggy-bank',
    'gifts': 'fa-gift',
    'electronics': 'fa-laptop',
    'sports': 'fa-basketball-ball',
    'dining out': 'fa-utensils',
    'investments': 'fa-chart-line',
    'subscriptions': 'fa-file-alt',
    'home improvement': 'fa-tools',
    'charity/donations': 'fa-heart'
  };

  // Loop through each container
  allContainers.forEach(container => {
    // Get the title (first <li> inside the ul)
    const titleElement = container.querySelector('.third-box-info ul li:first-child');
    const iconElement = container.querySelector('.icon i');

    // Get the title text
    const title = titleElement.textContent.trim().toLowerCase();

    // Set icon class based on the category
    if (categoryIcons[title]) {
      iconElement.className = `fa-solid ${categoryIcons[title]} fa-lg`;
    } else {
      iconElement.className = 'fa-solid fa-question fa-lg'; // Default icon for unrecognized titles
    }
  });
}

function updatePercentageBar(percentageId, percentage) {
  const percentageBar = document.getElementById(percentageId);
  percentageBar.style.width = percentage + '%';
  percentageBar.style.backgroundColor = percentage >= 100 ? 'red' : 'green';
}

updatePercentageBar('percentage-1', 100);
updatePercentageBar('percentage-2', 100);
updatePercentageBar('percentage-3', 50);

updateIconsForAllSections()