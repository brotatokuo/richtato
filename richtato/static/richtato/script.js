document.addEventListener('DOMContentLoaded', (event) => {
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

    const balanceInput = document.getElementById('balance-input');

    balanceInput.addEventListener('blur', () => {
        let balance = balanceInput.value;
        
        if (balance){
            newBalance = computeBalance(balance);

            if (newBalance) {
                balanceInput.value = newBalance;
                console.log('New balance:', newBalance);
            }
        }
    });
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

function getUserID() {
    return fetch('/get-user-id')
        .then(response => response.json())
        .then(data => data.userID);
}

function computeBalance(balance){
    // Check if it's a formula starting with '='
    if (balance.startsWith('=')) {
        try {
            // Evaluate the formula (strip the leading '=')
            balance = eval(balance.slice(1));  // Caution: Use math.js for safety in production
            console.log('Evaluated formula:', balance);
        } catch (error) {
            console.error('Invalid formula:', error);
            return;  // Stop further processing if the formula is invalid
        }
    }
    

    // Convert to a float for regular numbers or evaluated formulas
    balance = parseFloat(balance).toFixed(2);
    return balance;
}