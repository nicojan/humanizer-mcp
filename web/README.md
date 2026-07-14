# web/ : client-side checker (browser port)

A TypeScript port of the deterministic checker in `../src/checker/`, compiled to
run entirely in the browser. It powers the live demo (`../index.html`): edit
text and every AI-writing tell the rules can catch is flagged on each keystroke,
with no server and no network.

## Parity with the Python server

The port is not a re-interpretation; it is verified to produce the same findings
as the Python `run_checks`. `dump.py` runs the real checker over a battery of
texts (crafted edge cases plus a corpus of AI-written samples) and writes the
results to `golden.json`. `parity.mjs` runs the compiled port over the same
battery and diffs every finding, offset, count, metric, and fix string. Current
status: **65/65 texts match exactly.**

The same run also dumps the flattened rule data (`src/data.json`) straight from
the server's loaders, so the port consumes the identical banned phrases, flagged
terms, and structure patterns. There is no second copy of the rules to drift.

## Layout

| File | Role |
|---|---|
| `src/checker.ts` | the port (detectors + `runChecks`) |
| `src/data.json` | flattened rule data, dumped from the server loaders |
| `ui-template.html` | the demo page (UI and styles), with placeholders for the bundle and fonts |
| `fonts-embed.css` | IBM Plex Serif/Mono, base64-embedded so the page needs no font CDN |
| `build.mjs` | bundles the port and inlines it and the fonts into `../index.html` |
| `dump.py` | regenerates `src/data.json` and `golden.json` from the Python checker |
| `parity.mjs` | runs the port over `golden.json` and diffs against the server |
| `golden.json` | parity ground truth |

## Reproduce

```bash
# from web/, with the parent server's Python deps available
python3 dump.py     # regenerate src/data.json + golden.json from the Python checker
node build.mjs      # build ../index.html and the parity bundle
node parity.mjs     # verify 65/65 against the Python checker
```

## Parity scope

Parity is verified byte-for-byte on ASCII English text (plus the `pyRound`
cases below). Two edges differ from the Python server, both from JavaScript's
regex and string model:

- **Astral characters** (emoji and other non-BMP code points) count as two
  UTF-16 units in JS but one code point in Python, so a reported offset can
  shift by one after such a character.
- **Non-ASCII word characters** (accented letters) are not matched by JS
  `\w` / `\b` or the ASCII case/digit guards, where Python's `re` is
  Unicode-aware, so a word-boundary match can start one character over.

Both affect only the comparison against the server. The demo itself is
all-JavaScript and internally consistent, so its inline highlights land
correctly on any input.

`pyRound` reproduces CPython's `round(x, 1)` (round half to even, on the true
value of the double). `parity.mjs` checks it against Python over every `.x5`
step, the dyadic eighths, and a set of irrational values.
