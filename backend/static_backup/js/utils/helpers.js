// Utility helper functions
const Utils = {
  // Format currency values
  formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  },

  // Format dates
  formatDate(date, options = {}) {
    const defaultOptions = {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    };
    return new Date(date).toLocaleDateString('en-US', { ...defaultOptions, ...options });
  },

  // Compute balance with formula support
  computeBalance(balance) {
    if (typeof balance === 'string' && balance.startsWith("=")) {
      try {
        // Note: Using eval is dangerous - consider a proper formula parser for production
        balance = eval(balance.slice(1));
        console.log("Evaluated formula:", balance);
      } catch (error) {
        console.error("Invalid formula:", error);
        return null;
      }
    }

    const numericBalance = parseFloat(balance);
    return isNaN(numericBalance) ? null : parseFloat(numericBalance.toFixed(2));
  },

  // Debounce function calls
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },

  // Throttle function calls
  throttle(func, limit) {
    let inThrottle;
    return function() {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  },

  // Show/hide loading states
  showLoading(element) {
    if (element) {
      element.style.opacity = '0.6';
      element.style.pointerEvents = 'none';
    }
  },

  hideLoading(element) {
    if (element) {
      element.style.opacity = '1';
      element.style.pointerEvents = 'auto';
    }
  },

  // Toggle password visibility
  togglePasswordVisibility(inputId, buttonElement) {
    const passwordInput = document.getElementById(inputId);
    if (!passwordInput) {
      console.error(`Password input with id "${inputId}" not found`);
      return;
    }

    if (passwordInput.type === "password") {
      passwordInput.type = "text";
      buttonElement.textContent = "Hide";
      buttonElement.setAttribute('aria-label', 'Hide password');
    } else {
      passwordInput.type = "password";
      buttonElement.textContent = "Show";
      buttonElement.setAttribute('aria-label', 'Show password');
    }
  },

  // Show toast notifications
  showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    // Add toast styles if not already present
    if (!document.getElementById('toast-styles')) {
      const styles = document.createElement('style');
      styles.id = 'toast-styles';
      styles.textContent = `
        .toast {
          position: fixed;
          top: 20px;
          right: 20px;
          padding: 12px 24px;
          border-radius: 6px;
          color: white;
          font-weight: 500;
          z-index: 1003;
          animation: slideIn 0.3s ease;
        }
        .toast-success { background-color: #22c55e; }
        .toast-error { background-color: #ef4444; }
        .toast-warning { background-color: #f59e0b; }
        .toast-info { background-color: #3b82f6; }
        @keyframes slideIn {
          from { transform: translateX(100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
      `;
      document.head.appendChild(styles);
    }

    document.body.appendChild(toast);

    setTimeout(() => {
      toast.style.animation = 'slideIn 0.3s ease reverse';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  },

  // Validate form fields
  validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  },

  validateRequired(value) {
    return value !== null && value !== undefined && value.toString().trim() !== '';
  },

  // Local storage helpers
  storage: {
    set(key, value) {
      try {
        localStorage.setItem(key, JSON.stringify(value));
      } catch (error) {
        console.error('Error saving to localStorage:', error);
      }
    },

    get(key, defaultValue = null) {
      try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
      } catch (error) {
        console.error('Error reading from localStorage:', error);
        return defaultValue;
      }
    },

    remove(key) {
      try {
        localStorage.removeItem(key);
      } catch (error) {
        console.error('Error removing from localStorage:', error);
      }
    }
  }
};

// Make utils globally available
window.Utils = Utils;
