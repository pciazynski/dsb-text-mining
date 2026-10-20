import sys
from urllib.request import urlopen

import mapping_etl
from settings import count, ctsns, datadir, copyrighttoken, tokenlength
from pythoncts import *

FIELD = "lemma"
MODULE_LABEL = "lemmatisierowasch"
BAG_ATTR = "lemmabag"
MAPPING_ATTR = "lemmamapping"
MAPPING_DIR = "lemmamapping"
PERYEAR_DIR = "lemmamappingperyear"
DB_NAME = "lemmamapping.db"
BAG_FILE = "_lemmabag.txt"
INDEX_SQL = (
    "CREATE INDEX tokenindextype ON tokenlemmatypesubtypefrequency(token)",
    "CREATE INDEX lemmaindextype ON tokenlemmatypesubtypefrequency(lemma)",
    "CREATE INDEX subtypeindextype ON tokenlemmatypesubtypefrequency(subtype)",
    "CREATE INDEX tokenindex ON tokenlemmatypesubtypedatefrequency(token)",
    "CREATE INDEX lemmaindex ON tokenlemmatypesubtypedatefrequency(lemma)",
    "CREATE INDEX typeindex ON tokenlemmatypesubtypedatefrequency(type)",
    "CREATE INDEX subtypeindex ON tokenlemmatypesubtypedatefrequency(subtype)",
    "CREATE INDEX dateindex ON tokenlemmatypesubtypedatefrequency(date)",
    "CREATE INDEX lemmafrequencyindex ON lemmafrequency(lemma)",
    "CREATE INDEX lemmafrequencysortkeyindex ON lemmafrequency(sortkey)",
    "CREATE INDEX lemmatokenlemmaindex ON lemmatokenfrequency(lemma)",
    "CREATE INDEX lemmatokentokenindex ON lemmatokenfrequency(token)",
    "CREATE INDEX lemmaurnindex ON urndatelemmabag(urn)",
    "CREATE INDEX urnindex ON urndatelemmabag(lemmabag)",
    "CREATE INDEX urndateindex ON urndatelemmabag(date)",
    "CREATE INDEX lemmanonambiglemma ON lemmanonambig(lemma)",
    "CREATE INDEX lemmanonambigsortkey ON lemmanonambig(sortkey)",
)

lemmabag = {}
bagofwords = {}
ctsurl = ""

_SELF = sys.modules[__name__]


def requestctsurl(ns):
    global ctsurl
    if ctsurl:
        return
    if not ns.startswith("urn:cts"):
        ns = "urn:cts:" + ns
    ns = ns.split(":")[2]
    data = urlopen("https://urncts.eu/namespaceresolver/" + ns)
    for line in data:
        ctsurl += line.decode("utf-8")


def before_mapping(urn):
    requestctsurl(urn)


def load_bagofwords():
    return mapping_etl.load_bagofwords(_SELF)


def tokencheck(token):
    return mapping_etl.tokencheck(_SELF, token)


def lemmamapping(urn):
    return mapping_etl.mapping(_SELF, urn)


def process(foldername):
    return mapping_etl.process(foldername)


def reset():
    return mapping_etl.reset(_SELF)


def getdoclist(ctsns):
    return mapping_etl.getdoclist(_SELF, ctsns)


def collect():
    return mapping_etl.collect(_SELF)


def index(db_path=None):
    return mapping_etl.index(_SELF, db_path)


def initTables(db_path=None):
    return mapping_etl.initTables(_SELF, db_path)


def db():
    return mapping_etl.db(_SELF)


def main(argv=None):
    return mapping_etl.main(_SELF, argv)


if __name__ == "__main__":
    main()
