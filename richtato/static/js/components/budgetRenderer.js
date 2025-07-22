class BudgetRenderer {
  constructor(containerId, endpoint) {
    this.container = document.getElementById(containerId);
    this.endpoint = endpoint;
    this.categoryIcons = this.getCategoryIcons();
  }

  fetchAndRender({ count = null, year = null, month = null } = {}) {
    let url = new URL(this.endpoint, window.location.origin);
    const params = new URLSearchParams();

    if (count !== null) params.append("count", count);
    if (year !== null) params.append("year", year);
    if (month !== null) params.append("month", month);

    url.search = params.toString();
    console.log("Fetching categories from URL:", url.toString());
    fetch(url)
      .then(this._checkResponse)
      .then((data) => this._renderCategories(data.category_rankings))
      .catch((error) => console.error("Error fetching categories:", error));
  }

  _checkResponse(response) {
    if (!response.ok) {
      throw new Error("Network response was not ok");
    }
    return response.json();
  }

  _renderCategories(categories) {
    this.container.innerHTML = ""; // Clear old content
    categories.forEach((category, index) => {
      const categoryElement = this._createCategoryElement(category, index);
      this.container.appendChild(categoryElement);
    });
  }

  _createCategoryElement(category, index) {
    // Create a squarish widget with a circular progress ring
    const wrapper = this._createDiv("budget-category-item square-widget");

    // Create the circular progress ring with icon and text inside
    const ringDiv = this._createProgressRing(category, index);
    wrapper.appendChild(ringDiv);

    return wrapper;
  }

  _createProgressRing(category, index) {
    // SVG circular progress ring
    let percent = Math.abs(category.percent);
    const displayPercent = percent > 100 ? 100 : percent;
    const size = 130; // px, diameter of SVG (matches CSS)
    const stroke = 8; // px, thickness of ring
    const radius = (size - stroke) / 2;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference * (1 - displayPercent / 100);

    // Dynamic color: interpolate between green (0%) and red (100%)
    let color;
    if (percent <= 0) {
      color = "var(--green-color)";
    } else if (percent >= 100) {
      color = "var(--red-color)";
    } else {
      const greenHSL = { h: 88, s: 63, l: 48 };
      const redHSL = { h: 0, s: 100, l: 50 };
      const hue = greenHSL.h + (redHSL.h - greenHSL.h) * (displayPercent / 100);
      const sat = greenHSL.s + (redHSL.s - greenHSL.s) * (displayPercent / 100);
      const light = greenHSL.l + (redHSL.l - greenHSL.l) * (displayPercent / 100);
      color = `hsl(${hue}, ${sat}%, ${light}%)`;
    }

    // Create SVG
    const svgNS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(svgNS, "svg");
    svg.setAttribute("width", size);
    svg.setAttribute("height", size);
    svg.setAttribute("viewBox", `0 0 ${size} ${size}`);
    svg.classList.add("progress-ring-svg");

    // Background circle
    const bgCircle = document.createElementNS(svgNS, "circle");
    bgCircle.setAttribute("cx", size / 2);
    bgCircle.setAttribute("cy", size / 2);
    bgCircle.setAttribute("r", radius);
    bgCircle.setAttribute("fill", "none");
    const strokeColor = getComputedStyle(document.documentElement).getPropertyValue('--secondary-color');
    bgCircle.setAttribute("stroke", strokeColor.trim());
    bgCircle.setAttribute("stroke-width", stroke);
    svg.appendChild(bgCircle);

    // Progress circle
    const fgCircle = document.createElementNS(svgNS, "circle");
    fgCircle.setAttribute("cx", size / 2);
    fgCircle.setAttribute("cy", size / 2);
    fgCircle.setAttribute("r", radius);
    fgCircle.setAttribute("fill", "none");
    fgCircle.setAttribute("stroke", color);
    fgCircle.setAttribute("stroke-width", stroke);
    fgCircle.setAttribute("stroke-dasharray", circumference);
    fgCircle.setAttribute("stroke-dashoffset", offset);
    fgCircle.setAttribute("stroke-linecap", "round");
    fgCircle.setAttribute("transform", `rotate(-90 ${size / 2} ${size / 2})`);
    svg.appendChild(fgCircle);

    // Centered icon and text inside the ring
    const centerDiv = this._createDiv("progress-ring-center");
    // Icon
    const iconDiv = this._createIconElement(category.name);
    iconDiv.classList.add("progress-ring-icon");
    // Name
    const nameDiv = document.createElement("div");
    nameDiv.className = "progress-ring-name";
    nameDiv.textContent = category.name;
    // Amount left and percent
    const amountDiv = document.createElement("div");
    amountDiv.className = "progress-ring-amount";

    const numericBudget = parseFloat(category.budget.replace(/[^0-9.]/g, ""));
    const amountLeft = numericBudget * (1 - percent / 100);

    // Format the label and color based on amountLeft
    if (amountLeft > 0) {
      amountDiv.textContent = `$${amountLeft.toFixed(2)}`;
      amountDiv.style.color = "var(--green-color)";
    } else if (amountLeft === 0) {
      amountDiv.textContent = `0 left`;
      amountDiv.style.color = "#888"; // Gray
    } else {
      amountDiv.textContent = `$${Math.abs(amountLeft).toFixed(2)}`;
      amountDiv.style.color = "var(--red-color)";
    }

    // Stack icon, name, amount
    centerDiv.appendChild(iconDiv);
    centerDiv.appendChild(nameDiv);
    centerDiv.appendChild(amountDiv);

    // Wrap SVG and centerDiv in a container
    const ringContainer = this._createDiv("progress-ring-container");
    ringContainer.appendChild(svg);
    ringContainer.appendChild(centerDiv);
    return ringContainer;
  }

  _createInfoElement(category, index, compact = false) {
    const infoDiv = this._createDiv("budget-category-info");
    if (compact) {
      // Only show name and message in compact mode
      const nameDiv = document.createElement("div");
      nameDiv.className = "budget-category-name";
      nameDiv.textContent = category.name;
      const messageDiv = document.createElement("div");
      messageDiv.className = "budget-category-message";
      messageDiv.textContent = category.message;
      infoDiv.appendChild(nameDiv);
      infoDiv.appendChild(messageDiv);
    } else {
      const ul = document.createElement("ul");
      ["name", "budget", "message"].forEach((key) => {
        const li = document.createElement("li");
        li.textContent = category[key];
        ul.appendChild(li);
      });
      infoDiv.appendChild(ul);
    }
    return infoDiv;
  }

  _createIconElement(categoryName) {
    const iconDiv = this._createDiv("budget-category-icon");
    const icon = document.createElement("i");
    icon.className = "fa-solid fa-question fa-lg"; // Default

    const normalized = categoryName.trim().toLowerCase();
    if (this.categoryIcons[normalized]) {
      icon.className = `fa-solid ${this.categoryIcons[normalized]} fa-lg`;
    }

    iconDiv.appendChild(icon);
    return iconDiv;
  }

  _createDiv(className) {
    const div = document.createElement("div");
    div.className = className;
    return div;
  }

  getCategoryIcons() {
    return {
      travel: "fa-plane",
      shopping: "fa-shopping-cart",
      groceries: "fa-shopping-basket",
      entertainment: "fa-tv",
      fun: "fa-face-smile",
      utilities: "fa-plug",
      utility: "fa-plug",
      housing: "fa-home",
      medical: "fa-hospital",
      education: "fa-graduation-cap",
      savings: "fa-piggy-bank",
      gifts: "fa-gift",
      dining: "fa-utensils",
      investments: "fa-chart-line",
      subscriptions: "fa-file-invoice",
      charity: "fa-heart",
      pet: "fa-paw",
      wholesale: "fa-warehouse",
      car: "fa-car",
      phone: "fa-phone",
      internet: "fa-wifi",
      personal: "fa-user",
      transportation: "fa-bus",
      miscellaneous: "fa-ellipsis",
    };

  }
}
