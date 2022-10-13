function openPopup(cont){
    document.getElementById(cont).classList.toggle("show-popup")
}

window.onclick = function (event) {
    const deletePopup = document.getElementById("delete-popup");
    const deactivatePopup = document.getElementById("deactivate-popup");
    if (event.target == deletePopup) {
        deletePopup.classList.toggle("show-popup")
    }
    if (event.target == deactivatePopup) {
        deactivatePopup.classList.toggle("show-popup");
    }
  }