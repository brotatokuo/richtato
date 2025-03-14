// let getBarItem = document.querySelector(".bar-item");
let getSideBar = document.querySelector(".sidebar");
let getXmark = document.querySelector(".xmark");
let getPageContent = document.querySelector(".page-content");
let getLoader = document.querySelector(".loader");
let getToggle = document.querySelectorAll(".toggle");
let getHeart = document.querySelector(".heart");
let getSidebarLink = document.querySelectorAll(".sidebar-link");
let activePage = window.location.pathname;
let getSideBarStatus = false;

// getBarItem.onclick = () => {
//   getSideBar.style = "transform: translateX(0px);width:220px";
//   getSideBar.classList.add("sidebar-active");
// };
getXmark.onclick = () => {
  getSideBar.style =
    "transform: translateX(-220px);width:220px;box-shadow:none;";
  getSideBarStatus = true;
  if (getSideBar.classList.contains("sidebar-active")) {
    getSideBar.classList.remove("sidebar-active");
  }
};
window.addEventListener("resize", (e) => {
  if (getSideBarStatus === true) {
    if (e.target.innerWidth > 768) {
      getSideBar.style = "transform: translateX(0px);width:220px";
    } else {
      getSideBar.style =
        "transform: translateX(-220px);width:220px;box-shadow:none;";
    }
  }
});
if (getLoader) {
  window.addEventListener("load", () => {
    getLoader.style.display = "none";
    getPageContent.style.display = "grid";
    activePage = "index.html";
    getSidebarLink.forEach((item) => {
      if (item.href.includes(`${activePage}`)) {
        item.classList.add("active");
      } else item.classList.remove("active");
    });
  });
}
document.onclick = (e) => {
  if (getSideBar.classList.contains("sidebar-active")) {
    if (
      !e.target.classList.contains("bar-item") &&
      !e.target.classList.contains("sidebar") &&
      !e.target.classList.contains("brand") &&
      !e.target.classList.contains("brand-name")
    ) {
      getSideBar.style =
        "transform: translateX(-220px);width:220px;box-shadow:none;";
      getSideBar.classList.remove("sidebar-active");
      getSideBarStatus = true;
    }
  }
};
window.addEventListener("scroll", () => {
  if (getSideBar.classList.contains("sidebar-active")) {
    getSideBar.style =
      "transform: translateX(-220px);width:220px;box-shadow:none;";
    getSideBar.classList.remove("sidebar-active");
  }
});
if (getHeart) {
  getHeart.addEventListener("click", (e) => {
    if (e.target.classList.contains("fa-regular")) {
      getHeart.classList.replace("fa-regular", "fa-solid");
      getHeart.style.color = "red";
    } else {
      getHeart.classList.replace("fa-solid", "fa-regular");
      getHeart.style.color = "#888";
    }
  });
}
getToggle.forEach((item) => {
  item.addEventListener("click", () => {
    if (item.classList.contains("left")) {
      item.classList.remove("left");
    } else {
      item.classList.add("left");
    }
  });
});

getSidebarLink.forEach((item) => {
  if (item.href.includes(`${activePage}`)) {
    item.classList.add("active");
  }
});

document.addEventListener('DOMContentLoaded', () => {
  const currencyInputs = document.getElementsByClassName('currency-input');
  console.log('Currency inputs:', currencyInputs);
  Array.from(currencyInputs).forEach(currencyInput => {

    currencyInput.addEventListener('input', () => {
      const value = currencyInput.value;
      const validCharacters = /^[0-9+\-*/().=]*$/;
      if (!validCharacters.test(value)) {
        currencyInput.value = value.replace(/[^0-9+\-*/().=]/g, '');
      }
    });

    currencyInput.addEventListener('blur', () => {
      let balance = currencyInput.value;

      if (balance) {
        let newBalance = computeBalance(balance);

        if (newBalance) {
          currencyInput.value = newBalance;
          console.log('New balance:', newBalance);
        }
      }
    });
  });
});

function computeBalance(balance) {
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
  else {
    // Convert to a float for regular numbers or evaluated formulas
    balance = eval(balance);;
  }
  // Convert to a float for regular numbers or evaluated formulas
  balance = parseFloat(balance).toFixed(2);
  return balance;
} 