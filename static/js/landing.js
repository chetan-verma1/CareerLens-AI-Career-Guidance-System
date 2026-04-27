window.addEventListener("load", function () {
  const title = document.getElementById("landingTitle");
  if (title) {
    setTimeout(() => {
      title.classList.add("done");
    }, 2400);
  }
});