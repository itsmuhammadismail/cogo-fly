function closeProgressBar() {
    document.getElementById("progress-bar").style.display = "none"
}

function expandMissingInfo() {
    document.getElementById("show-more").classList.toggle("hide");
    document.getElementById("show-less").classList.toggle("show");

    document.getElementById("missing-info").classList.toggle("show")
    document.getElementById("expand-button").classList.toggle("expanded")
}

function closeWelcomePopup() {
    document.getElementsByClassName('welcome')[0].style.display = "none"
}