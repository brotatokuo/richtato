// Hover-based Sidebar Expansion

document.addEventListener("DOMContentLoaded", function () {
  initSidebar();
});

function initSidebar() {
  const sidebar = document.getElementById("sidebar");
  const hamburgerBtn = document.getElementById("hamburger");

  if (!sidebar) {
    console.log("Sidebar element not found");
    return;
  }

  // Check if mobile
  const isMobile = () => window.innerWidth <= 767;

  // Remove hover-based expansion on mobile
  function disableSidebarHoverOnMobile() {
    if (isMobile()) {
      sidebar.classList.remove("expanded");
      sidebar.classList.remove("hover-enabled");
      // Remove any hover event listeners if present
      sidebar.onmouseenter = null;
      sidebar.onmouseleave = null;
    } else {
      // Enable hover-based expansion on desktop
      sidebar.classList.add("hover-enabled");
      sidebar.onmouseenter = function () {
        sidebar.classList.add("expanded");
      };
      sidebar.onmouseleave = function () {
        sidebar.classList.remove("expanded");
      };
    }
  }

  // Initial setup
  disableSidebarHoverOnMobile();

  // Mobile hamburger menu behavior
  if (hamburgerBtn) {
    hamburgerBtn.addEventListener("click", function () {
      if (isMobile()) {
        // On mobile, always show expanded sidebar when hamburger is clicked
        if (sidebar.classList.contains("open")) {
          sidebar.classList.remove("open");
        } else {
          sidebar.classList.add("open");
        }
      }
    });
  }

  // Close mobile sidebar when clicking outside
  document.addEventListener("click", function (e) {
    if (
      isMobile() &&
      !sidebar.contains(e.target) &&
      !hamburgerBtn.contains(e.target)
    ) {
      sidebar.classList.remove("open");
    }
  });

  // Handle window resize
  window.addEventListener("resize", function () {
    disableSidebarHoverOnMobile();
    if (isMobile()) {
      // On mobile, remove desktop states
      sidebar.classList.remove("expanded");
    } else {
      // On desktop, remove mobile states
      sidebar.classList.remove("open");
    }
  });

  // Handle active link highlighting
  highlightActiveLink();
}

function highlightActiveLink() {
  const currentPath = window.location.pathname;
  const sidebarLinks = document.querySelectorAll(".sidebar-link");

  sidebarLinks.forEach((link) => {
    link.classList.remove("active");

    // Check if link href matches current path
    if (link.getAttribute("href") === currentPath) {
      link.classList.add("active");
    }
  });
}

// Export functions for use in other scripts (simplified for hover-based behavior)
window.sidebarUtils = {
  // These functions are kept for compatibility but don't do anything in hover mode
  collapse: function () {
    // No-op for hover-based behavior
  },
  expand: function () {
    // No-op for hover-based behavior
  },
  toggle: function () {
    // No-op for hover-based behavior
  },
};
