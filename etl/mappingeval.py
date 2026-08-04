"""Shared evaluation of a lemma/norm mapping against the bag of words."""

from collections import defaultdict

from settings import datadir


class _WeightedDict(dict):
    """A dict that also carries per-key weight attributes as side channels."""


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
            group, freq = line.split("\t")[:2]
            parts = group.split("|")
            if len(parts) <= 3:
                continue
            count = int(freq)
            if group not in unsortedlist:
                unsortedtypecount += count
                unsortedlist[group] = 1
            sortedkey = "|".join(sorted(parts))
            if sortedkey not in sortedlist:
                sortedtypecount += count
                sortedlist[sortedkey] = 1

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
    """Return per mapping target: (uniqueness ratio, unique count, ambiguous count).

    The returned dicts also carry occurrence-weighted counterparts:
    ``uniquenessbag.weighted_ratio``, ``uniquebag.weighted`` and
    ``ambiquebag.weighted``.
    """
    total = defaultdict(int)
    ambigue = defaultdict(int)
    weighted_total = defaultdict(int)
    weighted_ambigue = defaultdict(int)

    with open(mappingpath, "r", encoding="utf8") as inf:
        for rownum, line in enumerate(inf, start=1):
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 5:
                raise ValueError(f"row {rownum}: missing fields")
            try:
                count = int(fields[4].strip())
            except ValueError:
                raise ValueError(f"row {rownum}: invalid frequency") from None

            entry = fields[1]
            if entry == "":
                continue
            if not (entry.startswith("|") and entry.endswith("|")):
                raise ValueError(f"row {rownum}: unwrapped target {entry!r}")
            entry = entry[1:-1]
            if not entry:
                continue

            keys = entry.split("|")
            ambiguous = len(keys) > 1
            for key in keys:
                total[key] += 1
                weighted_total[key] += count
                if ambiguous:
                    ambigue[key] += 1
                    weighted_ambigue[key] += count

    uniquenessbag = _WeightedDict()
    uniquebag = _WeightedDict()
    ambiquebag = _WeightedDict()
    weighted_ratio = _WeightedDict()
    weighted_unique = _WeightedDict()
    weighted_ambigue_out = _WeightedDict()

    for key, insg in total.items():
        amb = ambigue[key]
        uniquebag[key] = insg - amb
        uniquenessbag[key] = (insg - amb) / insg
        ambiquebag[key] = amb

        total_w = weighted_total[key]
        amb_w = weighted_ambigue[key]
        weighted_unique[key] = total_w - amb_w
        weighted_ambigue_out[key] = amb_w
        weighted_ratio[key] = (total_w - amb_w) / total_w if total_w else 0.0

    uniquenessbag.weighted_ratio = weighted_ratio
    uniquebag.weighted = weighted_unique
    ambiquebag.weighted = weighted_ambigue_out

    return uniquenessbag, uniquebag, ambiquebag


def write_uniqueness(uniquenesspath, uniqueness):
    uniquenessbag, uniquebag, ambiquebag = uniqueness
    has_weights = hasattr(uniquenessbag, "weighted_ratio")
    with open(uniquenesspath, "w", encoding="utf8") as outf:
        for entry, value in sorted(
            uniquenessbag.items(), key=lambda x: x[1], reverse=True
        ):
            parts = [
                entry,
                str(uniquenessbag[entry]),
                str(uniquebag[entry]),
                str(ambiquebag[entry]),
            ]
            if has_weights:
                parts.extend(
                    [
                        str(uniquenessbag.weighted_ratio[entry]),
                        str(uniquebag.weighted[entry]),
                        str(ambiquebag.weighted[entry]),
                    ]
                )
            outf.write("\t".join(parts) + "\n")


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
