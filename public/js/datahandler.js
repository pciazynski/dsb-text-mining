function readTextFile(file){
	textstr=""
	rawFile = new XMLHttpRequest();
	rawFile.open("GET", dataurl+file+".txt", false);
	rawFile.onreadystatechange = function (){
		if(rawFile.readyState === 4){
			if(rawFile.status === 200 || rawFile.status == 0)
			{textstr = rawFile.responseText;}
		}}
	rawFile.send(null);
	return textstr
}

async function readTextFile_async(file){
	let response = await fetch(dataurl+file+".txt")
	let txt = await response.text()
	return txt
}

function ctsrequest(url){
	textstr=""
	rawFile = new XMLHttpRequest();
	rawFile.open("GET", url, false);
	rawFile.onreadystatechange = function (){
		if(rawFile.readyState === 4){
			if(rawFile.status === 200 || rawFile.status == 0)
			{textstr = rawFile.responseText;}
		}}
	rawFile.send(null);
	return textstr
}


function readPHP(file){
	textstr=""
	rawFile = new XMLHttpRequest();
	rawFile.open("GET", phpurl+file, false);
	rawFile.onreadystatechange = function (){
		if(rawFile.readyState === 4){
			if(rawFile.status === 200 || rawFile.status == 0){
				textstr = rawFile.responseText;
			}
		}
	}
	rawFile.send(null);
	return textstr
}

async function readGeoJsonFile(file){
	let response = await fetch(geourl+file+".json")
	let txt = await response.text()
	return txt
}

async function readPHP_async(file){
	let response = await fetch(phpurl+file)
	let txt = await response.text()
	return txt
}

function getQueryVariable(variable) {
	var query = window.location.search.substring(1);
	var vars = query.split("&");
	for (var i=0;i<vars.length;i++) {
		var pair = vars[i].split("=");
		if (pair[0] == variable) {
			return decodeURIComponent(pair[1]);
		}
	} 
	return ""
}



