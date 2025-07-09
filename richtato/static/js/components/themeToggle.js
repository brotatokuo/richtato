// Theme Toggle Functionality
class ThemeManager {
  constructor() {
    this.themeToggleBtn = document.getElementById("theme-toggle-btn");
    this.themeIcon = document.getElementById("theme-icon");
    this.currentTheme = localStorage.getItem("theme") || "dark-mode";

    this.init();
  }

  init() {
    // Set initial theme
    this.setTheme(this.currentTheme);

    // Add event listener
    if (this.themeToggleBtn) {
      this.themeToggleBtn.addEventListener("click", () => this.toggleTheme());
    }
  }

  setTheme(theme) {
    // Remove existing theme classes
    document.body.classList.remove("light-mode", "dark-mode");

    // Add new theme class
    document.body.classList.add(theme);

    // Update icon
    this.updateIcon(theme);

    // Save to localStorage
    localStorage.setItem("theme", theme);

    // Update current theme
    this.currentTheme = theme;

    // Reinitialize charts to update their colors
    this.updateChartColors();
  }

  toggleTheme() {
    const newTheme =
      this.currentTheme === "dark-mode" ? "light-mode" : "dark-mode";
    this.setTheme(newTheme);
  }

    updateIcon(theme) {
    if (this.themeIcon) {
      const themeText = this.themeToggleBtn.querySelector("span");

      if (theme === "light-mode") {
        this.themeIcon.className = "fa-solid fa-sun";
        this.themeToggleBtn.title = "Switch to Dark Mode";
        if (themeText) {
          themeText.textContent = "Light mode";
        }
      } else {
        this.themeIcon.className = "fa-solid fa-moon";
        this.themeToggleBtn.title = "Switch to Light Mode";
        if (themeText) {
          themeText.textContent = "Dark mode";
        }
      }
    }
  }

  updateChartColors() {
    // Get current text color
    const textColor = getComputedStyle(document.documentElement).getPropertyValue('--text-color');

    // Update all Chart.js instances
    if (window.Chart && window.Chart.instances) {
      Object.values(window.Chart.instances).forEach(chart => {
        if (chart.options && chart.options.plugins && chart.options.plugins.legend) {
          chart.options.plugins.legend.labels.color = textColor;
        }
        if (chart.options && chart.options.scales) {
          if (chart.options.scales.x && chart.options.scales.x.ticks) {
            chart.options.scales.x.ticks.color = textColor;
          }
          if (chart.options.scales.y && chart.options.scales.y.ticks) {
            chart.options.scales.y.ticks.color = textColor;
          }
        }
        chart.update();
      });
    }
  }
}

// Initialize theme manager when DOM is loaded
document.addEventListener("DOMContentLoaded", function () {
  new ThemeManager();
});

// Export for use in other scripts
window.ThemeManager = ThemeManager;
