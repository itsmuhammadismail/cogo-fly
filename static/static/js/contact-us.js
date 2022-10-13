function toggleContact(evt, section) {
	let sections = document.getElementsByClassName("section");
	for (i = 0; i < sections.length; i++) {
		sections[i].style.display = "none";
	}
	toggles = document.getElementsByClassName("toggle");
	for (i = 0; i < toggles.length; i++) {
		toggles[i].className = toggles[i].className.replace(" active", "");
	}
	document.getElementById(section).style.display = "block";
	evt.currentTarget.className += " active";
}


document.getElementById("contact-us-header").onclick = function () {
	document.getElementById('remarks').click();
	/* prevents page shift */
	return false
};
document.getElementById("testimony-header").onclick = function () {
	document.getElementById('testimony').click();
	return false
};