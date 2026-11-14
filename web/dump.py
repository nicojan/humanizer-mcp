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
    load_terms_of_art,
)

HERE = os.path.dirname(os.path.abspath(__file__))

# --- 1. Flattened data the detectors consume (identical to server) -----------
data = {
    "hard_phrases": load_hard_phrases(),
    "regex_structures": load_regex_structures(),
    "flagged_terms": load_flagged_terms(),
    "credibility": load_credibility_insistence(),
    # The runtime (lenient) loader's objects. `history` is maintainer-only and
    # never served, so it is left out of the browser bundle.
    "self_review": [
        {k: v for k, v in item.items() if k != "history"} for item in load_self_review()
    ],
    "terms_of_art": load_terms_of_art(),
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
    ("rule_of_three_stacked_prose", "prose",
     "We built it for speed, scale, and safety. The team values trust, focus, and craft. Our clients get clarity, momentum, and results. The office has light, space, and quiet."),
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
    ("bs031_carry", "prose", "The layout carries the weight of the argument every single time."),
    ("bs031_literal_ok", "prose", "The truck carries the load to the depot before the sun comes up."),
    ("bs032_honestly", "prose", "Honestly? Most people never follow up on any of it."),
    ("bs033_quiet", "prose", "She led with quiet confidence while the team quietly reshaped the roadmap."),
    ("bs033_quiet_ok", "prose", "It was a quiet room with one window and she closed the door quietly."),
    ("bs034_balance", "prose", "While automation has benefits, it also carries risks for the whole team."),
    ("bs035_crossref", "prose", "As mentioned above, the queue is the real bottleneck in the pipeline."),
    ("bs036_sink_in", "prose", "Only three of the twelve shipped. Let that sink in for a moment."),
    ("bs037_kicker", "prose", "Here's the kicker: the part most people miss is the review step."),
    # --- adversarial: markdown structure is not an em-dash digraph (AR-002) ---
    ("md_table_no_emdash", "prose",
     "The table below lists them.\n\n| Source | Used for |\n|---|---|\n| Forbes | BS-032 |\n\nThat is the whole set."),
    ("md_rule_no_emdash", "prose",
     "First the intro paragraph goes here.\n\n---\n\nThen the next section starts."),
    ("md_inline_digraph_flagged", "prose", "The build failed--again, and nobody had any idea why."),
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
    # --- adversarial: each regex banned-structure added since 2026-08-06 ---
    ("bs038_appended_wh_label", "prose", "Method, and why this one worked better than the rest."),
    ("bs038_ok_ordinary_clause", "prose", "He explained the delay, and why it mattered to the whole team."),
    ("bs039_not_but_fragment", "prose", "Not because it was easy, but because it was right for the team."),
    ("bs039_ok_mid_sentence", "prose", "He did not go to the store, but to the park instead that day."),
    ("bs040_artifact_carry", "prose", "The deck carries one still image from the original pitch we made."),
    ("bs040_ok_literal_frame", "prose", "The frame carries the roof of the old barn without any trouble."),
    ("bs041_stale_figure", "prose", "The new pricing page really moves the needle for the whole team."),
    ("bs041_ok_time_of_day", "prose", "We wrapped the review at the end of the day and went home."),
    ("bs042_candour_disclaimer", "prose", "The redesign took nine months, and I'm not going to pretend that was the plan."),
    ("bs042_ok_sentence_initial", "prose", "I'm not going to pretend I understand the tax code at all."),
    ("bs043_copula_avoidance", "prose", "The report serves as a guide for every new hire on the team."),
    ("bs043_ok_role_object", "prose", "She stood as the Labour candidate in the general election that year."),
    ("bs044_significance_predicate", "prose", "The ceremony represents a profound turning point for the whole community."),
    ("bs044_ok_literal", "prose", "The graph represents the data collected from three separate sites."),
    ("bs045_signposted_conclusion", "prose", "The pilot ran for six weeks. In conclusion, the team should keep the new schedule."),
    ("bs046_staccato_negation", "prose", "Not a bug. Not a feature. It is simply how the system behaves."),
    ("bs046_ok_ordinary_emphasis", "prose", "Not now. Not ever. She had made up her mind about it."),
    ("bs047_analogy_invitation", "prose", "Think of it like a garden that needs tending every single week."),
    ("bs048_structure_announcement", "prose", "Let's break this down into three parts before we go any further."),
    ("bs048_ok_let_be_honest", "prose", "Let's be honest, the deadline was always going to be tight."),
    ("bs049_boast_collocation", "prose", "The brochure boasts a rooftop pool and a private screening room."),
    ("bs050_elevate_collocation", "prose", "The new signage will elevate your lobby into something guests remember."),
    ("bs050_ok_literal_elevate", "prose", "The engineers elevated the track above the river to stop the flooding."),
    ("bs051_landscape_metaphor", "prose", "The competitive landscape has shifted dramatically over the last year."),
    ("bs052_time_noun_as_agent", "prose", "Busy season eats the Fridays I used to spend at the club."),
    ("bs052_ok_literal_season", "prose", "The winter killed the roses we planted along the back fence."),
    ("bs053_clipped_retention_verdict", "prose", "The Scouts books and the tutoring stay. Everything else goes."),
    ("bs053_ok_literal_car", "prose", "The car stays in the garage until the snow tires go on."),
    # the (?-i:[A-Z]) capital check and the case-insensitive exclusions
    ("bs053_list_item", "prose", "- Tutoring stays.\n- The gym goes."),
    ("bs053_ok_all_caps_pronoun", "prose", "HE STAYS. NOTHING REMAINS. No one stays."),
    ("bs053_ok_title_name", "prose", "Mr. Darcy stays. Please stay."),
    ("bs053_ok_lowercase_start", "prose", "then tutoring stays. and the gym goes."),
    ("bs054_deictic_stance_closer", "prose", "Seven to eight hours of sleep, and I want to keep it there."),
    ("bs054_ok_no_number", "prose", "The kitchen is tidy, and I want to keep it that way."),
    ("bs055_time_back_refrain_single", "prose", "I get my Fridays back in May when the season ends."),
    ("bs055_time_back_refrain_budget", "prose",
     "I get my Fridays back in May. I get my evenings back too. I even get my "
     "weekends back once the tournament wraps up for good."),
    # --- 2026-10-30 research round (BS-056..064, BS-030 extension) ---
    ("bs056_graded_contrast_like", "prose", "Good onboarding is less like a lecture and more like an apprenticeship."),
    ("bs056_ok_cross_sentence", "prose", "Nothing is less like home. More like a hotel, really."),
    ("bs057_about_single_silent", "prose", "I care less about the price and more about the fit of the jacket."),
    ("bs057_about_budget", "prose", "The job is less about speed and more about trust. Hiring is less about pedigree and more about range."),
    ("bs058_chatbot_residue", "prose", "Certainly! Here is a revised summary of the project. As an AI language model, I cannot browse."),
    ("bs058_ok_chat_courtesy", "prose", "Sure! Here's the Zoom link for tomorrow. They read as an AI tell, and I hope this helps."),
    ("bs059_fiction_stock", "prose", "Her voice was barely above a whisper, her heart hammering against her ribs. Elara waited."),
    ("bs059_ok_memoir_and_critic", "prose", "I woke at 3 a.m. with my heart pounding in my chest. Pauline Kael hated it."),
    ("bs060_emotion_inventory", "prose", "She felt a mix of pride and sadness, then an uneasy mix of hope and fear."),
    ("bs060_ok_recipe", "prose", "Add a mix of flour and sugar, then fold in the eggs."),
    ("bs061_corrective_disclaimer", "prose", "Claims about its floating should be treated as religious tradition rather than as archaeological explanation. Her early life is not widely documented."),
    ("bs061_ok_legal_reading", "prose", "The provision should be read as a limitation on agency power rather than as a grant of authority."),
    ("bs062_future_closer_last_para", "prose", "The council approved the plan.\n\nAs the industry continues to evolve, one thing is clear: the future looks bright."),
    ("bs062_ok_body_and_crlf", "prose", "Looking ahead, the council plans a vote.\r\n\r\nThe vote is in March, and the bypass opens in June."),
    ("bs062_looking_ahead_closer", "prose", "The bakery turns sixty this year.\n\nLooking ahead, the family hopes to open a second shop."),
    ("bs062_ok_weekday_forecast", "prose", "Rain overnight.\n\nLooking ahead, the forecast calls for rain through Thursday."),
    ("bs024_body_attribution", "prose", "Remote work boosts productivity, experts say."),
    ("bs024_ok_headline_attribution", "label", "Not a recession, but close, economists say"),
    ("bs063_importance_flag", "prose", "This distinction matters because teams often conflate the two."),
    ("bs063_ok_docs_warning", "prose", "The order matters here: auth middleware must run before the router."),
    ("bs064_as_much_about_closer", "prose", "The beds went in late.\n\nGardening is as much about patience as technique."),
    ("bs064_ok_review_body", "prose", "The film is as much about the city as it is about the people who leave it.\n\nIt opens Friday."),
    ("bs030_sounds_familiar", "prose", "Slow builds again? If this sounds familiar, take heart. Sound familiar? You're not alone."),
    ("bs030_ok_callback", "prose", "If this sounds familiar, it's because I wrote about it last week."),
    # --- adversarial: document budgets (BS-038 appended label, twice) ---
    ("document_budget_overrun", "prose",
     "## Method, and why this one\n\nWe ran it for six weeks.\n\n"
     "## Scope, and why it matters\n\nThe pilot covered two schools."),
    ("document_budget_bs053", "prose", "Tutoring stays. I cut the gym. Piano stays."),
    # --- adversarial: content_type="label" suppresses burstiness/uniformity ---
    ("label_content_type", "label", "Eight words to carry. Your answer first. Section three."),
    # --- 2026-11-09: content_type="resume" and lexical_patterns.terms_of_art ---
    ("resume_skills_block", "resume",
     "Design: user research, journey mapping, and usability testing.\n"
     "Prototyping: Figma, Framer, and HTML, CSS and JavaScript.\n"
     "Teaching: curriculum design, assessment, and differentiated instruction."),
    ("skills_block_as_prose_control", "prose",
     "Design: user research, journey mapping, and usability testing.\n"
     "Prototyping: Figma, Framer, and HTML, CSS and JavaScript.\n"
     "Teaching: curriculum design, assessment, and differentiated instruction."),
    ("terms_of_art_partial", "prose", "I use differentiated instruction. Our product differentiates itself."),
    # --- 2026-11-12 repair round PR 1: BS-066 budget-only flip, four un-nested lexicon terms ---
    ("bs066_contracted_flip_twice", "prose",
     "It's not a tool. It's a partner. This isn't a bug. It's a feature."),
    ("bs066_curly_semicolon_flip_twice", "prose",
     "It\u2019s not about speed; it\u2019s about trust. This isn\u2019t a bug. It\u2019s a feature."),
    ("bs066_ok_single_flip", "prose", "That isn't the invoice. It's the receipt."),
    ("lexicon_nestled", "prose", "The cabin was nestled in the hills above the lake."),
    ("lexicon_diverse_array", "prose", "The shop stocks a diverse array of teas."),
    ("lexicon_renowned_natural_beauty", "prose", "The renowned valley is known for its natural beauty."),
    ("lexicon_ok_nest_bird", "prose", "The wren built a nest in the shed."),
    # --- 2026-11-12 repair round PR 2: AR-002 skips code and command flags ---
    ("ar002_flag_in_backticks", "prose", "Run `git push --force` before you leave the office."),
    ("ar002_bare_flag_in_prose", "prose", "Pass --force when the lock file is stale."),
    ("ar002_emdash_in_fence", "prose",
     "Here is the draft.\n\n```\nThe plan \u2014 as agreed \u2014 ships Friday.\n```\n\nThat is all."),
    ("ar002_hyphen_run_in_fence_ok", "prose",
     "Usage below.\n\n```\ntool -- verbose --Dana\n```\n\nThat is all."),
    ("ar002_hyphen_run_in_tilde_fence_ok", "prose",
     "Usage below.\n\n  ~~~~sh\ntool -- again\n~~~~~\n\nThat is all."),
    ("ar002_backtick_fence_with_backtick_info", "prose",
     "Look at ```tool -- one``` here.\nThen `x -- y` too."),
    ("ar002_unclosed_fence_fires", "prose", "Usage below.\n\n```\ntool -- again\nNo closing fence."),
    ("ar002_short_closer_fires", "prose", "Usage below.\n\n````\ntool -- again\n```\nStill open."),
    ("ar002_tab_after_closer_fires", "prose", "Usage below.\n\n```\ntool -- again\n```\t\nNot closed."),
    ("ar002_typed_dash_beside_code_span", "prose", "Call `run` -- it exits at once after that."),
    ("ar002_typed_dash_upper_after_span", "prose", "Call `run`--Dana waits on the other end."),
    ("ar002_attribution_line", "prose",
     "Be yourself; everyone else is already taken.\n> --Oscar Wilde"),
    ("ar002_quoted_flag_ok", "prose", 'Use "--verbose" or \u2018--dry-run\u2019 for more output.'),
    ("ar002_quoted_typed_dash_fires", "prose", 'He said "--and then we left" and nothing more.'),
    ("ar002_paren_flag_ok", "prose", "Pass the flag (--force) when the lock is stale."),
    ("ar002_triple_hyphen_flag_fires", "prose", "Pass ---force when the lock is stale."),
    ("ar002_unicode_letter_after_fires", "prose", "Pass --\u00e9tat when the lock is stale."),
    ("ar002_crlf_fence", "prose", "Usage below.\r\n```\r\ntool -- again\r\n```\r\nThat is all -- done."),
    # Only \r and \n are stripped from a line's end, so a closer terminated by
    # another separator (U+2028, U+0085) is not a closer: the fence stays open.
    ("ar002_u2028_terminated_fence_stays_open", "prose",
     "Usage below.\u2028```\u2028tool -- again\u2028```\u2028That is all."),
    # splitlines breaks on \f, U+2029 and U+0085, so a closer after one of them
    # is on its own line and closes the fence; a \n-only split would miss it.
    ("ar002_formfeed_before_closer_closes", "prose", "Usage below.\n```\ntool -- again\f```\nThat is all."),
    ("ar002_u2029_before_closer_closes", "prose", "Usage below.\n```\ntool -- again\u2029```\nThat is all."),
    ("ar002_vtab_before_closer_closes", "prose", "Usage below.\n```\ntool -- again\v```\nThat is all."),
    ("ar002_nel_terminated_fence_stays_open", "prose", "Usage below.\x85```\x85tool -- again\x85```\x85Done."),
    ("ar002_nel_before_closer_closes", "prose", "Usage below.\n```\ntool -- again\x85```\nThat is all."),
    ("ar002_structural_line_control_chars", "prose", "Above.\n\x1c--\x1d\nBelow."),
    ("ar002_structural_nbsp_line", "prose", "Above.\n\u00a0-- |\nBelow."),
    ("ar002_emdash_inline_span_fires", "prose", "The `build \u2014 step` fails sometimes."),
    # --- repair round PR 2: rubric (see crafted_rubric below) ---
]

# Rubric cases: (name, content_type, text, rubric). They compare manual_review
# line for line, so the content-type filter, the aliases and the short/full
# switch are all under parity.
_RUBRIC_TEXT = (
    "I spent the morning fixing the fence. The wood had warped over winter, so "
    "two boards no longer met. My neighbour lent me a plane and we shaved them "
    "down until they sat flush."
)
crafted_rubric = [
    ("rubric_no_content_type_short", None, _RUBRIC_TEXT, "short"),
    ("rubric_label_short", "label", _RUBRIC_TEXT, "short"),
    ("rubric_case_study_short", "case_study", _RUBRIC_TEXT, "short"),
    ("rubric_case_study_full", "case_study", _RUBRIC_TEXT, "full"),
    ("rubric_no_content_type_full", None, _RUBRIC_TEXT, "full"),
    ("rubric_unknown_type_short", "newsletter", _RUBRIC_TEXT, "short"),
    ("rubric_alias_portfolio_padded_short", "  Portfolio ", _RUBRIC_TEXT, "short"),
    ("rubric_alias_resume_accent_full", "R\u00e9sum\u00e9", _RUBRIC_TEXT, "full"),
    ("rubric_tech_default", "tech", _RUBRIC_TEXT, "short"),
]

# --- 3. Real text: the eval corpus (human + AI) ------------------------------
# Cases whose non-AR-002 output differs from JS by a known whitespace edge (the
# NEL cases: U+0085 is whitespace to Python's str.split() but not to JS, so the
# sentence metrics differ on it); parity compares only the named report keys.
HARD_ONLY_CASES = {"ar002_nel_terminated_fence_stays_open", "ar002_nel_before_closer_closes"}
battery = []
for name, ct, text in crafted:
    entry = {"name": name, "content_type": ct, "text": text, "rubric": "short"}
    if name in HARD_ONLY_CASES:
        entry["compare"] = ["hard_violations"]
    battery.append(entry)
for name, ct, text, rubric in crafted_rubric:
    battery.append({"name": name, "content_type": ct, "text": text, "rubric": rubric})

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
                        "rubric": "short",
                        "text": fh.read().strip(),
                    })

golden = []
for item in battery:
    report = run_checks(item["text"], item["content_type"], item["rubric"])
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
