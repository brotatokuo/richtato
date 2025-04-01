function fetchAndRenderCategories(count) {
  let categoriesEndpoint = "/budget/get-budget-rankings/";
  if (count != null) {
    categoriesEndpoint += `?count=${encodeURIComponent(count)}`;
  }
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

function updatePercentageBar(percentageId, percentage) {
  const percentageBar = document.getElementById(percentageId);
  percentageBar.style.width = Math.abs(percentage) + '%';
  percentageBar.style.backgroundColor = percentage < 100 ? 'green' : 'red';
}

function updateIconForCategory(categoryName, iconElement) {
  const categoryIcons = {
    'travel': 'fa-plane',
    'shopping': 'fa-shopping-cart',
    'groceries': 'fa-shopping-basket',
    'entertainment': 'fa-tv',
    'utilities': 'fa-plug',
    'housing': 'fa-home',
    'medical': 'fa-hospital',
    'education': 'fa-graduation-cap',
    'savings': 'fa-piggy-bank',
    'gifts': 'fa-gift',
    'dining': 'fa-utensils',
    'investments': 'fa-chart-line',
    'subscriptions': 'fa-file-invoice',
    'charity/donations': 'fa-heart',
    'pet': 'fa-paw',
    'wholesale': 'fa-warehouse',
    'car': 'fa-car',
    'phone': 'fa-phone',
    'miscellaneous': 'fa-ellipsis',
  };

  if (categoryIcons[categoryName]) {
    iconElement.className = `fa-solid ${categoryIcons[categoryName]} fa-lg`;
  } else {
    iconElement.className = 'fa-solid fa-question fa-lg'; // Default icon for unknown category
  }
}

function togglePasswordVisibility(id, button) {
  console.log("togglePasswordVisibility called with id:", id);
  var passwordInput = document.getElementById(id);
  if (passwordInput.type === "password") {
    passwordInput.type = "text";
    button.textContent = "Hide";
  } else {
    passwordInput.type = "password";
    button.textContent = "Show";
  }
}

function getCSRFToken() {
  const cookieValue = document.cookie.match('(^|;)\\s*csrftoken\\s*=\\s*([^;]+)')?.pop();
  return cookieValue || '';
}

function getUserID() {
  return fetch('/get-user-id')
    .then(response => response.json())
    .then(data => data.userID);
}

function computeBalance(balance) {
  // Check if it's a formula starting with '='
  if (balance.startsWith('=')) {
    try {
      // Evaluate the formula (strip the leading '=')
      balance = eval(balance.slice(1));  // Caution: Use math.js for safety in production
      console.log('Evaluated formula:', balance);
    } catch (error) {
      console.error('Invalid formula:', error);
      return;  // Stop further processing if the formula is invalid
    }
  }


  // Convert to a float for regular numbers or evaluated formulas
  balance = parseFloat(balance).toFixed(2);
  return balance;
}
