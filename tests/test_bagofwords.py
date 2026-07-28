import bagofwords

# ---------------------------------------------------------------- sanitycheck


def test_sanitycheck_accepts_two_column_payload():
    assert bagofwords.sanitycheck("wóda\t3\nzemja\t1") is True


def test_sanitycheck_rejects_wrong_column_count():
    assert bagofwords.sanitycheck("wóda\t3\t1850") is False
    assert bagofwords.sanitycheck("wóda") is False


def test_sanitycheck_rejects_empty_string():
    assert bagofwords.sanitycheck("") is False


def test_sanitycheck_rejects_trailing_newline():
    # A trailing newline yields an empty final line, which is not 2 columns.
    assert bagofwords.sanitycheck("wóda\t3\n") is False


# -------------------------------------------------------------------- process


def read_tsv(path):
    with open(path, encoding="utf8") as inf:
        return [line.rstrip("\n").split("\t") for line in inf if line.strip()]


def test_process_aggregates_two_year_files(tmp_path, write_peryear):
    base = write_peryear(
        str(tmp_path / "bagofwords"),
        {
            1800: {"wóda": 3, "zemja": 1},
            1850: {"wóda": 2, "luft": 5},
        },
    )
    bagofwords.process(base)

    # _all.txt merges across years and sorts by descending frequency.
    assert read_tsv(base + "/_all.txt") == [
        ["wóda", "5"],
        ["luft", "5"],
        ["zemja", "1"],
    ]

    assert read_tsv(base + "/_tokensumperyear.txt") == [
        ["1800", "4"],
        ["1850", "7"],
    ]

    assert read_tsv(base + "/_typesumperyear.txt") == [
        ["1800", "2"],
        ["1850", "2"],
    ]

    ratios = read_tsv(base + "/_typetokenratioperyear.txt")
    assert [r[0] for r in ratios] == ["1800", "1850"]
    assert float(ratios[0][1]) == 2 / 4
    assert float(ratios[1][1]) == 2 / 7


def test_process_minmaxyearzipf_first_and_last_attestation(tmp_path, write_peryear):
    base = write_peryear(
        str(tmp_path / "bagofwords"),
        {
            1800: {"wóda": 3, "zemja": 1},
            1850: {"wóda": 2, "luft": 5},
        },
    )
    bagofwords.process(base)

    rows = {r[0]: r[1:] for r in read_tsv(base + "/_minmaxyearzipf.txt")}
    assert rows["wóda"] == ["1800", "1850", "5"]  # attested in both years
    assert rows["zemja"] == ["1800", "1800", "1"]
    assert rows["luft"] == ["1850", "1850", "5"]


def test_process_merges_duplicate_tokens_within_a_year(tmp_path, write_peryear):
    base = write_peryear(str(tmp_path / "bagofwords"), {1800: {}})
    peryear_file = base + "peryear/1800.txt"
    with open(peryear_file, "w", encoding="utf8") as outf:
        outf.write("wóda\t2\nwóda\t3\nzemja\t1\n")

    bagofwords.process(base)

    # The per-year file is rewritten deduplicated and sorted by frequency.
    assert read_tsv(peryear_file) == [["wóda", "5"], ["zemja", "1"]]
    assert read_tsv(base + "/_all.txt") == [["wóda", "5"], ["zemja", "1"]]


def test_process_runs_are_independent(tmp_path, write_peryear):
    # Consecutive calls must not accumulate sums from earlier runs.
    base1 = write_peryear(str(tmp_path / "a" / "bagofwords"), {1800: {"wóda": 3}})
    base2 = write_peryear(str(tmp_path / "b" / "bagofwords"), {1800: {"wóda": 4}})
    bagofwords.process(base1)
    bagofwords.process(base2)
    assert read_tsv(base2 + "/_tokensumperyear.txt") == [["1800", "4"]]
