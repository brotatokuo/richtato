document.addEventListener("DOMContentLoaded", () => {
  const expenseOverviewLineChart = document
    .getElementById("expense-overview-line-chart")
    .getContext("2d");
  plotOverviewLineChart(expenseOverviewLineChart, "/expense/get-last-30-days/");

  const incomeOverviewLineChart = document
    .getElementById("income-overview-line-chart")
    .getContext("2d");
  plotOverviewLineChart(incomeOverviewLineChart, "/income/get-last-30-days/");

  fetchAndRenderCategories();
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

// function updateIconsForAllSections() {
//   // Select all elements with the class 'third-box-section2-details'
//   const allContainers = document.querySelectorAll('.third-box-section2-details');

//   const categoryIcons = {
//     'travel': 'fa-plane',
//     'shopping': 'fa-shopping-cart',
//     'groceries': 'fa-shopping-basket',
//     'food': 'fa-utensils',
//     'entertainment': 'fa-tv',
//     'utilities': 'fa-plug',
//     'rent/mortgage': 'fa-home',
//     'insurance': 'fa-shield-alt',
//     'healthcare': 'fa-hospital',
//     'transportation': 'fa-car',
//     'education': 'fa-graduation-cap',
//     'savings': 'fa-piggy-bank',
//     'gifts': 'fa-gift',
//     'electronics': 'fa-laptop',
//     'sports': 'fa-basketball-ball',
//     'dining out': 'fa-utensils',
//     'investments': 'fa-chart-line',
//     'subscriptions': 'fa-file-alt',
//     'home improvement': 'fa-tools',
//     'charity/donations': 'fa-heart'
//   };

//   // Loop through each container
//   allContainers.forEach(container => {
//     // Get the title (first <li> inside the ul)
//     const titleElement = container.querySelector('.third-box-info ul li:first-child');
//     const iconElement = container.querySelector('.icon i');

//     // Get the title text
//     const title = titleElement.textContent.trim().toLowerCase();

//     // Set icon class based on the category
//     if (categoryIcons[title]) {
//       iconElement.className = `fa-solid ${categoryIcons[title]} fa-lg`;
//     } else {
//       iconElement.className = 'fa-solid fa-question fa-lg'; // Default icon for unrecognized titles
//     }
//   });
// }

// function updatePercentageBar(percentageId, percentage) {
//   const percentageBar = document.getElementById(percentageId);
//   percentageBar.style.width = percentage + '%';
//   percentageBar.style.backgroundColor = percentage >= 100 ? 'red' : 'green';
// }

// updateIconsForAllSections()

function fetchAndRenderCategories() {
  const categoriesEndpoint = "/budget/get-budget-rankings/";
  fetch(categoriesEndpoint)
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.json();
    })
    .then((data) => {
      const categories = data.category_rankings;
      const categoriesContainer = document.getElementById("categories-container");

      // Clear existing content
      categoriesContainer.innerHTML = '';

      categories.forEach((category, index) => {
        // Create the category container
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'third-box-section2-details';

        // Create the icon container
        const iconDiv = document.createElement('div');
        iconDiv.className = 'icon';
        const iconElement = document.createElement('i');
        iconElement.className = 'fa-solid fa-question fa-lg'; // Default icon, updated later
        iconDiv.appendChild(iconElement);

        // Create the category info (name, budget, diff)
        const infoDiv = document.createElement('div');
        infoDiv.className = 'third-box-info';

        const ulElement = document.createElement('ul');

        const nameLi = document.createElement('li');
        nameLi.textContent = category.name;

        const budgetLi = document.createElement('li');
        budgetLi.textContent = category.budget;

        const messageLi = document.createElement('li');
        messageLi.textContent = category.message;

        ulElement.appendChild(nameLi);
        ulElement.appendChild(budgetLi);
        ulElement.appendChild(messageLi);

        infoDiv.appendChild(ulElement);

        // Create the percentage bar
        const percentageBarDiv = document.createElement('div');
        percentageBarDiv.className = 'percentage-bar';
        const percentageDiv = document.createElement('div');
        percentageDiv.className = 'percentage';
        percentageDiv.id = `percentage-${index + 1}`;

        percentageBarDiv.appendChild(percentageDiv);
        infoDiv.appendChild(percentageBarDiv);

        // Append icon and info to the category container
        categoryDiv.appendChild(iconDiv);
        categoryDiv.appendChild(infoDiv);

        // Append the category container to the main container
        categoriesContainer.appendChild(categoryDiv);

        // Update the icon and percentage for each category
        updateIconForCategory(nameLi.textContent.trim().toLowerCase(), iconElement);
        updatePercentageBar(`percentage-${index + 1}`, category.percent);
      });
    })
    .catch((error) => console.error("Error fetching categories:", error));
}

function updateIconForCategory(categoryName, iconElement) {
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

  if (categoryIcons[categoryName]) {
    iconElement.className = `fa-solid ${categoryIcons[categoryName]} fa-lg`;
  } else {
    iconElement.className = 'fa-solid fa-question fa-lg'; // Default icon for unknown category
  }
}

function updatePercentageBar(percentageId, percentage) {
  const percentageBar = document.getElementById(percentageId);
  percentageBar.style.width = Math.abs(percentage) + '%';
  percentageBar.style.backgroundColor = percentage < 100 ? 'green' : 'red';
}