//Adapted from https://www.w3schools.com/howto/howto_js_autocomplete.asp

function autocomplete(input, datasource, functioncall) {
	var inp = document.getElementById(input);
	if (!inp) { return; }

	// Repeated calls should only update config, not register duplicate listeners.
	if (inp._autocompleteState) {
		inp._autocompleteState.datasource = datasource;
		inp._autocompleteState.functioncall = functioncall || "";
		return;
	}

	var state = {
		datasource: datasource,
		functioncall: functioncall || "",
		currentFocus: -1,
		oldFocus: 0
	};
	inp._autocompleteState = state;

	inp.addEventListener("input", function(e) {
		var a, b, i, val = this.value;
		closeAllLists();
		if (!val) { return false;}
		state.currentFocus = -1;
		state.oldFocus = 0;
		a = document.createElement("DIV");
		a.setAttribute("id", this.id + "autocomplete-list");
		a.setAttribute("class", "autocomplete-items");
		this.parentNode.appendChild(a);
		data_arr = readPHP(state.datasource + val).split("\n");
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
				if(state.functioncall.length>0){window[state.functioncall]()}
			});
			a.appendChild(b);
		}
	});
	inp.addEventListener("keydown", function(e) {
		var x = document.getElementById(this.id + "autocomplete-list");
		if (x) x = x.getElementsByTagName("div");
		if (e.keyCode == 40){
			//arrow DOWN
			state.currentFocus++;
			addActive(x);
		}else if (e.keyCode == 38) {
			//arrow UP
			state.currentFocus--;
			addActive(x);
		}else if (e.keyCode == 13) {
			//ENTER, select the highlighted suggestion before the page search handler runs
			if (state.currentFocus > -1 && x && x[state.currentFocus]) {
				e.preventDefault();
				e.stopImmediatePropagation();
				x[state.currentFocus].click();
				return;
			}
		}
	}, true);

	/*a function to classify an item as "active":*/
	function addActive(x) {
		if (!x) return false;
		removeActive(x);
		if (state.currentFocus >= x.length) state.currentFocus = 0;
		if (state.currentFocus < 0) state.currentFocus = (x.length - 1);
		x[state.currentFocus].classList.add("autocomplete-active");
		state.oldFocus = state.currentFocus;
	}

	/*a function to remove the "active" class from all autocomplete items:*/
	function removeActive(x) {
		if (x[state.oldFocus]) {
			x[state.oldFocus].classList.remove("autocomplete-active");
		}
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
