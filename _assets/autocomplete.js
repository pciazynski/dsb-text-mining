//Adapted from https://www.w3schools.com/howto/howto_js_autocomplete.asp

function autocomplete(input, datasource, functioncall) {
	inp = document.getElementById(input)
	var currentFocus;
	var oldFocus;
	inp.addEventListener("input", function(e) {
		var a, b, i, val = this.value;
		closeAllLists();
		if (!val) { return false;}
		currentFocus = -1, oldFocus = 0;
		a = document.createElement("DIV");
		a.setAttribute("id", this.id + "autocomplete-list");
		a.setAttribute("class", "autocomplete-items");
		this.parentNode.appendChild(a);
		data_arr = readPHP(datasource+val).split("\n");
		for (i = 0; i < data_arr.length; i++) {
			b = document.createElement("DIV");
			/*make the matching letters bold:*/
			b.innerHTML = "<strong>" + data_arr[i].substr(0, val.length) + "</strong>";
			b.innerHTML += data_arr[i].substr(val.length);
			/*insert a input field that will hold the current array item's value:*/
			b.innerHTML += "<input type='hidden' value='" + data_arr[i] + "'>";
			b.addEventListener("click", function(e) {
				document.getElementById(input).value = this.getElementsByTagName("input")[0].value;
				closeAllLists();
				if(functioncall.length>0){window[functioncall]()}
			});
			a.appendChild(b);
	}});
	inp.addEventListener("keydown", function(e) {
	var x = document.getElementById(this.id + "autocomplete-list");
	if (x) x = x.getElementsByTagName("div");
	if (e.keyCode == 40){
		//arrow DOWN
		currentFocus++;
		addActive(x);
	}else if (e.keyCode == 38) {
		//arrow UP
		currentFocus--;
		addActive(x);
	}else if (e.keyCode == 13) {
		//ENTER, simulate a click on "active"
		if (currentFocus > -1) {if (x) x[currentFocus].click();}
	}
});

/*a function to classify an item as "active":*/
function addActive(x) {
	if (!x) return false;
	removeActive(x);
	if (currentFocus >= x.length) currentFocus = 0;
	if (currentFocus < 0) currentFocus = (x.length - 1);
	x[currentFocus].classList.add("autocomplete-active");
	oldFocus = currentFocus
}

/*a function to remove the "active" class from all autocomplete items:*/
function removeActive(x) {
	x[oldFocus].classList.remove("autocomplete-active");
}
function closeAllLists(elmnt) {
	var x = document.getElementsByClassName("autocomplete-items");
	for (var i = 0; i < x.length; i++) {
		x[i].parentNode.removeChild(x[i]);
	}
}
/*execute a function when someone clicks in the document:*/
document.addEventListener("click", function (e){
	closeAllLists(e.target);
});
}

