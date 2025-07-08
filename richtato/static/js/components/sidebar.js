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

  // Desktop behavior - pure hover-based expansion
  if (!isMobile()) {
    // No persistent expanded state needed for hover-based behavior
    // The sidebar will expand on hover and collapse when mouse leaves
    // CSS handles the hover expansion automatically
  }

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
