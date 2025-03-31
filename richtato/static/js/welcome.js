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

  const pageContent = document.querySelector(".page-content");
  const sidebar = document.querySelector(".sidebar");

  // Hide the sidebar by adding the "sidebar-hidden" class
  function hideSidebar() {
    sidebar.style.display = "none";
    pageContent.classList.add("sidebar-hidden");
  }

  hideSidebar();
  const hamburger = document.querySelector("#hamburger");
  hamburger.style.display = "none";

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
