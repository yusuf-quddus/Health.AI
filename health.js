var collapsible = document.getElementsByClassName("collapsible");
var i;

for (i = 0; i < collapsible.length; i++) {
  collapsible[i].addEventListener("click", function() {
    this.classList.toggle("active");
    var container = this.nextElementSibling;
    if (container.style.display === "block") 
      container.style.display = "none";
    else 
      container.style.display = "block";
  });
}

