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

function loading(elementid){
	var ifrm = document.getElementById(elementid);
	ifrm = ifrm.contentWindow || ifrm.contentDocument.document || ifrm.contentDocument;
	ifrm.document.open();
	ifrm.document.write(lang_loading);
	ifrm.document.close();
}

function diagrammlink(elementid){
	window.open(document.getElementById(elementid).src, '_blank');
}

function embedding(iframeid){
	alert('<iframe height='+document.getElementById(iframeid).offsetHeight+' width='+document.getElementById(iframeid).offsetWidth + ' src="'+document.getElementById(iframeid).src+'"></iframe>' );
}

function printlink(elementid){
	loading(elementid)
	url = document.getElementById(elementid).src
	if(url.includes('&print=1')){url = url.replace('&print=1','')}else{url += '&print=1'}
	document.getElementById(elementid).src = url
}

var switchLogScale = function(elementid){
	loading(elementid)
	url = document.getElementById(elementid).src
	if(url.includes('&scale=log')){url=url.replaceAll('&scale=log','')}else{url+='&scale=log'}
	document.getElementById(elementid).src = url
}

var threeD = function(iframeid){
	loading(iframeid)
	el = document.getElementById(iframeid)
	if(el.src.includes("3d.html")){el.src=el.src.replace("3d.html",".html")}else{el.src=el.src.replace(".html","3d.html")}
}

function nolanguage(elementid){
	url = document.getElementById(elementid).src
	url=url.replace('&lang=DEU','').replace('&lang=DSB','')
	document.getElementById(elementid).src = url
}

function language(elementid){
	url = document.getElementById(elementid).src
	if(url.includes('&lang=DEU')){url = url.replace('&lang=DEU','')}else{url += '&lang=DEU'}
	document.getElementById(elementid).src = url
}

function hidewatermark(elementid){
	url = document.getElementById(elementid).src
	if(url.includes('&hidewatermark=1')){url = url.replace('&hidewatermark=1','')}else{url += '&hidewatermark=1'}
	document.getElementById(elementid).src = url
}


function datalink(elementid){
	thisdataurl = document.getElementById(elementid).src.split('data=')[1]
	if(thisdataurl.includes('.php')){
		window.open(phpurl+thisdataurl.replace('&','?'), '_blank');
	}else{
		window.open(dataurl+thisdataurl.split('&')[0]+'.txt', '_blank');
	}
}

function hidemenu(headerconf,index){
	headerconf=headerconf.split("")
	headerconf[index] = '0'
	return headerconf.join('')
}
function header(){
headerconftmp = getQueryVariable('headerconf')
if(headerconftmp.length==6){headerconf=headerconftmp}
str='<div class="header">'+
'<table>'
+'<tr style="text-align:center;">'
if(headerconf[0]!=='0'){str+='<td>'+lang_metadata+'&nbsp;<a style="color:black;" href=".?headerconf='+hidemenu(headerconf,0)+'"><sup title="'+lang_closemenu+'">&#10006;</sup></a></td>'}
if(headerconf[1]!=='0'){str+='<td>'+lang_textcorpus+'&nbsp;<a style="color:black;" href=".?headerconf='+hidemenu(headerconf,1)+'"><sup title="'+lang_closemenu+'">&#10006;</sup></a></td>'}
if(headerconf[2]!=='0'){str+='<td><a href="../characters?headerconf='+headerconf+'">'+lang_characters+'</a>&nbsp;<a  style="color:black;" href=".?headerconf='+hidemenu(headerconf,2)+'"><sup title="'+lang_closemenu+'">&#10006;</sup></a></td>'}
if(headerconf[3]!=='0'){str+='<td>'+lang_word+'&nbsp;<a style="color:black;" href=".?headerconf='+hidemenu(headerconf,3)+'"><sup title="'+lang_closemenu+'">&#10006;</sup></a></td>'}
if(headerconf[4]!=='0'){str+='<td>'+lang_connection+'&nbsp;<a style="color:black;" href=".?headerconf='+hidemenu(headerconf,4)+'"><sup title="'+lang_closemenu+'">&#10006;</sup></a></td>'}
if(headerconf[5]!=='0'){str+='<td>'+'SpoznajRec'+'&nbsp;<a style="color:black;" href=".?headerconf='+hidemenu(headerconf,5)+'"><sup title="'+lang_closemenu+'">&#10006;</sup></a></td>'}
str+='<td><a href="'+ctsurl.substring(0,ctsurl.length-4)+'plain/editions.php">'+lang_textapi+'</a></td>'
str+='</tr>'
+'<tr style="text-align:center;">'
if(headerconf[0]!=='0'){str+='<td>'
+'<a href="../metadatarestricted?headerconf='+headerconf+'">'+lang_restricted+'</a> | '
+'<a href="../metadataauthor?headerconf='+headerconf+'">'+lang_author+'</a> | '
+'<a href="../metadatadochierarchy?headerconf='+headerconf+'">'+lang_dochierarchy+'</a> | '
+'<a href="../metadatalang?headerconf='+headerconf+'">'+lang_lang+'</a>'
+'</td>'
}
if(headerconf[1]!=='0'){str+='<td>'
+'<a href="../docreferences?headerconf='+headerconf+'">'+lang_docreferences+'</a> | '
+'<a href="../typorecognition?headerconf='+headerconf+'">'+lang_typorec+'</a> | '
+'<a href="../stats?headerconf='+headerconf+'">'+lang_statistics+'</a> | '
+'<a href="../tokenrec?headerconf='+headerconf+'">'+lang_coverage+'</a> | '
+'<a href="../bwtime?headerconf='+headerconf+'">'+lang_genesis_disappear+'</a>'
+'</td>'
}
if(headerconf[2]!=='0'){str+='<td>'
+'</td>'
}
if(headerconf[3]!=='0'){str+='<td>'
+'<a href="../bwlemma?headerconf='+headerconf+'">'+lang_timeline+'</a> | '
+'<a href="../lemmavariation?headerconf='+headerconf+'">'+lang_variation+'</a> | '
+'<a href="../lemmaeval?headerconf='+headerconf+'">'+lang_evaluation+'</a> | '
+'<a href="../profile?headerconf='+headerconf+'">'+lang_profile+'</a>'
+'</td>'
}
if(headerconf[4]!=='0'){str+='<td>'
+'<a href="../collocation?headerconf='+headerconf+'">'+lang_collocation+'</a> | '
+'<a href="../ngram?headerconf='+headerconf+'&n=3">'+lang_trigram+'</a>'
+'</td>'
}
if(headerconf[5]!=='0'){str+='<td>'
+'<a href="../langdetect?headerconf='+headerconf+'&n=3">'+lang_langdetect+'</a> | <a href="../langrec/?headerconf='+headerconf+'&n=3">'+lang_langrec+'</a> | '
+'<a href="../langsep?headerconf='+headerconf+'">'+lang_langsep+'</a>'
+'</td>'
}
str+='<td id="resetmenubutton">'
if(headerconf.includes('0')){str+='<a  style="color:black;" href=".">'+lang_resetmenu+'</a>'}
str+='</td>'
+'</tr>'
+'</table>' 
+'</div>'

return str
}

function footer(){
str='<div class="header">'+
'<table>'
+'<tr>'
+'<td>'
+'<a href="../../">'+lang_projectsite+'</a>'
+'</td>'
+'<td>'
+'<a href="../../README.md">'+lang_citref+'</a>'
+'</td>'
+'<td>'
+'<a href="../../../">'+lang_hubarea+'</a>'
+'</td>'
+'</tr>'
+'</table>' 
+'</div>'
return str
}
