function toggleLogoutModal() {
	document
		.getElementsByClassName("logout-modal")[0]
		.classList.toggle("show-logout-modal");
}

function toggleHamburger() {
	document.getElementById("nav-links").classList.toggle("open-menu");
	document.getElementById("nav-hamburger").classList.toggle("open-hamburger");
}

function toggleHeaderDropdown(dropdown) {
	dropdowns = document.getElementsByClassName("dropdown");
	target = document.getElementById(dropdown)
	if (target.classList.contains("show-dropdown")) {
		for (i = 0; i < dropdowns.length; i++) {
			dropdowns[i].className = dropdowns[i].className.replace(" show-dropdown", "")
		}
	}
	else {
		for (i = 0; i < dropdowns.length; i++) {
			dropdowns[i].className = dropdowns[i].className.replace(" show-dropdown", "")
		}		
		target.className += " show-dropdown"
	}
}
/*
function toggleNotificationFeed(evt, feed) {
	notificationFeeds = document.getElementsByClassName("notification-feed");
	for (i = 0; i < notificationFeeds.length; i++){
		notificationFeeds[i].style.display = "none"
	}
	notificationToggles = document.getElementsByClassName("notification-toggle")
	for (i = 0; i < notificationToggles.length; i++){
		notificationToggles[i].className = notificationToggles[i].className.replace(" active-toggle", "")
	}
	document.getElementById(feed).style.display = "flex";
	evt.currentTarget.className += " active-toggle"

}*/