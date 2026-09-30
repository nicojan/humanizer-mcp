"""Tier 2 long-form false-positive corpus: the recorded manifest.

Dev-only. The text itself is NOT committed (see eval/fpcorpus/SOURCES.md for
why). fetch_longform.py downloads and normalizes it into eval/fpcorpus/longform/
and verifies each file against the sha256 recorded here.

Every work was first published before 1930, so model contamination is
impossible. Checksums are over the NORMALIZED text, because Project Gutenberg
regenerates its plain-text files and a raw-download checksum drifts for reasons
unrelated to corpus content.
"""

# gutenberg_id -> (title, author, first published, sha256 of normalized text,
#                  normalized chars, sentences per split_sentences)
WORKS: dict[int, tuple[str, str, int, str, int, int]] = {
    74: (
        "The Adventures of Tom Sawyer",
        "Mark Twain",
        1876,
        "ff154c35bd350c8546264ee5c18d853bcaeca0fc3ff359ed103cc73850e228db",
        392360,
        3717,
    ),
    205: (
        "Walden, and On the Duty of Civil Disobedience",
        "Henry David Thoreau",
        1854,
        "3cfd274fa5bda00834f4953ba874ce13b4271a5cb59d1cc207ea8ab30e913649",
        632748,
        3960,
    ),
    1023: (
        "Bleak House",
        "Charles Dickens",
        1853,
        "b99762484f85159eac2812b960bd1e23c6d62208efd8170ede337daa443e1710",
        1938244,
        19178,
    ),
    1342: (
        "Pride and Prejudice",
        "Jane Austen",
        1813,
        "6921027d641e7e5c5d87f4c14dc6b80f17cfad00417edb60dbb46ef1810b603a",
        725237,
        5943,
    ),
    1661: (
        "The Adventures of Sherlock Holmes",
        "Arthur Conan Doyle",
        1892,
        "91c5f470bf7a12893d9ffd5d479d48e0910d25bc140154ff5de518f40bce2f70",
        561795,
        5149,
    ),
    2701: (
        "Moby Dick; Or, The Whale",
        "Herman Melville",
        1851,
        "99c0ec4bf58170a3ae701d431edb09d94b232da1ca0ff726e4f3134636773a34",
        1217905,
        9141,
    ),
}

# The recorded denominator for the rate-per-10k metric. A round that re-fetches
# and re-records must update this and say so, because every reported rate is
# relative to it.
TIER2_SENTENCES = 47088
TIER2_CHARS = 5468289

# SHA-256 of the empty string. Any digest equal to this means an empty or
# missing input hashed to a plausible-looking value, which is the failure mode
# CLAUDE.md warns about. verify() rejects it explicitly.
_EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

__all__ = ["WORKS", "TIER2_SENTENCES", "TIER2_CHARS"]
