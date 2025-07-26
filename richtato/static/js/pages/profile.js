// Profile Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializeProfile();
});

function initializeProfile() {
    // Initialize preference change listeners
    initializePreferences();

    // Add keyboard event listeners
    document.addEventListener('keydown', handleKeyboardEvents);

    // Initialize tooltips and interactive elements
    initializeInteractiveElements();
}

// Username editing functionality
function editField(fieldName) {
    const display = document.getElementById(`${fieldName}-display`);
    const editForm = document.getElementById(`${fieldName}-edit`);
    const input = document.getElementById(`${fieldName}-input`);

    display.style.display = 'none';
    editForm.style.display = 'block';
    input.focus();
    input.select();
}

function saveField(fieldName) {
    const input = document.getElementById(`${fieldName}-input`);
    const newValue = input.value.trim();

    if (!newValue) {
        showNotification('Username cannot be empty', 'error');
        return;
    }

    if (newValue === document.getElementById(`${fieldName}-display`).textContent) {
        cancelEdit(fieldName);
        return;
    }

    // Show loading state
    const saveBtn = document.querySelector(`#${fieldName}-edit .save-btn`);
    const originalText = saveBtn.textContent;
    saveBtn.textContent = 'Saving...';
    saveBtn.disabled = true;

    // Make API call to update username
    fetch('/api/update-username/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({
            username: newValue
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update display
            document.getElementById(`${fieldName}-display`).textContent = newValue;
            document.querySelector('.profile-header-info h2').textContent = newValue;

            // Hide edit form
            cancelEdit(fieldName);

            showNotification('Username updated successfully', 'success');
        } else {
            showNotification(data.error || 'Failed to update username', 'error');
        }
    })
    .catch(error => {
        console.error('Error updating username:', error);
        showNotification('Network error. Please try again.', 'error');
    })
    .finally(() => {
        saveBtn.textContent = originalText;
        saveBtn.disabled = false;
    });
}

function cancelEdit(fieldName) {
    const display = document.getElementById(`${fieldName}-display`);
    const editForm = document.getElementById(`${fieldName}-edit`);
    const input = document.getElementById(`${fieldName}-input`);

    // Reset input to original value
    input.value = display.textContent;

    display.style.display = 'inline';
    editForm.style.display = 'none';
}

// Password change functionality
function changePassword() {
    document.getElementById('password-modal').style.display = 'flex';
    document.getElementById('current-password').focus();
}

function closePasswordModal() {
    document.getElementById('password-modal').style.display = 'none';

    // Clear form
    document.getElementById('password-form').reset();

    // Clear any error states
    clearFormErrors();
}

function submitPasswordChange() {
    const currentPassword = document.getElementById('current-password').value;
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;

    // Clear previous errors
    clearFormErrors();

    // Validate form
    if (!currentPassword) {
        showFieldError('current-password', 'Current password is required');
        return;
    }

    if (!newPassword) {
        showFieldError('new-password', 'New password is required');
        return;
    }

    if (newPassword.length < 8) {
        showFieldError('new-password', 'Password must be at least 8 characters long');
        return;
    }

    if (newPassword !== confirmPassword) {
        showFieldError('confirm-password', 'Passwords do not match');
        return;
    }

    if (currentPassword === newPassword) {
        showFieldError('new-password', 'New password must be different from current password');
        return;
    }

    // Show loading state
    const submitBtn = document.querySelector('.modal-footer .save-btn');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Changing Password...';
    submitBtn.disabled = true;

    // Make API call
    fetch('/api/change-password/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({
            current_password: currentPassword,
            new_password: newPassword
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            closePasswordModal();
            showNotification('Password changed successfully', 'success');
        } else {
            if (data.field) {
                showFieldError(data.field, data.error);
            } else {
                showNotification(data.error || 'Failed to change password', 'error');
            }
        }
    })
    .catch(error => {
        console.error('Error changing password:', error);
        showNotification('Network error. Please try again.', 'error');
    })
    .finally(() => {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    });
}

// Preferences functionality
function initializePreferences() {
    const emailNotifications = document.getElementById('email-notifications');
    const dataInsights = document.getElementById('data-insights');
    const currency = document.getElementById('currency');

    if (emailNotifications) {
        emailNotifications.addEventListener('change', function() {
            updatePreference('email_notifications', this.checked);
        });
    }

    if (dataInsights) {
        dataInsights.addEventListener('change', function() {
            updatePreference('data_insights', this.checked);
        });
    }

    if (currency) {
        currency.addEventListener('change', function() {
            updatePreference('preferred_currency', this.value);
        });
    }
}

function updatePreference(key, value) {
    fetch('/api/update-preferences/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({
            [key]: value
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Preference updated', 'success');
        } else {
            showNotification('Failed to update preference', 'error');
        }
    })
    .catch(error => {
        console.error('Error updating preference:', error);
        showNotification('Network error. Please try again.', 'error');
    });
}

// Account deletion functionality
function confirmDeleteAccount() {
    const confirmed = confirm(
        'Are you sure you want to delete your account?\n\n' +
        'This action will permanently delete:\n' +
        '• All your financial data\n' +
        '• All connected accounts\n' +
        '• All transaction history\n' +
        '• All budget information\n\n' +
        'This action cannot be undone.\n\n' +
        'Type "DELETE" to confirm:'
    );

    if (!confirmed) return;

    const confirmation = prompt('Please type "DELETE" to confirm account deletion:');

    if (confirmation !== 'DELETE') {
        showNotification('Account deletion cancelled', 'info');
        return;
    }

    // Final confirmation
    const finalConfirm = confirm('This is your final warning. Are you absolutely sure you want to delete your account?');

    if (!finalConfirm) {
        showNotification('Account deletion cancelled', 'info');
        return;
    }

    deleteAccount();
}

function deleteAccount() {
    const deleteBtn = document.querySelector('.danger-btn');
    const originalText = deleteBtn.textContent;
    deleteBtn.textContent = 'Deleting Account...';
    deleteBtn.disabled = true;

    fetch('/api/delete-account/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Account deleted successfully. Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = '/';
            }, 2000);
        } else {
            showNotification(data.error || 'Failed to delete account', 'error');
        }
    })
    .catch(error => {
        console.error('Error deleting account:', error);
        showNotification('Network error. Please try again.', 'error');
    })
    .finally(() => {
        deleteBtn.textContent = originalText;
        deleteBtn.disabled = false;
    });
}

// Interactive elements
function initializeInteractiveElements() {
    // Add hover effects to stat cards
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    // Add click effect to profile cards
    const profileCards = document.querySelectorAll('.profile-card');
    profileCards.forEach(card => {
        card.addEventListener('click', function(e) {
            if (!e.target.closest('.edit-btn') &&
                !e.target.closest('.edit-form') &&
                !e.target.closest('.preference-label') &&
                !e.target.closest('.preference-select') &&
                !e.target.closest('.danger-btn')) {

                this.style.transform = 'scale(0.98)';
                setTimeout(() => {
                    this.style.transform = 'scale(1)';
                }, 100);
            }
        });
    });
}

// Keyboard event handling
function handleKeyboardEvents(e) {
    // Escape key to close modals
    if (e.key === 'Escape') {
        const passwordModal = document.getElementById('password-modal');
        if (passwordModal.style.display === 'flex') {
            closePasswordModal();
        }

        // Cancel any active edits
        const activeEdits = document.querySelectorAll('.edit-form[style*="block"]');
        activeEdits.forEach(edit => {
            const fieldName = edit.id.replace('-edit', '');
            cancelEdit(fieldName);
        });
    }

    // Enter key to save edits
    if (e.key === 'Enter') {
        const activeInput = document.activeElement;
        if (activeInput && activeInput.id === 'username-input') {
            saveField('username');
        }
    }
}

// Utility functions
function getCsrfToken() {
    const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
    if (tokenElement) {
        return tokenElement.value;
    }

    // Try to get from cookies
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }

    return '';
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fa-solid ${getNotificationIcon(type)}"></i>
            <span>${message}</span>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                <i class="fa-solid fa-times"></i>
            </button>
        </div>
    `;

    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${getNotificationColor(type)};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        border: 1px solid ${getNotificationBorderColor(type)};
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        z-index: 10001;
        min-width: 300px;
        max-width: 500px;
        animation: slideInRight 0.3s ease-out;
    `;

    // Add to page
    document.body.appendChild(notification);

    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }
    }, 5000);
}

function getNotificationIcon(type) {
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    return icons[type] || icons.info;
}

function getNotificationColor(type) {
    const colors = {
        success: '#4CAF50',
        error: '#f44336',
        warning: '#ff9800',
        info: '#2196F3'
    };
    return colors[type] || colors.info;
}

function getNotificationBorderColor(type) {
    const colors = {
        success: '#45a049',
        error: '#d32f2f',
        warning: '#f57c00',
        info: '#1976d2'
    };
    return colors[type] || colors.info;
}

function showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    if (!field) return;

    // Clear existing error
    const existingError = field.parentElement.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }

    // Add error styling
    field.style.borderColor = '#f44336';
    field.style.boxShadow = '0 0 0 2px rgba(244, 67, 54, 0.2)';

    // Add error message
    const errorElement = document.createElement('div');
    errorElement.className = 'field-error';
    errorElement.textContent = message;
    errorElement.style.cssText = `
        color: #f44336;
        font-size: 12px;
        margin-top: 5px;
        display: block;
    `;

    field.parentElement.appendChild(errorElement);

    // Focus the field
    field.focus();
}

function clearFormErrors() {
    const errors = document.querySelectorAll('.field-error');
    errors.forEach(error => error.remove());

    const fields = document.querySelectorAll('.form-group input');
    fields.forEach(field => {
        field.style.borderColor = '';
        field.style.boxShadow = '';
    });
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }

    .notification-content {
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .notification-close {
        background: none;
        border: none;
        color: white;
        cursor: pointer;
        padding: 2px;
        margin-left: auto;
        opacity: 0.8;
        transition: opacity 0.2s ease;
    }

    .notification-close:hover {
        opacity: 1;
    }
`;
document.head.appendChild(style);
