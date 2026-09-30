# Tier 2 long-form false-positive corpus: provenance manifest

Six public-domain works, **47,088 sentences** by `src.checker.segment.split_sentences`, 5,468,289 normalized characters. Dev-only, like the rest of `eval/`. The `Dockerfile` copies only `src/` and `data/`, so nothing here reaches the deployed image.

This corpus exists to falsify rules that `eval/corpus/human` structurally cannot: run-length chains, cross-sentence shapes, paragraph-bounded logic, density measures and document-scoped budgets. The two corpora serve different jobs and are kept in different directories on purpose. See `eval/README.md` and `caveats.short_corpus_cannot_validate_run_detectors`.

## The text is not committed

5.5MB of Victorian fiction does not belong in this repo. `eval/fpcorpus/longform/` is gitignored. What is committed is the machinery to rebuild it byte for byte:

```bash
python -m eval.fpcorpus.fetch_longform            # fetch and verify
python -m eval.fpcorpus.fetch_longform --verify   # verify only, no network
```

`eval/fpcorpus/manifest.py` holds the recorded digests and counts. `eval/fpcorpus/normalize.py` holds the normalization. Tier 2 test helpers skip when the corpus is absent, so a clean clone stays green without fetching anything.

## Works

All first published before 1930, so model contamination is impossible. Fetched from `https://www.gutenberg.org/ebooks/<id>.txt.utf-8`.

| Gutenberg id | Title | Author | Published | Normalized chars | Sentences |
|---|---|---|---|---|---|
| 74 | The Adventures of Tom Sawyer | Mark Twain | 1876 | 392,360 | 3,717 |
| 205 | Walden, and On the Duty of Civil Disobedience | Henry David Thoreau | 1854 | 632,748 | 3,960 |
| 1023 | Bleak House | Charles Dickens | 1853 | 1,938,244 | 19,178 |
| 1342 | Pride and Prejudice | Jane Austen | 1813 | 725,237 | 5,943 |
| 1661 | The Adventures of Sherlock Holmes | Arthur Conan Doyle | 1892 | 561,795 | 5,149 |
| 2701 | Moby Dick; Or, The Whale | Herman Melville | 1851 | 1,217,905 | 9,141 |

SHA-256 digests live in `manifest.py` rather than here, so that the verifier and the record cannot drift apart.

## Normalization

Applied by `eval/fpcorpus/normalize.py`, and the digests are taken **after** it.

- The Gutenberg licence header and footer are stripped at the `*** START OF` and `*** END OF` markers.
- Line endings are normalized to `\n`.
- Smart quotes and curly apostrophes become ASCII, matching the convention in `eval/corpus/SOURCES.md`. The word tokenizer splits on a curly apostrophe but not a straight one, so mixing them would be a tokenization confound.
- Ellipsis and en-dash characters become ASCII. **Em-dashes are left verbatim**, exactly as the calibration corpus leaves them. `AR-002` is excluded from the structural sweep, so the em-dash ban never meets this corpus.
- Hard wrapping is unwrapped: single newlines become spaces, blank lines survive as paragraph breaks. Gutenberg plain text is hard-wrapped at about 70 columns, and without this step `split_sentences` and every paragraph-bounded detector both read the wrong thing.

Normalization is load-bearing and was measured to be so. An earlier probe of this round rewrote em-dashes to ` -- ` and produced 47,474 sentences against the same six works. The committed pipeline produces 47,088, which matches the figure the 2026-09-18 anaphora round recorded independently. The checksum in `manifest.py` is what caught the discrepancy.

## Why the digest covers normalized text

Project Gutenberg regenerates its plain-text files. A raw-download digest drifts for reasons unrelated to corpus content, whereas a post-normalization digest pins exactly what the sweep reads. `verify()` also rejects the SHA-256 of the empty string outright, because a missing or empty input otherwise hashes to a plausible-looking value.

## Blind spot, stated up front

**22 of the 40 deployed regex structures score exactly zero on this corpus**, and every one of them targets a marketing shape, a meta-label or a corporate abstraction that Victorian fiction does not contain: `BS-004`, `BS-007`, `BS-021` through `BS-023`, `BS-026` through `BS-032`, `BS-034`, `BS-036` through `BS-038`, `BS-040`, `BS-042`, `BS-044`, `BS-046` through `BS-048`.

A zero here is therefore no more evidence of precision than a 0/16 on the 109-sentence calibration corpus was for an anaphora chain. A round must say which tier answers its question and which tier is blind to it, and must show that a discriminating control fired in the same pipeline before reporting any zero.

## The blind spot cuts both ways

A rule aimed at a modern register can score a clean zero on Tier 2 and still fire on prose written today: Tier 2 is pre-1930 fiction, so it cannot fire on any shape that only modern editorial or technical prose writes. The private source repo behind this project keeps an internal, non-redistributed control for exactly that gap (its own docs plus a modern sibling corpus); it is not part of this public export, since it reads files and paths specific to that private checkout. If you maintain a fork, consider building an equivalent control over your own modern-register prose before shipping a new run-length or cross-sentence rule, and note that a zero on Tier 2 alone is not evidence of precision for such a rule.

## Licence

All six works are in the public domain in the United States. The text is downloaded at use time and never redistributed by this repo.
