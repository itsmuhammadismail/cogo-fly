function openStep(evt, step, cta) {
	let i, stepsContent, tabs;
	stepsContent = document.getElementsByClassName("step-content");
	for (i = 0; i < stepsContent.length; i++) {
		stepsContent[i].style.display = "none";
	}
	tabs = document.getElementsByClassName("tab");
	for (i = 0; i < tabs.length; i++) {
		tabs[i].className = tabs[i].className.replace(" active-tab", "");
	}

	ctas = document.getElementsByClassName("cta");
	if (document.getElementById(cta).style.display == "flex") {
		for (i = 0; i < ctas.length; i++) {
			ctas[i].style.display = "none";
		}
	} else {
		for (i = 0; i < ctas.length; i++) {
			ctas[i].style.display = "none";
		}
		document.getElementById(cta).style.display = "flex";
	}
	evt.currentTarget.className += " active-tab";
	document.getElementById(step).style.display = "flex";
}

function switchInformation(evt, information, subInformation) {
	let i, infos, subInfos, titles;
	infos = document.getElementsByClassName("information");
	for (i = 0; i < infos.length; i++) {
		infos[i].style.display = "none";
	}
	subInfos = document.getElementsByClassName("sub-information");
	for (i = 0; i < subInfos.length; i++) {
		subInfos[i].style.display = "none";
	}
	titles = document.getElementsByClassName("title");
	for (i = 0; i < titles.length; i++) {
		titles[i].className = titles[i].className.replace(" active-title", "");
	}
	document.getElementById(information).style.display = "flex";
	document.getElementById(subInformation).style.display = "flex";
	evt.currentTarget.className += " active-title";
}

function toggleSubInfo(subInfo) {
	document.getElementById(subInfo).classList.toggle("show-sub-info")
}

function toggleTip(evt,tip) {
	evt.currentTarget.classList.toggle('active-button');
	document.getElementById(tip).classList.toggle('show-tip')
}

function toggleTipContent(tipContent) {
	document.getElementById(tipContent).classList.toggle("show-tip-content")
}

function toggleMemberChoice(evt, choice) {
	let memberChoiceButton = document.getElementsByClassName("member-choice-button");
	let addTripChoice = document.getElementsByClassName("add-trip-choice");

	if (evt.currentTarget.classList.contains('clicked')) {
		for (i = 0; i < memberChoiceButton.length; i++) {
			memberChoiceButton[i].className = memberChoiceButton[i].className.replace(" clicked", "");
		}
		for (i = 0; i < addTripChoice.length; i++) {
			addTripChoice[i].style.display = "none";
		}
	}
	else {
		for (i = 0; i < memberChoiceButton.length; i++) {
			memberChoiceButton[i].className = memberChoiceButton[i].className.replace(" clicked", "");
		}
		for (i = 0; i < addTripChoice.length; i++) {
			addTripChoice[i].style.display = "none";
		}
		evt.currentTarget.className += ' clicked';
		document.getElementById(choice).style.display = "block"
	}
}