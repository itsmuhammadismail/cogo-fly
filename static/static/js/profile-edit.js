function tabContentSwitch(evt, tabContent) {
	let i, tabTitles, tabContents;
	tabTitles = document.getElementsByClassName("tab-title");
	tabContents = document.getElementsByClassName("tab-content");

	for (i = 0; i < tabContents.length; i++) {
		tabContents[i].style.display = "none";
	}
	document.getElementById(tabContent).style.display = "block";

	for (i = 0; i < tabTitles.length; i++) {
		tabTitles[i].className = tabTitles[i].className.replace(" active-tab", "");
	}
	evt.currentTarget.className += " active-tab";
}

window.onload = function () {
	document.getElementById("default-tab").click()
}
