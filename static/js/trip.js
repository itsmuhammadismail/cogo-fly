function pictureFull() {
	const tripTopPic = document.getElementById("trip-top-pic");
	const tripComment = document.getElementsByClassName("trip-comment")[0];
	const upArrow = document.getElementsByClassName("up-arrow")[0];
	const downArrow = document.getElementsByClassName("down-arrow")[0];

	tripTopPic.classList.toggle("full-height");
	tripComment.classList.toggle("show");
	upArrow.classList.toggle("show");
	downArrow.classList.toggle("hide");
}
