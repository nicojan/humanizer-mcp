/**
 * Client-side TypeScript port of the mcp-humanizer deterministic checker.
 * Ported 1:1 from src/checker/*.py. Consumes the same flattened rule data the
 * Python server loads (data.json), so parity is verified against a golden
 * reference produced by the real server (see parity.mjs).
 */
import DATA from "./data.json";

type Finding = Record<string, unknown>;

interface FlaggedTerm { term: string; severity: string; alternatives: string[]; }
interface RegexStructure {
  id: string; name: string; fix?: string;
  detection: { method: string; pattern: string; confidence?: string };
  document_budget?: number;
  budget_only?: boolean;
}

const HARD_PHRASES: string[] = (DATA as any).hard_phrases;
const REGEX_STRUCTURES: RegexStructure[] = (DATA as any).regex_structures;
const FLAGGED_TERMS: FlaggedTerm[] = (DATA as any).flagged_terms;
const CRED: any = (DATA as any).credibility;
const SELF_REVIEW: string[] = (DATA as any).self_review;

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------
function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** Python str.split() with no args: split on whitespace runs, drop empties. */
function words(s: string): string[] {
  const t = s.trim();
  return t ? t.split(/\s+/) : [];
}
function wordCount(s: string): number {
  return words(s).length;
}

/** Python str.strip(chars): strip the given chars from both ends. */
function stripChars(s: string, chars: string): string {
  let a = 0, b = s.length;
  while (a < b && chars.includes(s[a])) a++;
  while (b > a && chars.includes(s[b - 1])) b--;
  return s.slice(a, b);
}

function mean(xs: number[]): number {
  return xs.reduce((a, b) => a + b, 0) / xs.length;
}
/** statistics.pstdev: population standard deviation. */
function pstdev(xs: number[]): number {
  const m = mean(xs);
  const v = xs.reduce((a, x) => a + (x - m) * (x - m), 0) / xs.length;
  return Math.sqrt(v);
}
/**
 * Python round(x, ndigits): round half to even, on the TRUE value of the
 * double (not on x*10^n, which reintroduces ties, e.g. 6.35*10 === 63.5 in
 * IEEE even though the true value 6.3499999996 rounds down to 6.3). We read the
 * double's faithful 17-significant-digit decimal and round the string, so ties
 * engage only for genuinely dyadic halves (6.25, 6.75, …), matching CPython.
 */
export function pyRound(x: number, ndigits = 1): number {
  if (!Number.isFinite(x)) return x;
  const neg = x < 0;
  const a = Math.abs(x);
  // 30 significant digits: enough to expose whether the true double sits above
  // or below an X.x5 point (the deviation shows around the 16th digit), so a
  // near-tie like 14.65 (double 14.650000000000000355 → rounds up) is not
  // mistaken for an exact tie. Genuine dyadic ties (6.25) stay all-zero after.
  const s = a.toPrecision(30);
  if (s.indexOf("e") !== -1 || s.indexOf("E") !== -1) {
    return Number(a.toFixed(ndigits)) * (neg ? -1 : 1); // extreme magnitudes
  }
  const dot = s.indexOf(".");
  const intPart = dot === -1 ? s : s.slice(0, dot);
  let fracPart = dot === -1 ? "" : s.slice(dot + 1);
  while (fracPart.length <= ndigits) fracPart += "0";
  const keep = fracPart.slice(0, ndigits);
  const next = fracPart.charCodeAt(ndigits) - 48;
  const restNonZero = /[1-9]/.test(fracPart.slice(ndigits + 1));
  const digits = (intPart + keep).split("").map(Number);
  let roundUp: boolean;
  if (next > 5 || (next === 5 && restNonZero)) roundUp = true;
  else if (next < 5) roundUp = false;
  else roundUp = digits[digits.length - 1] % 2 === 1; // exact tie → half to even
  if (roundUp) {
    let i = digits.length - 1;
    while (i >= 0) { digits[i]++; if (digits[i] < 10) break; digits[i] = 0; i--; }
    if (i < 0) digits.unshift(1);
  }
  const all = digits.join("");
  const intLen = all.length - ndigits;
  const resStr = ndigits > 0 ? all.slice(0, intLen) + "." + all.slice(intLen) : all;
  return Number(resStr) * (neg ? -1 : 1);
}

/** Python str(float): integer-valued floats render with a trailing ".0". */
function pyFloatStr(x: number): string {
  return Number.isInteger(x) ? x.toFixed(1) : String(x);
}

function excerpt(text: string, start: number, end: number, radius = 40): string {
  const a = Math.max(0, start - radius);
  const b = Math.min(text.length, end + radius);
  const snippet = text.slice(a, b).replace(/\n/g, " ").trim();
  return (a > 0 ? "…" : "") + snippet + (b < text.length ? "…" : "");
}

interface MatchLite { index: number; end: number; groups: (string | undefined)[]; text: string; }
function finditer(re: RegExp, text: string): MatchLite[] {
  const flags = re.flags.includes("g") ? re.flags : re.flags + "g";
  const g = new RegExp(re.source, flags);
  const out: MatchLite[] = [];
  let m: RegExpExecArray | null;
  while ((m = g.exec(text)) !== null) {
    out.push({ index: m.index, end: m.index + m[0].length, groups: m.slice(1), text: m[0] });
    if (m[0].length === 0) g.lastIndex++;
  }
  return out;
}

/**
 * Translate a Python `re` pattern (compiled server-side with re.IGNORECASE)
 * into a JS RegExp source/flags pair, emulating the two inline-flag forms the
 * data actually uses (see BS-052/BS-053 in banned_structures.json):
 *   - a leading `(?m)`: JS has no inline flag syntax, so it is stripped and
 *     the `m` flag is added to the RegExp instead.
 *   - a scoped `(?-i:...)`: JS has no scoped-flag groups at all. The group is
 *     turned into an ordinary capturing group so the match still succeeds
 *     case-insensitively, and the captured text is re-checked case-sensitively
 *     against the same sub-pattern after the match (see matchPassesCaseGuards).
 * Every other pattern in the data set passes through unchanged.
 */
interface CaseGuard { groupIndex: number; validator: RegExp; }
function translatePattern(pattern: string): { source: string; flags: string; caseGuards: CaseGuard[] } {
  let src = pattern;
  let flags = "gi";
  if (src.startsWith("(?m)")) {
    src = src.slice(4);
    flags += "m";
  }
  const caseGuards: CaseGuard[] = [];
  let out = "";
  let groupIndex = 0;
  let i = 0;
  while (i < src.length) {
    const ch = src[i];
    if (ch === "\\") { out += src.slice(i, i + 2); i += 2; continue; }
    if (ch === "[") {
      // character class: copy verbatim so a `(` inside it is never mistaken
      // for a group open.
      let j = i + 1;
      if (src[j] === "]") j++;
      while (j < src.length && src[j] !== "]") { if (src[j] === "\\") j++; j++; }
      j++;
      out += src.slice(i, j);
      i = j;
      continue;
    }
    if (ch === "(") {
      if (src.startsWith("(?-i:", i)) {
        let depth = 1;
        let j = i + 5;
        const start = j;
        while (j < src.length && depth > 0) {
          const c = src[j];
          if (c === "\\") { j += 2; continue; }
          if (c === "[") {
            j++;
            while (j < src.length && src[j] !== "]") { if (src[j] === "\\") j++; j++; }
            j++;
            continue;
          }
          if (c === "(") depth++;
          else if (c === ")") { depth--; if (depth === 0) break; }
          j++;
        }
        const inner = src.slice(start, j);
        groupIndex += 1;
        caseGuards.push({ groupIndex, validator: new RegExp("^(?:" + inner + ")$") });
        out += "(" + inner + ")";
        i = j + 1;
        continue;
      }
      if (src[i + 1] === "?") {
        // non-capturing group, lookaround, or (already-handled) inline flag.
        out += ch;
        i += 1;
        continue;
      }
      groupIndex += 1;
      out += ch;
      i += 1;
      continue;
    }
    out += ch;
    i += 1;
  }
  return { source: out, flags, caseGuards };
}

function matchPassesCaseGuards(m: MatchLite, caseGuards: CaseGuard[]): boolean {
  for (const guard of caseGuards) {
    const g = m.groups[guard.groupIndex - 1];
    if (g !== undefined && !guard.validator.test(g)) return false;
  }
  return true;
}

// ---------------------------------------------------------------------------
// segmentation (segment.py)
// ---------------------------------------------------------------------------
function splitSentences(text: string): string[] {
  const t = text.trim();
  if (!t) return [];
  return t.split(/(?<=[.!?])\s+/).filter((s) => s.trim());
}

// ---------------------------------------------------------------------------
// emdash.py
// ---------------------------------------------------------------------------
const EMDASH_FIX =
  "Replace with a semicolon, colon, or period (two sentences); or parentheses " +
  "for an aside. Use a comma only when it does not join two independent clauses " +
  "— a comma between independent clauses is a comma splice (AR-003).";

// A line made only of hyphens, pipes, colons and spaces is markdown structure
// (a table separator '|---|---|', a setext underline, a '---' horizontal rule
// or front-matter fence), never an em-dash digraph. Checking the whole line
// keeps a genuine inline 'word--word' flagged while markdown chrome passes.
const STRUCTURAL_LINE = /^[\s\-|:]+$/;

function isMarkdownStructure(text: string, offset: number): boolean {
  const start = text.lastIndexOf("\n", offset - 1) + 1;
  const end = text.indexOf("\n", offset);
  const line = end === -1 ? text.slice(start) : text.slice(start, end);
  return STRUCTURAL_LINE.test(line);
}

function findEmdashes(text: string): Finding[] {
  return finditer(/—|-{2,}/g, text)
    .filter((m) => !isMarkdownStructure(text, m.index))
    .map((m) => ({
      rule: "AR-002",
      type: "em_dash",
      offset: m.index,
      excerpt: excerpt(text, m.index, m.end),
      fix: EMDASH_FIX,
    }));
}

// ---------------------------------------------------------------------------
// phrases.py
// ---------------------------------------------------------------------------
function inflections(word: string): string[] {
  const w = word.toLowerCase();
  if (w.includes(" ") || !/^[a-z]+$/.test(w)) return [w];
  const forms = new Set<string>([w, w + "s", w + "es", w + "ed", w + "ing"]);
  if (w.endsWith("e")) {
    forms.add(w.slice(0, -1) + "ing");
    forms.add(w + "d");
  }
  if (w.endsWith("y")) {
    forms.add(w.slice(0, -1) + "ies");
    forms.add(w.slice(0, -1) + "ied");
  }
  return [...forms];
}

function findPhrases(text: string, phrases: string[]): Array<[string, number]> {
  const low = text.toLowerCase();
  const out: Array<[string, number]> = [];
  for (const p of phrases) {
    const re = new RegExp("\\b" + escapeRegExp(p.toLowerCase()) + "\\b", "g");
    for (const m of finditer(re, low)) out.push([p, m.index]);
  }
  return out;
}

function findFlaggedTerms(text: string, terms: FlaggedTerm[]): Finding[] {
  const low = text.toLowerCase();
  const results: Finding[] = [];
  for (const entry of terms) {
    const locations: number[] = [];
    for (const form of inflections(entry.term)) {
      const re = new RegExp("\\b" + escapeRegExp(form) + "\\b", "g");
      for (const m of finditer(re, low)) locations.push(m.index);
    }
    if (locations.length) {
      results.push({
        type: "flagged_term",
        term: entry.term,
        severity: entry.severity ?? "",
        count: locations.length,
        locations: [...locations].sort((a, b) => a - b),
        alternatives: entry.alternatives ?? [],
      });
    }
  }
  return results;
}

// ---------------------------------------------------------------------------
// punctuation.py
// ---------------------------------------------------------------------------
const STACKED = /[,;:][,;:]|[,;:]\.|\.{4,}/g;
const TERMINAL = /[.!?]+["')\]]*/g;
const MAX_WORDS_PER_SENTENCE = 45;

const SUBJECT_PRONOUNS = new Set(["i", "we", "you", "he", "she", "it", "they"]);
const SUBORDINATORS = new Set([
  "when", "whenever", "while", "if", "unless", "until", "because", "although",
  "though", "since", "as", "after", "before", "whereas", "once", "provided",
  "wherever", "whether", "lest",
]);
const AUX_BE = new Set([
  "is", "was", "are", "were", "am", "be", "been", "being", "will", "would",
  "can", "could", "shall", "should", "may", "might", "must", "do", "does",
  "did", "have", "has", "had", "get", "got", "gets",
]);
const COMMON_VERBS = new Set([
  "go", "went", "gone", "run", "ran", "see", "saw", "say", "said", "make",
  "made", "take", "took", "come", "came", "know", "knew", "think", "thought",
  "feel", "felt", "want", "need", "try", "use", "look", "find", "found",
  "give", "gave", "tell", "told", "keep", "kept", "put", "set", "let",
  "leave", "left", "build", "built", "ship", "send", "sent", "read", "write",
  "wrote", "hear", "heard", "show", "turn", "start", "stop", "help", "hold",
  "held", "bring", "brought", "mean", "meant", "win", "won", "lose", "lost",
  "become", "became", "begin", "began", "grow", "grew", "fall", "fell", "sit",
  "sat", "stand", "stood", "pay", "paid", "buy", "bought", "cut", "hit",
  "quit", "decide", "forget", "forgot",
]);
const WORD_RE = /[A-Za-z']+/g;
const SENTENCE_BREAK = /[.!?]\s+/g;

function isFiniteVerb(word: string): boolean {
  const w = stripChars(word.toLowerCase(), "'");
  if (!w || !/^[a-z]+$/.test(w)) return false;
  if (AUX_BE.has(w) || COMMON_VERBS.has(w)) return true;
  if (w.length > 3 && w.endsWith("ed")) return true;
  if (w.length > 3 && w.endsWith("s") &&
      !(w.endsWith("ss") || w.endsWith("us") || w.endsWith("is") ||
        w.endsWith("ous") || w.endsWith("ics"))) return true;
  return false;
}

function nextNonspace(text: string, idx: number): string {
  while (idx < text.length && text[idx] === " ") idx++;
  return idx < text.length ? text[idx] : "";
}

function spanHasFiniteVerb(span: string): boolean {
  for (const m of finditer(WORD_RE, span)) {
    const wl = stripChars(m.text.toLowerCase(), "'");
    if (AUX_BE.has(wl) || COMMON_VERBS.has(wl)) return true;
    if (wl.length > 3 && wl.endsWith("ed")) return true;
  }
  return false;
}

const COMMA_SPLICE_FIX =
  "Two independent clauses are joined by only a comma. Use a period (two " +
  "sentences), a semicolon, or a colon; or add a coordinating conjunction " +
  "(and, but, so) after the comma. If the splice is a deliberate stylistic " +
  "choice, justify it.";

function findCommaSplices(text: string): Finding[] {
  const out: Finding[] = [];
  for (const m of finditer(/,/g, text)) {
    const ci = m.index;
    const rest = text.slice(ci + 1);
    const toks = finditer(WORD_RE, rest).map(
      (t) => [t.text, ci + 1 + t.index, ci + 1 + t.end] as [string, number, number],
    );
    if (!toks.length) continue;
    if (!SUBJECT_PRONOUNS.has(toks[0][0].toLowerCase())) continue;

    let idx = 1;
    if (idx < toks.length && toks[idx][0].toLowerCase().endsWith("ly")) idx++;
    if (idx >= toks.length) continue;
    const [verbW, , verbEnd] = toks[idx];
    if (!isFiniteVerb(verbW)) continue;

    if (nextNonspace(text, verbEnd) === ",") continue;

    let sentStart = 0;
    for (const sb of finditer(SENTENCE_BREAK, text.slice(0, ci))) sentStart = sb.end;
    const left = text.slice(sentStart, ci);

    const leadM = finditer(WORD_RE, left)[0];
    const leadW = leadM ? leadM.text.toLowerCase() : "";
    if (SUBORDINATORS.has(leadW)) continue;
    if (leadW === "to" || leadW.endsWith("ing") || leadW.endsWith("ed")) continue;
    if (!spanHasFiniteVerb(left)) continue;

    out.push({
      rule: "AR-003",
      type: "comma_splice",
      offset: ci,
      excerpt: excerpt(text, ci, ci + 1),
      fix: COMMA_SPLICE_FIX,
    });
  }
  return out;
}

function findStackedMarks(text: string): Finding[] {
  return finditer(STACKED, text).map((m) => ({
    rule: "AR-003",
    type: "stacked_punctuation",
    offset: m.index,
    excerpt: excerpt(text, m.index, m.end),
    fix: "Remove the stray or duplicate mark. Keep only the single correct internal or terminal punctuation.",
  }));
}

function spanBetweenTerminals(text: string): Array<[number, number]> {
  const boundaries = [0];
  for (const m of finditer(TERMINAL, text)) boundaries.push(m.end);
  if (boundaries[boundaries.length - 1] !== text.length) boundaries.push(text.length);
  const spans: Array<[number, number]> = [];
  for (let i = 0; i < boundaries.length - 1; i++) {
    const a = boundaries[i], b = boundaries[i + 1];
    if (b > a) spans.push([a, b]);
  }
  return spans;
}

function findUnterminated(text: string, maxWords = MAX_WORDS_PER_SENTENCE): Finding[] {
  const out: Finding[] = [];
  const stripped = text.trim();
  if (!stripped) return out;

  const tail = stripChars(stripped, "\"')]}");
  if (tail && !".!?".includes(tail[tail.length - 1])) {
    let lastTermEnd = 0;
    for (const m of finditer(TERMINAL, text)) lastTermEnd = m.end;
    const start = lastTermEnd;
    out.push({
      rule: "AR-003",
      type: "missing_terminal_mark",
      offset: start,
      excerpt: excerpt(text, start, text.length),
      fix: "End with a terminal mark (period, question mark, or exclamation point), or justify as an intentional title/fragment.",
    });
  }

  const seen = new Set<string>();
  for (const [start, end] of spanBetweenTerminals(text)) {
    const segment = text.slice(start, end).trim();
    if (!segment) continue;
    const wc = wordCount(segment);
    if (wc <= maxWords) continue;
    const key = `${start},${end}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({
      rule: "AR-003",
      type: "run_on_without_terminal",
      offset: start,
      excerpt: excerpt(text, start, Math.min(end, start + 200)),
      fix: `This ${wc}-word span has no internal terminal punctuation. Break into shorter sentences with periods, or use a semicolon to join two related independent clauses.`,
    });
  }
  return out;
}

// ---------------------------------------------------------------------------
// structures.py
// ---------------------------------------------------------------------------
const NOMINAL = /\b\w+(?:tion|ment|ance|ence|ity|ness)\s+of\b/gi;
const THIS_OPENER = /^(this|these|it)\b/i;
const TRIAD = /\b[\w'\-]+,\s+[\w'\-]+,?\s+(?:and|or)\s+[\w'\-]+\b/gi;
const TRIAD_WINDOW = 250;
const ABSTRACT_SUBJECTS = new Set([
  "craft", "work", "point", "truth", "reality", "design", "lesson",
  "difference", "answer", "rest", "order", "draft", "part", "thing", "idea",
  "goal", "key", "real",
]);
const COPULA = new Set(["is", "was", "are", "were"]);
const PARA = /\n\s*\n/;
const MAXIM_OPENER = /^(?:the|my|our)\b/i;
const NEG_CLAUSE =
  /^(?:it|they|that)\s+(?:never|does not|doesn't|do not|don't|will not|won't|cannot|can't)\s+([a-z']+)/i;
const ALPHA = /[a-z']+/gi;

interface CompiledStructure {
  id: string; name: string; fix?: string; confidence?: string;
  source: string; flags: string; caseGuards: CaseGuard[];
}
const COMPILED_REGEX_STRUCTURES: CompiledStructure[] = REGEX_STRUCTURES
  .filter((s) => s.detection?.method === "regex")
  .map((s) => {
    const { source, flags, caseGuards } = translatePattern(s.detection.pattern);
    return {
      id: s.id, name: s.name, fix: s.fix, confidence: s.detection.confidence,
      source, flags, caseGuards,
    };
  });

function findRegexStructures(text: string, structures: CompiledStructure[]): Finding[] {
  const out: Finding[] = [];
  for (const s of structures) {
    const re = new RegExp(s.source, s.flags);
    for (const m of finditer(re, text)) {
      if (!matchPassesCaseGuards(m, s.caseGuards)) continue;
      out.push({
        type: "banned_structure",
        id: s.id,
        name: s.name,
        confidence: s.confidence ?? "medium",
        offset: m.index,
        excerpt: excerpt(text, m.index, m.end),
        fix: s.fix ?? "",
      });
    }
  }
  return out;
}

function stem(word: string): string {
  let w = word.toLowerCase();
  const rules: Array<[string, string]> = [
    ["ing", ""], ["ies", "y"], ["es", ""], ["ed", ""], ["s", ""],
  ];
  for (const [suf, repl] of rules) {
    if (w.endsWith(suf) && w.length - suf.length >= 3) {
      return w.slice(0, w.length - suf.length) + repl;
    }
  }
  return w;
}

function copulaMaximCloser(text: string): Finding[] {
  const out: Finding[] = [];
  let cursor = 0;
  for (const para of text.split(PARA)) {
    const start = text.indexOf(para, cursor);
    cursor = start >= 0 ? start + para.length : cursor;
    const sents = splitSentences(para);
    if (!sents.length) continue;
    const last = sents[sents.length - 1].trim();
    const ws = last.split(/\s+/).filter(Boolean);
    if (!(ws.length >= 1 && ws.length <= 10)) continue;
    if (!MAXIM_OPENER.test(last)) continue;
    const toks = ws.map((w) => stripChars(w, ",.;:!?\"'()").toLowerCase());
    let copulaIdx = -1;
    for (let i = 0; i < toks.length; i++) {
      if (COPULA.has(toks[i])) { copulaIdx = i; break; }
    }
    if (copulaIdx === -1) continue;
    const before = new Set(toks.slice(0, copulaIdx));
    let hasAbstract = false;
    for (const t of before) if (ABSTRACT_SUBJECTS.has(t)) { hasAbstract = true; break; }
    if (!hasAbstract) continue;
    if (ws.some((w) => /[0-9]/.test(w))) continue;
    if (ws.slice(1).some((w) => w.length > 0 && w[0] >= "A" && w[0] <= "Z")) continue;
    const sStart = Math.max(text.indexOf(last, Math.max(start, 0)), 0);
    out.push({
      type: "banned_structure",
      id: "BS-018",
      name: "copula_maxim_closer",
      confidence: "low",
      offset: sStart,
      excerpt: excerpt(text, sStart, sStart + last.length),
      fix: "End on the concrete thing, not a distilled lesson about it. If the maxim is earned, attach it to a specific action rather than floating it as a closer.",
    });
  }
  return out;
}

function verbAntithesisPair(text: string): Finding[] {
  const sents = splitSentences(text);
  const out: Finding[] = [];
  if (!sents.length) return out;
  const first = text.indexOf(sents[0]);
  let cursor = first >= 0 ? first + sents[0].length : 0;
  for (let i = 1; i < sents.length; i++) {
    const cur = sents[i].trim();
    const curStart = text.indexOf(cur, cursor);
    if (curStart >= 0) cursor = curStart + cur.length;
    const m = NEG_CLAUSE.exec(cur);
    if (!m) continue;
    const verb = m[1].toLowerCase();
    const prevWords = new Set(
      (sents[i - 1].match(ALPHA) ?? []).map((w) => w.toLowerCase()),
    );
    const st = stem(verb);
    const prevStems = new Set([...prevWords].map((w) => stem(w)));
    const repeated = prevWords.has(verb) || (st.length >= 3 && prevStems.has(st));
    if (!repeated) continue;
    const sStart = Math.max(curStart, 0);
    out.push({
      type: "banned_structure",
      id: "BS-020",
      name: "verb_antithesis_pair",
      confidence: "low",
      offset: sStart,
      excerpt: excerpt(text, sStart, sStart + cur.length),
      fix: "Make the positive claim once. If the boundary matters, state it without mirroring the verb in the negative.",
    });
  }
  return out;
}

function stackedNominalization(text: string): Finding[] {
  const out: Finding[] = [];
  let offset = 0;
  for (const sent of splitSentences(text)) {
    const start = text.indexOf(sent, offset);
    offset = start >= 0 ? start + sent.length : offset;
    if ((sent.match(NOMINAL) ?? []).length >= 3) {
      const s0 = Math.max(start, 0);
      out.push({
        type: "banned_structure",
        id: "BS-012",
        name: "stacked_nominalization",
        confidence: "medium",
        offset: s0,
        excerpt: excerpt(text, s0, s0 + sent.length),
        fix: "Unpack the nouns back into verbs; name the agent.",
      });
    }
  }
  return out;
}

function thisChain(text: string): Finding[] {
  const sents = splitSentences(text);
  const out: Finding[] = [];
  let run = 0, runStartIdx = 0;
  for (let i = 0; i < sents.length; i++) {
    if (THIS_OPENER.test(sents[i].trim())) {
      if (run === 0) runStartIdx = i;
      run += 1;
    } else {
      run = 0;
    }
    if (run === 3) {
      const first = sents[runStartIdx];
      const start = Math.max(text.indexOf(first), 0);
      out.push({
        type: "banned_structure",
        id: "BS-009",
        name: "this_chain",
        confidence: "medium",
        offset: start,
        excerpt: excerpt(text, start, start + first.length),
        fix: "Leave causal links implicit; vary sentence openings.",
      });
    }
  }
  return out;
}

function findHeuristicStructures(text: string): Finding[] {
  return [
    ...stackedNominalization(text),
    ...thisChain(text),
    ...copulaMaximCloser(text),
    ...verbAntithesisPair(text),
  ];
}

function findRuleOfThreeDensity(text: string): Finding[] {
  const starts = finditer(TRIAD, text).map((m) => m.index);
  if (starts.length < 2) return [];
  const out: Finding[] = [];
  let cluster = [starts[0]];
  const flush = (group: number[]) => {
    if (group.length < 2) return;
    const end = Math.min(text.length, group[group.length - 1] + 40);
    out.push({
      type: "rule_of_three_density",
      confidence: "low",
      count: group.length,
      offset: group[0],
      excerpt: excerpt(text, group[0], end),
      fix: "Two or more parallel three-item lists sit close together, a strong rule-of-three tell. Vary one: drop to two items, expand to four, or fold the items into a sentence with commentary between them.",
    });
  };
  for (const s of starts.slice(1)) {
    if (s - cluster[cluster.length - 1] <= TRIAD_WINDOW) cluster.push(s);
    else { flush(cluster); cluster = [s]; }
  }
  flush(cluster);
  return out;
}

// ---------------------------------------------------------------------------
// budgets.py
// ---------------------------------------------------------------------------
const BUDGETS: Record<string, number> = {};
const BUDGET_NAMES: Record<string, string> = {};
const BUDGET_ONLY = new Set<string>();
for (const s of REGEX_STRUCTURES) {
  if (s.document_budget) {
    BUDGETS[s.id] = s.document_budget;
    BUDGET_NAMES[s.id] = s.name ?? s.id;
    if (s.budget_only) BUDGET_ONLY.add(s.id);
  }
}

/**
 * One finding per budgeted rule that appears more often than its budget.
 * `findings` is the already-assembled must_clear list, so this counts what
 * the detectors actually reported rather than re-running them. For a rule in
 * budgetOnly the instances are dropped from the report by the caller, so the
 * overrun carries their excerpts instead: the writer still needs to find them.
 */
function findBudgetOverruns(
  findings: Finding[],
  budgets: Record<string, number>,
  names: Record<string, string>,
  budgetOnly: Set<string>,
): Finding[] {
  const counts = new Map<string, number>();
  for (const f of findings) {
    const id = (f as any).id;
    if (id && id in budgets) counts.set(id, (counts.get(id) ?? 0) + 1);
  }
  const out: Finding[] = [];
  for (const ruleId of [...counts.keys()].sort()) {
    const count = counts.get(ruleId)!;
    const budget = budgets[ruleId];
    if (count <= budget) continue;
    const name = names[ruleId] ?? ruleId;
    const finding: any = {
      type: "document_budget",
      id: ruleId,
      name,
      count,
      budget,
      detail:
        `${name} appears ${count} times in the text supplied; the budget for ` +
        `the whole piece is ${budget}. A repeated rhetorical shape is the ` +
        "durable tell, not any single use.",
      fix:
        "Keep the strongest instance and rewrite the rest. Counted only " +
        "within this call, so run the final check on the assembled document " +
        "rather than section by section " +
        "(caveats.per_section_checks_miss_document_budgets).",
    };
    if (budgetOnly.has(ruleId)) {
      finding.excerpts = findings
        .filter((f: any) => f.id === ruleId)
        .map((f: any) => f.excerpt ?? "");
    }
    out.push(finding);
  }
  return out;
}

// ---------------------------------------------------------------------------
// insistence.py
// ---------------------------------------------------------------------------
const CRED_WORD = /[A-Za-z]+(?:[-'][A-Za-z]+)*/g;
const REAL_PHRASES = /real[-\s]?time|real[-\s]?world|real\s+estate|real\s+number|in\s+real\s+terms/gi;
const SENT_START_END = /(?:^|[.!?]\s+)$/;

function spansOf(re: RegExp, text: string): Array<[number, number]> {
  return finditer(re, text).map((m) => [m.index, m.end] as [number, number]);
}
function quotedSpans(text: string): Array<[number, number]> {
  return spansOf(/"[^"]*"|“[^”]*”/g, text);
}
function within(idx: number, spans: Array<[number, number]>): boolean {
  return spans.some(([a, b]) => a <= idx && idx < b);
}

function findCredibilityInsistence(text: string, config: any): Finding[] {
  const tokens = new Set<string>((config.tokens ?? []).map((t: string) => t.toLowerCase()));
  if (!tokens.size) return [];
  const sameTokenMin = config.same_token_min ?? 3;
  const ratePerWords = config.rate_per_words ?? 2 / 400;

  const quoted = quotedSpans(text);
  const realPhrases = spansOf(REAL_PHRASES, text);

  const counts = new Map<string, number>();
  const firstOffset = new Map<string, number>();
  let actuallyFreebieUsed = false;

  for (const m of finditer(CRED_WORD, text)) {
    const w = m.text.toLowerCase();
    if (!tokens.has(w)) continue;
    const i = m.index;
    if (within(i, quoted)) continue;
    if (w === "real" && within(i, realPhrases)) continue;
    if (w === "really") {
      let j = m.end;
      while (j < text.length && text[j] === " ") j++;
      if (j < text.length && text[j] === "?") continue;
    }
    if (w === "actually" && !actuallyFreebieUsed && SENT_START_END.test(text.slice(0, i))) {
      actuallyFreebieUsed = true;
      continue;
    }
    counts.set(w, (counts.get(w) ?? 0) + 1);
    if (!firstOffset.has(w)) firstOffset.set(w, i);
  }

  let total = 0;
  for (const v of counts.values()) total += v;
  if (total === 0) return [];
  const wc = wordCount(text);
  // argmax with first-seen (insertion order) tie-break, matching Python max().
  let dominant = "";
  let dominantCount = -1;
  for (const [k, v] of counts) {
    if (v > dominantCount) { dominant = k; dominantCount = v; }
  }
  const overSameToken = counts.get(dominant)! >= sameTokenMin;
  const overRate = total >= sameTokenMin && wc > 0 && total / wc > ratePerWords;
  if (!(overSameToken || overRate)) return [];

  const off = firstOffset.get(dominant)!;
  const dc = counts.get(dominant)!;
  return [{
    type: "credibility_insistence",
    confidence: "low",
    count: total,
    dominant_token: dominant,
    dominant_count: dc,
    offset: off,
    excerpt: excerpt(text, off, off + dominant.length),
    fix:
      "You are repeatedly insisting the work is real/actual/genuine " +
      `('${dominant}' x${dc}; ${total} across the set). A human rarely needs ` +
      "to vouch that their own account is real. Cut the assertions and let the " +
      "specifics carry the credibility; keep at most one if a contrast genuinely needs it.",
  }];
}

// ---------------------------------------------------------------------------
// metrics.py
// ---------------------------------------------------------------------------
const TARGETS: Record<string, number> = {
  prose: 6.0, general_prose: 6.0, general: 6.0, academic: 5.0,
  marketing: 7.0, tech: 4.0, technical: 4.0,
};
const SEGMENT_MEAN_SPREAD_MAX = 2.5;
const SEGMENT_INTERNAL_STDEV_MAX = 3.0;
const MIN_SENTENCES_PER_SEGMENT = 3;
const MIN_SEGMENTS = 3;
const PARA_SPLIT = /\n\s*\n/;

// Content types whose caller declares the input is labels, worksheet cells or
// notes, where sentence-length variance is undefined or deliberately flat
// (caveats.metrics_do_not_apply_to_label_text). An explicit opt-in, never
// inferred from the text.
const SHORT_COPY_TYPES = new Set(["label", "labels", "notes"]);

function lengthMetricsApply(contentType: string | null | undefined): boolean {
  return !SHORT_COPY_TYPES.has((contentType ?? "prose").toLowerCase());
}

function targetStdev(contentType: string | null | undefined): number {
  return TARGETS[(contentType ?? "prose").toLowerCase()] ?? 6.0;
}

function burstiness(text: string, target: number): any {
  const lengths = splitSentences(text).map((s) => wordCount(s));
  if (lengths.length < 2) {
    return {
      sentence_count: lengths.length,
      length_mean: lengths.length ? lengths[0] : 0.0,
      length_stdev: 0.0,
      min: lengths.length ? Math.min(...lengths) : 0,
      max: lengths.length ? Math.max(...lengths) : 0,
      burstiness_target_stdev: target,
      burstiness_flag: false,
    };
  }
  const sd = pstdev(lengths);
  return {
    sentence_count: lengths.length,
    length_mean: pyRound(mean(lengths), 1),
    length_stdev: pyRound(sd, 1),
    min: Math.min(...lengths),
    max: Math.max(...lengths),
    burstiness_target_stdev: target,
    burstiness_flag: sd < target,
  };
}

function segmentUniformity(text: string): any {
  const paragraphs = text.trim().split(PARA_SPLIT).filter((p) => p.trim());
  const segments: Array<[number, number]> = [];
  for (const para of paragraphs) {
    const sentences = splitSentences(para);
    if (sentences.length < MIN_SENTENCES_PER_SEGMENT) continue;
    const lengths = sentences.map((s) => wordCount(s));
    segments.push([mean(lengths), pstdev(lengths)]);
  }
  if (segments.length < MIN_SEGMENTS) {
    return { segment_count: segments.length, uniformity_flag: false };
  }
  const means = segments.map(([m]) => m);
  const spread = Math.max(...means) - Math.min(...means);
  const maxInternal = Math.max(...segments.map(([, sd]) => sd));
  const flag = spread < SEGMENT_MEAN_SPREAD_MAX && maxInternal < SEGMENT_INTERNAL_STDEV_MAX;
  return {
    segment_count: segments.length,
    segment_mean_lengths: means.map((m) => pyRound(m, 1)),
    segment_mean_spread: pyRound(spread, 1),
    max_internal_stdev: pyRound(maxInternal, 1),
    uniformity_flag: flag,
  };
}

// ---------------------------------------------------------------------------
// report.py + __init__.py orchestration
// ---------------------------------------------------------------------------
const NOTE =
  "prohibitions_clear means no hard prohibitions remain. It does NOT mean humanization is complete.";
const NEXT_ACTION =
  "Resolve every hard_violation (required). Rewrite or justify each must_clear " +
  "item, and re-run humanizer_check_text until prohibitions_clear is true. Then " +
  "run the self-review rubric (manual_review) against your own draft — rate each " +
  "item and rewrite every weak spot — before returning.";

export interface Report {
  prohibitions_clear: boolean;
  note: string;
  hard_violations: Finding[];
  must_clear: Finding[];
  metrics: any;
  manual_review: string[];
  next_action: string;
}

export function runChecks(text: string, contentType?: string | null): Report {
  const hard: Finding[] = findEmdashes(text);
  hard.push(...findStackedMarks(text));
  for (const [phrase, off] of findPhrases(text, HARD_PHRASES)) {
    hard.push({
      rule: "banned_structure",
      type: "fixed_phrase",
      phrase,
      offset: off,
      excerpt: excerpt(text, off, off + phrase.length),
      fix: "Cut the phrase; state the point directly.",
    });
  }

  const rawMust: Finding[] = [];
  rawMust.push(...findUnterminated(text));
  rawMust.push(...findCommaSplices(text));
  rawMust.push(...findFlaggedTerms(text, FLAGGED_TERMS));
  rawMust.push(...findRegexStructures(text, COMPILED_REGEX_STRUCTURES));
  rawMust.push(...findHeuristicStructures(text));
  rawMust.push(...findRuleOfThreeDensity(text));
  rawMust.push(...findCredibilityInsistence(text, CRED));

  const overruns = findBudgetOverruns(rawMust, BUDGETS, BUDGET_NAMES, BUDGET_ONLY);
  const must: Finding[] = rawMust.filter((f: any) => !(f.id && BUDGET_ONLY.has(f.id)));
  must.push(...overruns);

  // Under content_type "label"/"notes" the numbers are still reported, but the
  // flags are cleared so no consumer reads them as a failure.
  const applies = lengthMetricsApply(contentType);
  const rawMetrics = burstiness(text, targetStdev(contentType));
  const metrics: any = {
    ...rawMetrics,
    burstiness_flag: applies && rawMetrics.burstiness_flag,
    length_metrics_apply: applies,
  };
  if (metrics.burstiness_flag) {
    must.push({
      type: "burstiness",
      detail: `low sentence-length variance (stdev ${pyFloatStr(metrics.length_stdev)} < target ${pyFloatStr(metrics.burstiness_target_stdev)})`,
      fix: "Vary sentence lengths: mix short and long, add a fragment or a longer multi-clause sentence.",
    });
  }

  const rawSegments = segmentUniformity(text);
  const segments = { ...rawSegments, uniformity_flag: applies && rawSegments.uniformity_flag };
  metrics.segment_variation = segments;
  if (segments.uniformity_flag) {
    must.push({
      type: "segment_uniformity",
      detail: `style is flat across ${segments.segment_count} sections (mean sentence-length spread ${pyFloatStr(segments.segment_mean_spread)} words)`,
      fix: "Humans modulate style between a document's sections; LLMs hold one flat fingerprint throughout. Make one section terse and another more flowing, varying rhythm and sentence length section to section. Or justify if the format genuinely requires uniform sections.",
    });
  }

  return {
    prohibitions_clear: hard.length === 0,
    note: NOTE,
    hard_violations: hard,
    must_clear: must,
    metrics,
    manual_review: SELF_REVIEW,
    next_action: NEXT_ACTION,
  };
}

// ---------------------------------------------------------------------------
// UI helpers: compute the inline highlight span for a finding, using the exact
// same patterns the detectors use. Document-level findings (rule-of-three,
// credibility, burstiness, segment uniformity, heuristic structures) return
// null and are shown in the findings list without an inline mark.
// ---------------------------------------------------------------------------
export function spanOf(text: string, f: any): [number, number] | null {
  switch (f.type) {
    case "em_dash":
      return [f.offset, f.offset + (text.substr(f.offset, 2) === "--" ? 2 : 1)];
    case "fixed_phrase":
      return [f.offset, f.offset + String(f.phrase).length];
    case "comma_splice":
      return [f.offset, f.offset + 1];
    case "stacked_punctuation": {
      const m = /^([,;:][,;:]|[,;:]\.|\.{4,})/.exec(text.slice(f.offset));
      return [f.offset, f.offset + (m ? m[0].length : 1)];
    }
    case "banned_structure": {
      if (!f.id) return null; // heuristic BS-009/012/018/020 → list only
      const s = COMPILED_REGEX_STRUCTURES.find((x) => x.id === f.id);
      if (!s) return null;
      const re = new RegExp(s.source, s.flags);
      let m: RegExpExecArray | null;
      while ((m = re.exec(text)) !== null) {
        if (m.index === f.offset) return [f.offset, f.offset + m[0].length];
        if (m[0].length === 0) re.lastIndex++;
      }
      return null;
    }
    default:
      return null;
  }
}

/** Length of the flagged-term form matched at a given location (longest form). */
export function flaggedFormLen(text: string, term: string, loc: number): number {
  const low = text.toLowerCase();
  let best = 0;
  for (const form of inflections(term)) {
    if (low.startsWith(form, loc) && form.length > best) best = form.length;
  }
  return best || term.length;
}
