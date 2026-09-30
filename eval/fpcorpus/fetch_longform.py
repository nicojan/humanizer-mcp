"""Fetch and verify the Tier 2 long-form false-positive corpus.

    python -m eval.fpcorpus.fetch_longform          # fetch missing, verify all
    python -m eval.fpcorpus.fetch_longform --verify # verify only, no network

Dev-only. Writes to eval/fpcorpus/longform/, which is gitignored: the corpus is
5.5MB of public-domain text that the repo does not need to own. eval/ never
reaches the Docker image (the Dockerfile copies only src/ and data/).

A checksum mismatch is reported loudly and exits non-zero, but no test depends
on the corpus being present. See eval/fpcorpus/SOURCES.md.
"""

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

from eval.fpcorpus.manifest import WORKS, _EMPTY_SHA256
from eval.fpcorpus.normalize import normalize

LONGFORM = Path(__file__).resolve().parent / "longform"
_URL = "https://www.gutenberg.org/ebooks/{id}.txt.utf-8"


def path_for(work_id: int) -> Path:
    return LONGFORM / f"pg{work_id}.txt"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def download(work_id: int, timeout: int = 60) -> str:
    with urllib.request.urlopen(_URL.format(id=work_id), timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def verify(work_id: int, text: str) -> tuple[bool, str]:
    """Compare against the recorded digest. Rejects the empty-string digest
    outright: an empty or missing input hashes to a plausible-looking value,
    so a bare equality check cannot tell a match from a no-op."""
    title, _author, _year, expected, chars, _sents = WORKS[work_id]
    got = _sha256(text)
    if got == _EMPTY_SHA256:
        return False, f"{title}: empty input (digest is sha256 of the empty string)"
    if not text.strip():
        return False, f"{title}: normalized text is blank"
    if got != expected:
        return (
            False,
            f"{title}: sha256 {got[:16]} != recorded {expected[:16]} "
            f"({len(text)} chars, recorded {chars}). Gutenberg may have "
            f"regenerated the source. Re-record the manifest and say so in the "
            f"round that reports a number from it.",
        )
    return True, f"{title}: ok ({len(text)} chars)"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verify", action="store_true", help="verify only, no network")
    args = ap.parse_args(argv)

    LONGFORM.mkdir(parents=True, exist_ok=True)
    failures = []
    for work_id in sorted(WORKS):
        dest = path_for(work_id)
        if not dest.exists():
            if args.verify:
                failures.append(f"{work_id}: not fetched")
                continue
            print(f"fetching {work_id} ...", flush=True)
            dest.write_text(normalize(download(work_id)), encoding="utf-8")
        ok, msg = verify(work_id, dest.read_text(encoding="utf-8"))
        print(("  OK   " if ok else "  FAIL ") + msg)
        if not ok:
            failures.append(msg)

    if failures:
        print(f"\n{len(failures)} problem(s).", file=sys.stderr)
        return 1
    print(f"\nAll {len(WORKS)} works verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
