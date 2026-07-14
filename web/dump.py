"""Dump the real Python checker's flattened data + a golden reference battery.
Run with the repo venv and PYTHONPATH=<repo root>."""

import json
import os
import sys

# web/ lives inside the mcp-humanizer repo; the repo root is one level up.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
os.environ.setdefault("HUMANIZER_DATA_DIR", os.path.join(REPO, "data"))

from src.checker import run_checks
from src.checker.loader import (
    load_credibility_insistence,
    load_flagged_terms,
    load_hard_phrases,
    load_regex_structures,
    load_self_review,
)

HERE = os.path.dirname(os.path.abspath(__file__))

# --- 1. Flattened data the detectors consume (identical to server) -----------
data = {
    "hard_phrases": load_hard_phrases(),
    "regex_structures": load_regex_structures(),
    "flagged_terms": load_flagged_terms(),
    "credibility": load_credibility_insistence(),
    "self_review": load_self_review(),
}
with open(os.path.join(HERE, "src", "data.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# --- 2. Battery: crafted edge cases exercising every detector ----------------
crafted = [
    ("clean_prose", "prose",
     "I spent the morning fixing the fence. The wood had warped over winter, so "
     "two boards no longer met. My neighbour lent me a plane and we shaved them "
     "down until they sat flush. It took longer than I expected, and my hands "
     "ached by noon."),
    ("marketing_sample", "marketing",
     "In today's fast-paced world, our innovative platform leverages cutting-edge "
     "AI to deliver seamless solutions. It's not just a tool — it's a revolution. "
     "We are committed to transparency, authenticity, and genuine results. Whether "
     "you are a scrappy startup or a global enterprise, our platform helps you "
     "streamline workflows, boost productivity, and unlock your team's full "
     "potential. The best part? It is completely free to start."),
    ("emdash_digraph", "prose", "The plan was simple -- we shipped it Friday."),
    ("stacked_marks", "prose", "He arrived late,. then left early;. nobody minded."),
    ("abbrev_ok", "prose", "We tested e.g., Chrome, Firefox, etc., and it worked. All good."),
    ("comma_splice", "prose", "The results were clear, we shipped the release that night."),
    ("comma_splice_adverb", "prose", "It rained hard, we quickly left the field."),
    ("subordinator_ok", "prose", "When it rains, it pours across the whole valley."),
    ("parenthetical_ok", "prose", "The plan, it seemed, would work out fine in the end."),
    ("run_on", "prose",
     "We started early and drove north past the lake and then the road turned to "
     "gravel and the signal dropped and nobody had a map and we kept going anyway "
     "until the sun set behind the ridge and we finally found the cabin door"),
    ("flagged_terms_inflect", "prose",
     "The team leverages the platform daily. It leveraged the same approach last "
     "year, and keeps delving into seamless, innovative tactics."),
    ("this_chain", "prose",
     "This changes everything. This is why we win. This matters to every user we "
     "have. The team agreed."),
    ("stacked_nominalization", "prose",
     "The implementation of the automation of the reduction of complexity remains a "
     "priority for the organization this quarter."),
    ("copula_maxim", "prose",
     "We rebuilt the onboarding from scratch over six weeks with the whole team.\n\n"
     "The craft is mostly restraint."),
    ("verb_antithesis", "prose",
     "The system carries the busywork for you. It never carries the judgment."),
    ("rule_of_three", "marketing",
     "We design, build, and ship. We plan, test, and measure. Our tools are fast, "
     "clean, and simple."),
    ("credibility_insistence", "prose",
     "This is a real account of a real project with real stakes. The genuine, "
     "authentic truth is that it actually happened, really."),
    ("negation_flip", "prose", "It is not about the tool. It is about the habit."),
    ("rarely_flip", "prose", "Good writing rarely announces itself. It simply works."),
    ("wh_cleft", "prose", "What matters is not the plan. What matters is the follow-through."),
    ("meta_label", "prose", "In brief.\n\nWe cut the scope and shipped the core."),
    ("validation_reassurance", "prose", "You're not alone. Many teams hit this exact wall."),
    ("vague_authority", "prose", "Studies show that readers skim. Experts agree that clarity wins."),
    ("question_fragment", "prose", "The best part? It ships today."),
    ("noun_participle", "prose", "The homepage, reimagined."),
    ("uniform_segments", "academic",
     "The first section covers the setup. It explains the basic parameters. It "
     "lists the core assumptions clearly.\n\n"
     "The second section covers the method. It walks through each measured step. "
     "It states the sampling frame plainly.\n\n"
     "The third section covers results. It reports the primary outcome first. It "
     "notes the two secondary findings."),
    ("empty_ish", "prose", "Ok."),
    ("single_sentence", "prose", "This is a single clean sentence with no findings at all."),
    ("smart_quotes_real", "prose",
     "“This is real,” she said. The real story is that real people did real work."),
    # --- adversarial: comma-splice guards ---
    ("intro_element_ok", "prose", "However, it was late when we finally reached the cabin."),
    ("year_intro_ok", "prose", "In 2020, it changed the way the whole team worked."),
    ("nonfinite_to_ok", "prose", "To be fair, we shipped it on time and under budget."),
    ("participial_ok", "prose", "Having finished the report, we left the office early that night."),
    ("real_splice_they", "prose", "She left early, they stayed until the very end of the night."),
    ("real_splice_we", "prose", "We shipped the fix, it worked on the very first try."),
    ("compound_but_ok", "prose", "We tried the new approach, but it failed on the edge cases."),
    # --- adversarial: credibility exclusions ---
    ("actually_freebie", "prose", "Actually, it works now. This is actual, actual proof of the actual result we got."),
    ("really_interrogative", "prose", "Is this really the plan? Really? We need a genuine, genuine, genuine rethink now."),
    ("quoted_real_excluded", "prose", "\"real real real real\" was all the short note ever said."),
    # --- adversarial: each regex banned-structure in isolation ---
    ("bs004_puffery", "prose", "The launch, marking a pivotal moment for the team, went off smoothly."),
    ("bs005_participle", "prose", "Sales doubled last quarter, underscoring the strength of the plan."),
    ("bs007_despite", "prose", "Despite strong revenue, the company faces real challenges ahead this year."),
    ("bs010_that_clause", "prose", "That the design works is obvious to everyone on the team here."),
    ("bs011_x_not_y", "prose", "We chose speed, not polish, for the very first release."),
    ("bs016_meta_framing", "prose", "The point of the exercise is to find the seams early on."),
    ("bs017_disclaimer", "prose", "I will not pretend this is easy. But the payoff is worth the effort."),
    ("bs019_locative", "prose", "The kitchen is where the whole family gathers every single evening."),
    # --- adversarial: round-half-to-even tie (mean 4.25) ---
    ("round_tie_425", "tech",
     "Alpha beta gamma four. Alpha beta gamma four. Alpha beta gamma four. Alpha beta gamma four five."),
    # --- adversarial: long run-on (>45 words, no internal terminal) ---
    ("long_run_on", "prose",
     "We packed the truck before dawn and drove north along the coast road past "
     "the sleeping towns and the shuttered diners and the long grey beaches where "
     "nobody walked and the fog sat low over the water and we talked about nothing "
     "in particular and let the miles go by until the tank ran low and we pulled "
     "off at a station that time forgot"),
]

# --- 3. Real text: the eval corpus (human + AI) ------------------------------
battery = []
for name, ct, text in crafted:
    battery.append({"name": name, "content_type": ct, "text": text})

corpus_root = os.path.join(REPO, "eval", "corpus")
for pile in ("ai",):  # human pile removed from public repo; ai pile is present
    d = os.path.join(corpus_root, pile)
    if os.path.isdir(d):
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".txt"):
                with open(os.path.join(d, fn), encoding="utf-8") as fh:
                    battery.append({
                        "name": f"{pile}/{fn}",
                        "content_type": "prose",
                        "text": fh.read().strip(),
                    })

golden = []
for item in battery:
    report = run_checks(item["text"], item["content_type"])
    golden.append({**item, "report": report})

with open(os.path.join(HERE, "golden.json"), "w", encoding="utf-8") as f:
    json.dump(golden, f, ensure_ascii=False, indent=2)

# --- 4. pyRound parity cases: every .x5 near-tie, dyadic eighths, irrationals -
import math
round_vals = [i / 20.0 for i in range(0, 500)]          # 0.00..24.95 in .05 steps
round_vals += [i / 8.0 for i in range(0, 200)]          # dyadic eighths (true ties)
round_vals += [math.sqrt(i) for i in range(1, 80)]      # stdev-like irrationals
round_cases = [{"x": x, "py": round(x, 1)} for x in round_vals]
with open(os.path.join(HERE, "round_cases.json"), "w", encoding="utf-8") as f:
    json.dump(round_cases, f)
print(f"round_cases.json: {len(round_cases)} values")

print(f"data.json: {len(data['hard_phrases'])} hard phrases, "
      f"{len(data['regex_structures'])} regex structures, "
      f"{len(data['flagged_terms'])} flagged terms")
print(f"golden.json: {len(golden)} test texts")
# Quick regex-syntax scan for Python-only features that break in JS.
import re as _re
suspect = []
for s in data["regex_structures"]:
    pat = s["detection"]["pattern"]
    for feat in ("(?P<", "(?P=", "\\g<", "(?#"):
        if feat in pat:
            suspect.append((s["id"], feat, pat))
    # possessive quantifiers / atomic groups
    if _re.search(r"[*+?}]\+", pat) or "(?>" in pat:
        suspect.append((s["id"], "possessive/atomic", pat))
print("regex compat suspects:", suspect if suspect else "none")
