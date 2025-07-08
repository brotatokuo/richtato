document.addEventListener("DOMContentLoaded", (event) => {
  const userAuthenticated = "{{ user.is_authenticated|yesno:'true,false' }}";
  console.log("user auth: ", userAuthenticated);

  var gif = document.getElementById("growth-gif");
  if (gif) {
    setTimeout(function () {
      document.querySelector(".typewriter-text").style.borderRight = "none";
      gif.src = staticImagePath;
    }, 2000);
  }

  const hamburger = document.querySelector("#hamburger");
  function updateHamburgerDisplay() {
    if (window.innerWidth <= 767) {
      hamburger.style.display = "inline-block";
    } else {
      hamburger.style.display = "none";
    }
  }
  updateHamburgerDisplay();
  window.addEventListener("resize", updateHamburgerDisplay);

  const loginButton = document.querySelector("#login-button");
  if (loginButton) {
    loginButton.addEventListener("keypress", (event) => {
      if (event.key === "Enter") {
        loginButton.click();
      }
    });
  }

  const registerButton = document.querySelector("#register-button");
  if (registerButton) {
    registerButton.addEventListener("keypress", (event) => {
      if (event.key === "Enter") {
        registerButton.click();
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
  const cookieValue = document.cookie
    .match("(^|;)\\s*csrftoken\\s*=\\s*([^;]+)")
    ?.pop();
  return cookieValue || "";
}

function getUserID() {
  return fetch("/get-user-id")
    .then((response) => response.json())
    .then((data) => data.userID);
}

function computeBalance(balance) {
  if (balance.startsWith("=")) {
    try {
      balance = eval(balance.slice(1));
      console.log("Evaluated formula:", balance);
    } catch (error) {
      console.error("Invalid formula:", error);
      return;
    }
  }

  balance = parseFloat(balance).toFixed(2);
  return balance;
}
