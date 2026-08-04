import sys

import mapping_etl
from settings import count, ctsns, datadir, copyrighttoken, tokenlength
from pythoncts import *

FIELD = "norm"
MODULE_LABEL = "normierowasch"
BAG_ATTR = "normbag"
MAPPING_ATTR = "normmapping"
MAPPING_DIR = "normmapping"
PERYEAR_DIR = "normmappingperyear"
DB_NAME = "normmapping.db"
BAG_FILE = "_normbag.txt"
INDEX_SQL = (
    "CREATE INDEX tokenindextype ON tokennormtypesubtypefrequency(token)",
    "CREATE INDEX normindextype ON tokennormtypesubtypefrequency(norm)",
    "CREATE INDEX typeindextype ON tokennormtypesubtypefrequency(type)",
    "CREATE INDEX subtypeindextype ON tokennormtypesubtypefrequency(subtype)",
    "CREATE INDEX tokenindex ON tokennormtypesubtypedatefrequency(token)",
    "CREATE INDEX normindex ON tokennormtypesubtypedatefrequency(norm)",
    "CREATE INDEX typeindex ON tokennormtypesubtypedatefrequency(type)",
    "CREATE INDEX subtypeindex ON tokennormtypesubtypedatefrequency(subtype)",
    "CREATE INDEX dateindex ON tokennormtypesubtypedatefrequency(date)",
    "CREATE INDEX normfrequencyindex ON normfrequency(norm)",
    "CREATE INDEX normfrequencysortkeyindex ON normfrequency(sortkey)",
    "CREATE INDEX normtokenindex ON normtokenfrequency(norm)",
    "CREATE INDEX normtokentokenindex ON normtokenfrequency(token)",
    "CREATE INDEX normurnindex ON urndatenormbag(urn)",
    "CREATE INDEX urnindex ON urndatenormbag(normbag)",
    "CREATE INDEX urndateindex ON urndatenormbag(date)",
    "CREATE INDEX normnonambignorm ON normnonambig(norm)",
    "CREATE INDEX normnonambigsortkey ON normnonambig(sortkey)",
)

normbag = {}
bagofwords = {}

_SELF = sys.modules[__name__]


def load_bagofwords():
    return mapping_etl.load_bagofwords(_SELF)


def tokencheck(token):
    return mapping_etl.tokencheck(_SELF, token)


def normmapping(urn):
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
