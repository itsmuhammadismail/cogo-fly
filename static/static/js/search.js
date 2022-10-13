function tabContentSwitch(evt, tabContent) {
	let i, tabTitles, tabContents;
	tabTitles = document.getElementsByClassName("tab-title");
	tabContents = document.getElementsByClassName("tab-content");

	for (i = 0; i < tabContents.length; i++) {
		tabContents[i].style.position = 'absolute';
		tabContents[i].style.visibility = 'hidden';
	}
	document.getElementById(tabContent).style.position = 'unset';
	document.getElementById(tabContent).style.visibility = 'visible';

	for (i = 0; i < tabTitles.length; i++) {
		tabTitles[i].className = tabTitles[i].className.replace(" active-tab", "");
	}
	evt.currentTarget.className += " active-tab";
}

window.onload = function () {
	document.getElementById("default-tab").click();
	if (window.innerWidth < 600) {
		document.getElementsByClassName("search-content")[0].scrollIntoView();
	}
}

function toggleLucky() {
	document.getElementsByClassName("lucky")[0].classList.toggle("show");
}
/*window.onload = function () {
	if (window.location.href.indexOf('?') > -1) {
		document.getElementsByClassName("nonfield")[0].style.display = "block";
	}
}
*/