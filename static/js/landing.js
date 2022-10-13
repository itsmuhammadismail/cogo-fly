const scrollUpButton = document.getElementById("scrollup");
const navBar = document.querySelector("header");
const main = document.getElementsByTagName("main")[0];

/*const langModal = document.getElementById("lang-modal");
const langOpen = document.getElementById("lang-open");
const langClose = document.getElementById("lang-close");
langOpen.onclick = function () {
	navBar.className = "solid";z
	langModal.classList.toggle("open");
	main.classList.toggle("is-blurred");
};

langClose.onclick = function () {
	navBar.className = "";
	langModal.classList.toggle("open");
	main.classList.toggle("is-blurred");
};*/

const hamburger = document.getElementById("menu-toggle");
const page = document.getElementById("page");
hamburger.onclick = function () {
	page.classList.toggle("menu-open");
	hamburger.classList.toggle("is_active");
};

const scrollToTop = function () {
	window.scrollTo({ top: 0, behavior: "smooth" });
};

window.onscroll = function () {
	const scroll = document.body.scrollTop;

	if (scroll < 100) {
		scrollUpButton.className = "";
		navBar.className = "";
	} else {
		scrollUpButton.className = "visible";
		navBar.className = "solid";
	}
};

scrollUpButton.onclick = scrollToTop;

function toggleCoTravels(evt, cont) {
	let toggles = document.getElementsByClassName("cotravels-toggle");
	for (i = 0; i < toggles.length; i++) {
		toggles[i].className = toggles[i].className.replace(" selected", "");
	}
	evt.currentTarget.className += " selected";

	let cotravelsContent = document.getElementsByClassName("cotravels-carousel");
	for (i = 0; i < cotravelsContent.length; i++) {
		cotravelsContent[i].className = cotravelsContent[i].className.replace(" show-carousel", "");
	}
	carousel = document.getElementById(cont);
	carousel.className += " show-carousel";

	/* Hack to fix bug when changing tab; slides not displaying unless setting width on them */
	carouselSlides = carousel.children[1].children
	for (i = 0; i < carouselSlides.length; i++) {
		if (window.innerWidth > 640) {
			carouselSlides[0].children[i].style.width = carousel.offsetWidth / 3 - 20
			carouselSlides[0].children[i].style.marginRight = "20px"
		}
		else if (window.innerWidth <= 640 && window.innerWidth > 400) {
			carouselSlides[0].children[i].style.width = carousel.offsetWidth / 2 - 22
			carouselSlides[0].children[i].style.marginRight = "20px"
		}
		else {
			carouselSlides[0].children[i].style.width = carousel.offsetWidth
		}
	}
}

/* COOKIE POLICY */
window.cookieconsent.initialise({
	container: document.getElementById("cookieconsent"),
	palette: {
		popup: { background: "#1aa3ff" },
		button: { background: "#e0e0e0" },
	},
	revokable: true,
	onStatusChange: function (status) {
		console.log(this.hasConsented() ?
			'enable cookies' : 'disable cookies');
	},
	"position": "bottom",
	"theme": "classic",
	"domain": "https://cogofly.com/",
	"secure": true,
	"content": {
		"header": 'Cookies used on the website!',
		"message": 'This site uses cookies in order to provide, protect and optimise Cogofly\'s\ services. By continuing, you agree to our policy covering all of the above.',
		"dismiss": 'Do not show this messages again',
		"allow": 'Allow cookies',
		"deny": 'Decline',
		"link": 'Find out more here',
		"href": 'https://cogofly.com/privacy-policy',
		"close": '&#x274c;',
		"policy": 'Cookie Policy',
		"target": '_blank',
	}
});
