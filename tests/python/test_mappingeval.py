import os

import lemmaeval
import mappingeval
import normeval
import pytest

TAB = "\t"


def read_lines(path):
    with open(path, encoding="utf8") as inf:
        return inf.read().splitlines()


def read_rows(path):
    """Read a file as tab-separated column lists so empty columns stay visible."""
    return [line.split(TAB) for line in read_lines(path)]


def write_rows(path, rows):
    with open(path, "w", encoding="utf8") as outf:
        for row in rows:
            print(*row, sep=TAB, file=outf)


# token, target, type, subtype, count -- as lemmatisierowasch writes _all.txt
LEMMA_MAPPING = [
    ["a", "|A|", "n", "x", "5"],
    ["a", "|B|", "n", "x", "3"],
    ["b", "|A|B|", "n", "x", "2"],
    ["c", "|C|", "n", "x", "1"],
]

# target group, count -- as lemmatisierowasch writes _lemmabag.txt
LEMMA_BAG = [
    ["|A|B|", "7"],
    ["|B|A|", "4"],
    ["|C|", "1"],
    ["|A|B|C|", "2"],
]

BAG_OF_WORDS = [
    ["a", "8"],
    ["b", "2"],
    ["z", "9"],
]

STATS = [
    "Lemmatisiert / Alle: 2 / 3",
    "Inkonsistent: 1",
    "Sortierungsredundanz (ambige Einträge sortiert / ambige Einträge "
    "unsortiert / Betroffene Token ) : 2 / 3 / 4",
]


@pytest.fixture
def mapping_datadir(tmp_path, monkeypatch):
    """Point mappingeval at a tmp data dir and create the folders run() expects."""
    base = str(tmp_path) + os.sep
    os.makedirs(base + "bagofwords")
    os.makedirs(base + "lemmamapping")
    os.makedirs(base + "normmapping")
    monkeypatch.setattr(mappingeval, "datadir", base)
    return base


# --- collect_mapped_forms ---------------------------------------------------


def test_collect_mapped_forms_returns_every_form_once(tmp_path):
    mapping = tmp_path / "_all.txt"
    write_rows(mapping, [["a", "|A|", "n", "x", "5"], ["b", "|B|", "n", "x", "2"]])

    bl, incons = mappingeval.collect_mapped_forms(
        str(mapping), str(tmp_path / "_inconsistencies.txt")
    )

    assert bl == {"a": 1, "b": 1}
    assert incons == 0


def test_collect_mapped_forms_writes_repeated_forms_as_inconsistencies(tmp_path):
    mapping = tmp_path / "_all.txt"
    write_rows(
        mapping,
        [
            ["a", "|A|", "n", "x", "5"],
            ["a", "|B|", "n", "x", "3"],
            ["a", "|C|", "n", "x", "1"],
        ],
    )
    inconsistencies = tmp_path / "_inconsistencies.txt"

    bl, incons = mappingeval.collect_mapped_forms(str(mapping), str(inconsistencies))

    assert incons == 2
    assert read_lines(inconsistencies) == ["a", "a"]
    assert bl == {"a": 1}


def test_collect_mapped_forms_empty_mapping_creates_empty_inconsistencies_file(
    tmp_path,
):
    mapping = tmp_path / "_all.txt"
    write_rows(mapping, [])
    inconsistencies = tmp_path / "_inconsistencies.txt"

    bl, incons = mappingeval.collect_mapped_forms(str(mapping), str(inconsistencies))

    assert (bl, incons) == ({}, 0)
    assert read_lines(inconsistencies) == []


# --- split_bagofwords -------------------------------------------------------


def test_split_bagofwords_separates_mapped_from_unmapped(tmp_path):
    bag = tmp_path / "bag.txt"
    write_rows(bag, BAG_OF_WORDS)
    yay, nay = tmp_path / "yay.txt", tmp_path / "nay.txt"

    mapped, unmapped = mappingeval.split_bagofwords(
        str(bag), str(yay), str(nay), str(tmp_path / "progress.txt"), {"a": 1, "b": 1}
    )

    assert (mapped, unmapped) == (2, 1)
    assert read_rows(yay) == [["a", "8"], ["b", "2"]]
    assert read_rows(nay) == [["z", "9"]]


def test_split_bagofwords_progress_lists_mapped_before_unmapped(tmp_path):
    bag = tmp_path / "bag.txt"
    write_rows(bag, [["z", "1"], ["a", "2"], ["m", "3"], ["b", "4"]])
    progress = tmp_path / "progress.txt"

    mappingeval.split_bagofwords(
        str(bag),
        str(tmp_path / "yay.txt"),
        str(tmp_path / "nay.txt"),
        str(progress),
        {"m": 1, "z": 1},
    )

    assert read_rows(progress) == [
        ["z", "1", "1"],
        ["m", "3", "1"],
        ["a", "2", "0"],
        ["b", "4", "0"],
    ]


def test_split_bagofwords_empty_bag_writes_empty_files(tmp_path):
    bag = tmp_path / "bag.txt"
    write_rows(bag, [])
    yay, nay, progress = (
        tmp_path / "yay.txt",
        tmp_path / "nay.txt",
        tmp_path / "progress.txt",
    )

    counts = mappingeval.split_bagofwords(
        str(bag), str(yay), str(nay), str(progress), {"a": 1}
    )

    assert counts == (0, 0)
    assert (read_rows(yay), read_rows(nay), read_rows(progress)) == ([], [], [])


# --- count_sorting_redundancy ----------------------------------------------


def test_count_sorting_redundancy_ignores_unambiguous_entries(tmp_path):
    bag = tmp_path / "_lemmabag.txt"
    write_rows(bag, [["|A|", "3"], ["|B|", "2"]])

    assert mappingeval.count_sorting_redundancy(str(bag)) == (0, 0, 0)


def test_count_sorting_redundancy_merges_permutations_of_the_same_group(tmp_path):
    bag = tmp_path / "_lemmabag.txt"
    write_rows(bag, LEMMA_BAG)

    # |A|B| and |B|A| collapse into one sorted group, |C| is not ambiguous.
    assert mappingeval.count_sorting_redundancy(str(bag)) == (2, 3, 4)


# --- write_stats ------------------------------------------------------------


def test_write_stats_writes_counts_and_redundancy(tmp_path):
    stats = tmp_path / "_stats.txt"

    mappingeval.write_stats(str(stats), "Lemmatisiert", 2, 1, 1, (2, 3, 4))

    assert read_lines(stats) == STATS


# --- count_uniqueness -------------------------------------------------------


def test_count_uniqueness_splits_unique_and_ambiguous_occurrences(tmp_path):
    mapping = tmp_path / "_all.txt"
    write_rows(mapping, LEMMA_MAPPING)

    uniqueness, unique, ambiguous = mappingeval.count_uniqueness(str(mapping))

    assert uniqueness == {"A": 0.5, "B": 0.5, "C": 1.0}
    assert unique == {"A": 1, "B": 1, "C": 1}
    assert ambiguous == {"A": 1, "B": 1, "C": 0}


def test_count_uniqueness_ignores_lines_without_a_mapping_target(tmp_path):
    mapping = tmp_path / "_all.txt"
    write_rows(mapping, [["a", "", "n", "x", "5"], ["b", "|B|", "n", "x", "1"]])

    uniqueness, unique, ambiguous = mappingeval.count_uniqueness(str(mapping))

    assert (uniqueness, unique, ambiguous) == ({"B": 1.0}, {"B": 1}, {"B": 0})


def test_count_uniqueness_empty_mapping_returns_empty_bags(tmp_path):
    mapping = tmp_path / "_all.txt"
    write_rows(mapping, [])

    assert mappingeval.count_uniqueness(str(mapping)) == ({}, {}, {})


# --- write_uniqueness -------------------------------------------------------


def test_write_uniqueness_sorts_by_ratio_descending(tmp_path):
    out = tmp_path / "_lemmauniqueness.txt"

    mappingeval.write_uniqueness(
        str(out),
        (
            {"A": 0.5, "C": 1.0, "B": 0.25},
            {"A": 1, "C": 1, "B": 1},
            {"A": 1, "C": 0, "B": 3},
        ),
    )

    # target, uniqueness ratio, unique count, ambiguous count
    assert read_rows(out) == [
        ["C", "1.0", "1", "0"],
        ["A", "0.5", "1", "1"],
        ["B", "0.25", "1", "3"],
    ]


# --- run --------------------------------------------------------------------


def write_mapping_fixture(base, prefix):
    write_rows(base + "bagofwords/_all.txt", BAG_OF_WORDS)
    folder = base + prefix + "mapping/"
    write_rows(folder + "_all.txt", LEMMA_MAPPING)
    write_rows(folder + "_" + prefix + "bag.txt", LEMMA_BAG)
    return folder


def test_run_writes_all_evaluation_files(mapping_datadir):
    folder = write_mapping_fixture(mapping_datadir, "lemma")

    mappingeval.run("lemma", "Lemmatisiert")

    assert sorted(os.listdir(folder)) == [
        "_all.txt",
        "_inconsistencies.txt",
        "_lemmabag.txt",
        "_lemmauniqueness.txt",
        "_nay.txt",
        "_progress.txt",
        "_stats.txt",
        "_yay.txt",
    ]


def test_run_stats_combine_mapping_and_bagofwords(mapping_datadir):
    folder = write_mapping_fixture(mapping_datadir, "lemma")

    mappingeval.run("lemma", "Lemmatisiert")

    assert read_lines(folder + "_stats.txt") == STATS


def test_run_writes_uniqueness_under_the_prefixed_name(mapping_datadir):
    folder = write_mapping_fixture(mapping_datadir, "lemma")

    mappingeval.run("lemma", "Lemmatisiert")

    assert read_rows(folder + "_lemmauniqueness.txt") == [
        ["C", "1.0", "1", "0", "1.0", "1", "0"],
        ["A", "0.5", "1", "1", str(5 / 7), "5", "2"],
        ["B", "0.5", "1", "1", "0.6", "3", "2"],
    ]


def test_run_missing_mapping_file_raises_filenotfound(mapping_datadir):
    write_rows(mapping_datadir + "bagofwords/_all.txt", BAG_OF_WORDS)

    with pytest.raises(FileNotFoundError):
        mappingeval.run("lemma", "Lemmatisiert")


# --- lemmaeval / normeval entry points --------------------------------------


def test_lemmaeval_main_evaluates_the_lemma_mapping(mapping_datadir):
    folder = write_mapping_fixture(mapping_datadir, "lemma")

    lemmaeval.main()

    assert read_lines(folder + "_stats.txt")[0] == "Lemmatisiert / Alle: 2 / 3"


def test_normeval_main_evaluates_the_norm_mapping(mapping_datadir):
    folder = write_mapping_fixture(mapping_datadir, "norm")

    normeval.main()

    assert read_lines(folder + "_stats.txt")[0] == "Normiert / Alle: 2 / 3"
