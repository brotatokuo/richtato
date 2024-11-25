document.addEventListener('DOMContentLoaded', (event) => {
    // Swap GIF with a static image after 2 seconds
    var gif = document.getElementById('growth-gif');
    if (gif) {
        setTimeout(function () {
            document.querySelector('.typewriter-text').style.borderRight = 'none';
            gif.src = staticImagePath; // Use the variable defined in the HTML
        }, 2000);
    }

    const currencyInput = document.getElementById('balance-input');
    if (currencyInput) {
        currencyInput.addEventListener('blur', function (e) {
            let value = parseFloat(e.target.value);
            // Ensure the value is a valid number before formatting
            if (!isNaN(value)) {
                e.target.value = value.toFixed(2); // Format to two decimal places
            } else {
                console.log("Invalid input:", e.target.value); // Handle invalid input
            }
        });
    }
});

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
