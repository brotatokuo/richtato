// Simplified Sidebar Toggle Functionality

document.addEventListener('DOMContentLoaded', function() {
    initSidebar();
});

function initSidebar() {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebar-toggle');

    if (!sidebar || !toggleBtn) {
        console.log('Sidebar elements not found');
        return;
    }

    // Sidebar defaults to collapsed (icon-only) state
    // Load saved sidebar state - default to collapsed
    const isExpanded = localStorage.getItem('sidebarExpanded') === 'true';
    if (isExpanded) {
        expandSidebar();
    }

    // Toggle functionality
    toggleBtn.addEventListener('click', function() {
        if (sidebar.classList.contains('expanded')) {
            collapseSidebar();
        } else {
            expandSidebar();
        }
    });

    // Close sidebar when clicking outside (for overlay behavior)
    document.addEventListener('click', function(e) {
        if (!sidebar.contains(e.target) && sidebar.classList.contains('expanded')) {
            collapseSidebar();
        }
    });

    // Handle active link highlighting
    highlightActiveLink();
}

function collapseSidebar() {
    const sidebar = document.getElementById('sidebar');

    sidebar.classList.remove('expanded');

    // Save state
    localStorage.setItem('sidebarExpanded', 'false');

    // Update toggle button tooltip
    const toggleBtn = document.getElementById('sidebar-toggle');
    toggleBtn.title = 'Expand Sidebar';
}

function expandSidebar() {
    const sidebar = document.getElementById('sidebar');

    sidebar.classList.add('expanded');

    // Save state
    localStorage.setItem('sidebarExpanded', 'true');

    // Update toggle button tooltip
    const toggleBtn = document.getElementById('sidebar-toggle');
    toggleBtn.title = 'Collapse Sidebar';
}

function highlightActiveLink() {
    const currentPath = window.location.pathname;
    const sidebarLinks = document.querySelectorAll('.sidebar-link');

    sidebarLinks.forEach(link => {
        link.classList.remove('active');

        // Check if link href matches current path
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + B to toggle sidebar
    if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
        e.preventDefault();
        const toggleBtn = document.getElementById('sidebar-toggle');
        if (toggleBtn) {
            toggleBtn.click();
        }
    }

    // Escape key to collapse sidebar
    if (e.key === 'Escape') {
        const sidebar = document.getElementById('sidebar');
        if (sidebar && sidebar.classList.contains('expanded')) {
            collapseSidebar();
        }
    }
});

// Export functions for use in other scripts
window.sidebarUtils = {
    collapse: collapseSidebar,
    expand: expandSidebar,
    toggle: function() {
        const sidebar = document.getElementById('sidebar');
        if (sidebar.classList.contains('expanded')) {
            collapseSidebar();
        } else {
            expandSidebar();
        }
    }
};
