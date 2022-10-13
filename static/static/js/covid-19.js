var coll = document.getElementsByClassName("collapsible-toggle");
var i;
/*TODO*/
function toggleCollapsible(evt) {
  evt.currentTarget.classList.toggle("active-toggle");
  var content = evt.currentTarget.parentElement.nextElementSibling;
  if (content.style.maxHeight) {
    content.style.maxHeight = null;
  } else {
    content.style.maxHeight = content.scrollHeight + "px";
  }
};
