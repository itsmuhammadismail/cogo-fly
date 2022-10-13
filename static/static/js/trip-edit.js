function showSaveMessage() {
	document.getElementById("save-message").classList.toggle("show");
	document.getElementById("modify-message").className = "hide";
	document.getElementById("delete-message").className = "hide";
}

/*function showModifyMessage() {
	document.getElementById("save-message").className = "hide";
	document.getElementById("modify-message").classList.toggle("show");
	document.getElementById("delete-message").className = "hide";
}*/

function showDeleteMessage() {
	document.getElementById("save-message").className = "hide";
	document.getElementById("modify-message").className = "hide";
	document.getElementById("delete-message").classList.toggle("show");
}

function showDeleteForm() {
	document.getElementById("delete-form").classList.toggle("show-delete-form")
}