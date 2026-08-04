"""Shared evaluation of a lemma/norm mapping against the bag of words."""

from settings import datadir


def collect_mapped_forms(mappingpath, inconsistenciespath):
    """Read a mapping; write word forms mapped more than once, return forms + count."""
    bl = {}
    incons = 0
    with (
        open(mappingpath, "r", encoding="utf8") as bwin,
        open(inconsistenciespath, "w", encoding="utf8") as incout,
    ):
        for line in bwin:
            linearr = line.split("\t")
            if linearr[0] in bl:
                incout.write(linearr[0] + "\n")
                incons += 1
            bl[linearr[0]] = 1

    return bl, incons


def split_bagofwords(bagpath, yaypath, naypath, progresspath, bl):
    """Split the bag of words into mapped / unmapped, return both counts."""
    yay = 0
    nay = 0
    progress = {}

    with (
        open(bagpath, "r", encoding="utf8") as bwin,
        open(yaypath, "w", encoding="utf8") as outyay,
        open(naypath, "w", encoding="utf8") as outnay,
    ):
        for line in bwin:
            linearr = line.split("\t")
            if linearr[0] in bl:
                outyay.write(line)
                yay += 1
                progress[line.strip()] = 1
            else:
                nay += 1
                progress[line.strip()] = 0
                outnay.write(line)

    with open(progresspath, "w", encoding="utf8") as outprogress:
        for line, value in sorted(progress.items(), key=lambda x: x[1], reverse=True):
            outprogress.write(line + "\t" + str(progress[line]) + "\n")

    return yay, nay


def count_sorting_redundancy(bagpath):
    """Return (sorted entries, unsorted entries, tokens saved by sorting)."""
    unsortedlist = {}
    sortedlist = {}

    sortedtypecount = 0
    unsortedtypecount = 0

    with open(bagpath, "r", encoding="utf8") as inf:
        for line in inf:
            count = int(line.split("\t")[1])
            line = line.split("\t")[0]
            linearr = line.split("|")
            if len(linearr) > 3:
                unsortedtypecount += count
                unsortedlist["|".join(linearr)] = 1
                linearr = sorted(linearr)
                if not "|".join(linearr) in sortedlist:
                    sortedtypecount += count
                sortedlist["|".join(linearr)] = 1

    return len(sortedlist), len(unsortedlist), unsortedtypecount - sortedtypecount


def write_stats(statspath, statslabel, yay, nay, incons, redundancy):
    sortedcount, unsortedcount, savedtokens = redundancy
    with open(statspath, "w", encoding="utf8") as out:
        out.write(statslabel + " / Alle: " + str(yay) + " / " + str(yay + nay) + "\n")
        out.write("Inkonsistent: " + str(incons) + "\n")
        out.write(
            "Sortierungsredundanz (ambige Einträge sortiert / ambige Einträge unsortiert / Betroffene Token ) : "
            + str(sortedcount)
            + " / "
            + str(unsortedcount)
            + " / "
            + str(savedtokens)
            + "\n"
        )


def count_uniqueness(mappingpath):
    """Return per mapping target: (uniqueness ratio, unique count, ambiguous count)."""
    bag = {}
    ambiquebag = {}
    groupbag = {}

    with open(mappingpath, "r", encoding="utf8") as inf:
        for line in inf:
            linearr = line.split("\t")
            entry = linearr[1]
            entry = entry[1:-1]
            if len(entry) > 0:
                entryarr = entry.split("|")
                if len(entryarr) > 1:
                    if entry in groupbag:
                        groupbag[entry] = groupbag[entry] + 1
                    else:
                        groupbag[entry] = 1
                    for key in entryarr:
                        if key in ambiquebag:
                            ambiquebag[key] = ambiquebag[key] + 1
                        else:
                            ambiquebag[key] = 1

                for key in entryarr:
                    if key in bag:
                        bag[key] = bag[key] + 1
                    else:
                        bag[key] = 1

    uniquenessbag = {}
    uniquebag = {}

    for entry in bag:
        insg = bag[entry]
        if entry in ambiquebag:
            ambique = ambiquebag[entry]
        else:
            ambiquebag[entry] = 0
            ambique = 0
        unique = insg - ambique
        uniquebag[entry] = unique
        uniquenessbag[entry] = unique / insg

    return uniquenessbag, uniquebag, ambiquebag


def write_uniqueness(uniquenesspath, uniqueness):
    uniquenessbag, uniquebag, ambiquebag = uniqueness
    with open(uniquenesspath, "w", encoding="utf8") as outf:
        for entry, value in sorted(
            uniquenessbag.items(), key=lambda x: x[1], reverse=True
        ):
            outf.write(
                entry
                + "\t"
                + str(uniquenessbag[entry])
                + "\t"
                + str(uniquebag[entry])
                + "\t"
                + str(ambiquebag[entry])
                + "\n"
            )


def run(prefix, statslabel):
    """Evaluate the <prefix>mapping folder, e.g. run("lemma", "Lemmatisiert")."""
    folder = datadir + prefix + "mapping/"
    mappingpath = folder + "_all.txt"

    bl, incons = collect_mapped_forms(mappingpath, folder + "_inconsistencies.txt")

    yay, nay = split_bagofwords(
        datadir + "bagofwords/_all.txt",
        folder + "_yay.txt",
        folder + "_nay.txt",
        folder + "_progress.txt",
        bl,
    )

    redundancy = count_sorting_redundancy(folder + "_" + prefix + "bag.txt")

    write_stats(folder + "_stats.txt", statslabel, yay, nay, incons, redundancy)

    write_uniqueness(
        folder + "_" + prefix + "uniqueness.txt", count_uniqueness(mappingpath)
    )
