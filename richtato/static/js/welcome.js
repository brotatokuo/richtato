document.addEventListener("DOMContentLoaded", (event) => {
  var gif = document.getElementById("growth-gif");
  if (gif) {
    setTimeout(function () {
      document.querySelector(".typewriter-text").style.borderRight = "none";
      gif.src = staticImagePath;
    }, 2000);
  }
});
