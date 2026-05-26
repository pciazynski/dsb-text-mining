var n = function(N){
	return N.length
}

var summe = function(N){
	sum = 0
	for (var i=0;i<N.length;i++){sum+=parseFloat(N[i]);}
	return sum
}

var durchschnitt = function(N){
	return summe(N)/N.length
}

var varianz = function(N){
	avg = durchschnitt(N)
	abw = 0
	for (var i=0;i<N.length;i++){
		xiavg=(parseFloat(N[i]) - avg)
		xiavg = xiavg*xiavg
		abw+=xiavg;
	}
	return abw/(N.length-1)
}

var standardabweichung = function(N){
	return Math.sqrt(varianz(N))
}
