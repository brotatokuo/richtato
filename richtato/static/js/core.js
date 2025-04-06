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

function computeBalance(balance) {
  if (balance.startsWith('=')) {
    try {
      balance = eval(balance.slice(1));
      console.log('Evaluated formula:', balance);
    } catch (error) {
      console.error('Invalid formula:', error);
      return;
    }
  }

  balance = parseFloat(balance).toFixed(2);
  return balance;
}
