"""Regression tests for known, unfixed bugs in etl/mappingeval.py."""

import pytest

import mappingeval


def write_rows(path, rows):
    with open(path, "w", encoding="utf8") as outf:
        for row in rows:
            outf.write("\t".join(row) + "\n")


def read_rows(path):
    with open(path, encoding="utf8") as inf:
        return [line.rstrip("\n").split("\t") for line in inf]


def test_count_uniqueness_writes_record_and_occurrence_weighted_metrics(tmp_path):
    mapping = tmp_path / "_all.txt"
    output = tmp_path / "_lemmauniqueness.txt"
    write_rows(
        mapping,
        [
            ["form-a", "|A|", "", "", "5"],
            ["form-b", "|A|B|", "", "", "2"],
        ],
    )

    mappingeval.write_uniqueness(
        str(output), mappingeval.count_uniqueness(str(mapping))
    )

    assert read_rows(output) == [
        ["A", "0.5", "1", "1", str(5 / 7), "5", "2"],
        ["B", "0.0", "0", "1", "0.0", "0", "2"],
    ]


def test_count_uniqueness_rejects_unwrapped_target_with_row_context(tmp_path):
    mapping = tmp_path / "_all.txt"
    write_rows(mapping, [["form", "PŚIŚ", "", "", "1"]])

    with pytest.raises(ValueError, match="row 1"):
        mappingeval.count_uniqueness(str(mapping))


def test_count_uniqueness_rejects_mapping_row_without_frequency(tmp_path):
    mapping = tmp_path / "_all.txt"
    write_rows(mapping, [["form", "|A|"]])

    with pytest.raises(ValueError, match="row 1"):
        mappingeval.count_uniqueness(str(mapping))


def test_count_sorting_redundancy_does_not_credit_identical_groups(tmp_path):
    bag = tmp_path / "_lemmabag.txt"
    write_rows(bag, [["|A|B|", "7"], ["|A|B|", "5"]])

    assert mappingeval.count_sorting_redundancy(str(bag)) == (1, 1, 0)
