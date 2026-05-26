from urllib.request import urlopen

ctsurl=""
oldns = ""
manualurl = ""

def cts_setmanualurl(newurl):
    global manualurl
    manualurl = newurl
    
def cts_setCtsSource(url):
    global ctsurl
    ctsurl = url
    
def cts_nslist():
    global ctsurl
    res = ""
    data = urlopen("https://urncts.eu/namespaceresolver/index.php") 
    for line in data:
        res+=line.decode('utf-8')
    return res

def cts_nsurl(ns):
    global ctsurl
    try:
        data = urlopen("https://urncts.eu/namespaceresolver/"+ns) 
        for line in data:
            ctsurl+=line.decode('utf-8')
    except:
        print("ERROR: CTS Instance "+ns+" is not a registered CTS namespace. If you want to use an unregistered data set, you can set the endpoint URL manually in the file pythoncts.py")
        exit()

def cts_checkConfig(reference):
    global ctsurl
    global manualurl
    global oldns
    if reference.startswith("urn:"):
        reference = reference.split(":")[2]
    if(oldns != reference):
        ctsurl = ""
        oldns = reference
    if(len(ctsurl) == 0 and len(manualurl)==0):
        cts_nsurl(reference)

def cts_requestFromCts (requesturl):
    global ctsurl
    global manualurl
    global cts_lastURL
    
    if len(manualurl)>0:
        thisurl = manualurl
    else:
        thisurl = ctsurl
    
    res = ""
    cts_lastURL = thisurl+requesturl
    print(cts_lastURL)
    try:
        data = urlopen(cts_lastURL)
        for line in data: 
            res+=line.decode('utf-8')
    except:
        print("ERROR: Data Endpoint "+thisurl+" is unavailable. \nIf you want to use an alternative endpoint, you can set the URL manually in the file pythoncts.py. Else you can contact the administrator to communicate this issue. You can find administrative contacts for individual data instances at https://urncts.eu.")
        exit()
    return res.strip("\n")


def cts_punctuation(ns):
    cts_checkConfig(ns)
    return cts_requestFromCts("plain/punctuation.php")

def cts_version(ns):
    cts_checkConfig(ns)
    return cts_requestFromCts("version.txt")

def cts_daterange(ns):
    cts_checkConfig(ns)
    return cts_requestFromCts("plain/daterange.php")

def cts_doccount(ns):
    cts_checkConfig(ns)
    return cts_requestFromCts("plain/doccount.php")

def cts_urncount(ns):
    cts_checkConfig(ns)
    return cts_requestFromCts("plain/urncount.php")

def cts_dates(ns):
    cts_checkConfig(ns)
    return cts_requestFromCts("plain/dates.php")

def cts_doclanguages(ns):
    cts_checkConfig(ns)
    return cts_requestFromCts("plain/doclanguages.php")

def cts_authors(ns):
    cts_checkConfig(ns)
    return cts_requestFromCts("plain/authors.php")

def cts_anyworkurn(ns):
    cts_checkConfig(ns)
    return cts_requestFromCts("plain/anyworkurn.php")

def cts_anyurn(ns):
    cts_checkConfig(ns)
    return cts_requestFromCts("plain/anyurn.php")
    
def cts_inventory(ns):
    cts_checkConfig(ns)
    return cts_requestFromCts("plain/editions.php")
    
def cts_docurns(ns):
    cts_checkConfig(ns)
    return cts_requestFromCts("plain/editionsslim.php")

    
def cts_generatedpassage(urn, params=""):
    cts_checkConfig(urn)
    if len(params)>0 and not params.startswith("&"):
        params = "&"+params
    return cts_requestFromCts("plain/generatedpassage.php?urn="+urn+params)

def cts_urnsperlang(urn, params=""):
    cts_checkConfig(urn)
    if len(params)>0 and not params.startswith("&"):
        params = "&"+params
    return cts_requestFromCts("plain/urnsperlang.php?urn="+urn+params)

def cts_label(urn):
    cts_checkConfig(urn)
    return cts_requestFromCts("plain/label.php?urn="+urn)

def cts_prevnexturn(urn):
    cts_checkConfig(urn)
    return cts_requestFromCts("plain/prevnexturn.php?urn="+urn)

def cts_firsturn(urn):
    cts_checkConfig(urn)
    return cts_requestFromCts("plain/firsturn.php?urn="+urn)

def cts_validreff(urn):
    cts_checkConfig(urn)
    return cts_requestFromCts("plain/validreff.php?urn="+urn)


def cts_structuretext(urn, params=""):
    cts_checkConfig(urn)
    if len(params)>0 and not params.startswith("&"):
        params = "&"+params
    return cts_requestFromCts("plain/structuretext.php?urn="+urn+params)

def cts_structurebagofwords(urn, params="&sort&lowercase"):
    cts_checkConfig(urn)
    if len(params)>0 and not params.startswith("&"):
        params = "&"+params
    return cts_requestFromCts("tm/structurebagofwords.php?urn="+urn+params)

def cts_bagofwords(urn, params="&sort&lowercase"):
    cts_checkConfig(urn)
    if len(params)>0 and not params.startswith("&"):
        params = "&"+params
    return cts_requestFromCts("tm/bagofwords.php?urn="+urn+params)

#    data = urlopen(ctsurl+"tm/ngrams.php?urn="+urn+"&sort&&lowercase&n="+str(ngramsize))

def cts_ngram(urn,params=""):
    cts_checkConfig(urn)
    if len(params)>0 and not params.startswith("&"):
        params = "&"+params
    return cts_requestFromCts("tm/ngrams.php?urn="+urn+params)
    
def cts_passage(urn, params="&deletexml"):
    cts_checkConfig(urn)
    if len(params)>0 and not params.startswith("&"):
        params = "&"+params
    return cts_requestFromCts("plain/passage.php?urn="+urn+params)

def cts_passage_xml(urn, params="&deletexml"):
    cts_checkConfig(urn)
    if len(params)>0 and not params.startswith("&"):
        params = "&"+params
    return cts_requestFromCts("cts/?request=GetPassage&urn="+urn+params)

def cts_textsearch(urn, params=""):
    if not "snippet=" in params:
        return ""
    cts_checkConfig(urn)
    if not params.startswith("&"):
        params = "&"+params
    return cts_requestFromCts("plain/textsearch.php?urn="+urn+params)
    
def cts_exactsearch(urn, params=""):
    if not "snippet=" in params:
        return ""
    cts_checkConfig(urn)
    if not params.startswith("&"):
        params = "&"+params
    return cts_requestFromCts("plain/exactsearch.php?urn="+urn+params)
