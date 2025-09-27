// Navigation component - handles sidebar, profile dropdown, and navigation state
class NavigationManager {
  constructor() {
    this.elements = {
      barItem: document.querySelector(".bar-item"),
      sidebar: document.querySelector(".sidebar"),
      xmark: document.querySelector(".xmark"),
      pageContent: document.querySelector(".page-content"),
      loader: document.querySelector(".loader"),
      toggles: document.querySelectorAll(".toggle"),
      heart: document.querySelector(".heart"),
      sidebarLinks: document.querySelectorAll(".sidebar-link"),
    };

    this.activePage = window.location.pathname;
    this.sidebarOpen = false;

    this.init();
  }

  init() {
    this.bindEvents();
    this.setActiveLink();
    this.handlePageLoad();
  }

  bindEvents() {
    const { barItem, xmark, heart, toggles } = this.elements;

    if (barItem) {
      barItem.addEventListener("click", () => this.openSidebar());
    }

    if (xmark) {
      xmark.addEventListener("click", () => this.closeSidebar());
    }

    if (heart) {
      heart.addEventListener("click", (e) => this.toggleHeart(e));
    }

    toggles.forEach((toggle) => {
      toggle.addEventListener("click", () => this.handleToggle(toggle));
    });

    // Window events
    window.addEventListener(
      "resize",
      Utils.throttle((e) => this.handleResize(e), 250)
    );
    window.addEventListener(
      "scroll",
      Utils.throttle(() => this.handleScroll(), 100)
    );
    document.addEventListener("click", (e) => this.handleOutsideClick(e));
  }

  openSidebar() {
    const { sidebar } = this.elements;
    if (sidebar) {
      sidebar.style = "transform: translateX(0px);width:220px";
      sidebar.classList.add("sidebar-active");
      this.sidebarOpen = true;
    }
  }

  closeSidebar() {
    const { sidebar } = this.elements;
    if (sidebar) {
      sidebar.style =
        "transform: translateX(-220px);width:220px;box-shadow:none;";
      sidebar.classList.remove("sidebar-active");
      this.sidebarOpen = false;
    }
  }

  toggleHeart(event) {
    const heart = event.target;
    if (heart.classList.contains("fa-regular")) {
      heart.classList.replace("fa-regular", "fa-solid");
      heart.style.color = "#ef4444";
    } else {
      heart.classList.replace("fa-solid", "fa-regular");
      heart.style.color = "#888";
    }
  }

  handleToggle(toggle) {
    toggle.classList.toggle("active");
  }

  handleResize(event) {
    if (this.sidebarOpen) {
      if (event.target.innerWidth > 768) {
        this.elements.sidebar.style = "transform: translateX(0px);width:220px";
      } else {
        this.elements.sidebar.style =
          "transform: translateX(-220px);width:220px;box-shadow:none;";
      }
    }
  }

  handleScroll() {
    if (this.sidebarOpen) {
      this.closeSidebar();
    }
  }

  handleOutsideClick(event) {
    const { sidebar } = this.elements;

    // Close sidebar when clicking outside
    if (sidebar && sidebar.classList.contains("sidebar-active")) {
      if (
        !event.target.classList.contains("bar-item") &&
        !event.target.classList.contains("sidebar") &&
        !event.target.classList.contains("brand") &&
        !event.target.classList.contains("brand-name")
      ) {
        this.closeSidebar();
      }
    }
  }

  setActiveLink() {
    const { sidebarLinks } = this.elements;
    sidebarLinks.forEach((link) => {
      link.classList.remove("active");
      if (
        link.href &&
        (link.href.includes(this.activePage) ||
          (this.activePage === "/" && link.href.includes("index")))
      ) {
        link.classList.add("active");
      }
    });
  }

  handlePageLoad() {
    const { loader, pageContent } = this.elements;

    if (loader) {
      window.addEventListener("load", () => {
        loader.style.display = "none";
        if (pageContent) {
          pageContent.style.display = "grid";
        }
        this.activePage = "index.html";
        this.setActiveLink();
      });
    }
  }
}

// Legacy function for backward compatibility
function getCSRFToken() {
  return window.apiClient ? window.apiClient.getCSRFToken() : "";
}

// Initialize navigation when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  window.navigationManager = new NavigationManager();
});
