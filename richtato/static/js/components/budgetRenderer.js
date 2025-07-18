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
    const wrapper = this._createDiv("budget-category-item");

    const iconDiv = this._createIconElement(category.name);
    const infoDiv = this._createInfoElement(category, index);

    wrapper.appendChild(iconDiv);
    wrapper.appendChild(infoDiv);

    return wrapper;
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

  _createInfoElement(category, index) {
    const infoDiv = this._createDiv("budget-category-info");

    const ul = document.createElement("ul");
    ["name", "budget", "message"].forEach((key) => {
      const li = document.createElement("li");
      li.textContent = category[key];
      ul.appendChild(li);
    });

    const percentageBar = this._createPercentageBar(
      index + 1,
      category.percent
    );

    infoDiv.appendChild(ul);
    infoDiv.appendChild(percentageBar);

    return infoDiv;
  }

  _createPercentageBar(id, percent) {
    const barWrapper = this._createDiv("budget-progress-bar");
    const bar = this._createDiv("budget-progress-fill");
    bar.id = `percentage-${id}`;
    bar.style.width = Math.abs(percent) + "%";

    // Dynamic color: interpolate between green (0%) and red (100%)
    // Use HSL: green (88, 63%, 48%) to red (0, 100%, 50%)
    // Or use CSS variables for --green-color and --red-color
    // We'll use a simple linear interpolation for hue (88 to 0)
    let color;
    if (percent <= 0) {
      color = "var(--green-color)";
    } else if (percent >= 100) {
      color = "var(--red-color)";
    } else {
      // Interpolate hue from green (88) to red (0)
      const greenHSL = { h: 88, s: 63, l: 48 }; // #98cc2c
      const redHSL = { h: 0, s: 100, l: 50 }; // red
      const hue = greenHSL.h + (redHSL.h - greenHSL.h) * (percent / 100);
      const sat = greenHSL.s + (redHSL.s - greenHSL.s) * (percent / 100);
      const light = greenHSL.l + (redHSL.l - greenHSL.l) * (percent / 100);
      color = `hsl(${hue}, ${sat}%, ${light}%)`;
    }
    bar.style.backgroundColor = color;

    barWrapper.appendChild(bar);
    return barWrapper;
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
      utilities: "fa-plug",
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
      miscellaneous: "fa-ellipsis",
    };
  }
}
