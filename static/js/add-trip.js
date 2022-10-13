function destination() {
	document
		.getElementsByClassName("past-future")[0]
		.classList.toggle("hide-past-future");
	document
		.getElementsByClassName("destination")[0]
		.classList.toggle("show-destination");
}

function commentPhotos() {
	document
		.getElementsByClassName("destination")[0]
		.classList.toggle("show-destination");
	document
		.getElementsByClassName("comment-photos")[0]
		.classList.toggle("show-comment-photos");
}

function result() {
	document
		.getElementsByClassName("comment-photos")[0]
		.classList.toggle("show-comment-photos");
	document.getElementsByClassName("result")[0].classList.toggle("show-result");
}
