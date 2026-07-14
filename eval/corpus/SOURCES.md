# Step 0 calibration corpus: provenance manifest

16 human + 16 AI samples, four genres × four, for the signal spike
(`python3 -m eval.spike`). Construction rules and validity guards:
`docs/superpowers/specs/2026-06-29-humanizer-eval-corpus-construction.md`.

The `.txt` files contain **sample text only**: `load_pile` scores them verbatim,
so no metadata lives in them. This file is the metadata.

## Normalization (applied uniformly to BOTH piles)

- Smart quotes / curly apostrophes → ASCII (`'` `"`). The word tokenizer
  `[A-Za-z']+` splits on a curly apostrophe but not a straight one, so leaving
  human web text curly while raw AI output is straight would be a tokenization
  confound. Normalizing both removes it.
- Reference markers (`[1]`), navigation, specs tables, code blocks, and (for
  cover letters) the address/date/salutation/signature were trimmed so each
  sample is clean running prose. Wording within each retained span is verbatim.
- Em-dashes are left as-is in human text (they are verbatim and the tokenizer
  ignores them); they do not affect the texture features.

## Human pile (genuinely human, all published before 2022-11-30 / ChatGPT launch)

Every row cites a **frozen** snapshot (Wayback capture timestamp in the URL) so
the pre-ChatGPT date is provable from this file alone.

| File | Genre | Source | Archived snapshot | Date | License | Words |
|---|---|---|---|---|---|---|
| human_prose_01 | prose | Paul Graham, "How to Do What You Love" | http://web.archive.org/web/20180105032648/http://paulgraham.com:80/love.html | 2018-01-05 | copyrighted-excerpt | 147 |
| human_prose_02 | prose | Tim Urban, Wait But Why, "The Tail End" | http://web.archive.org/web/20180620063435/https://waitbutwhy.com/2015/12/the-tail-end.html | 2018-06-20 | copyrighted-excerpt | 126 |
| human_prose_03 | prose | Tim Kreider, NYT Opinionator, "The 'Busy' Trap" | http://web.archive.org/web/20180109182507/https://opinionator.blogs.nytimes.com/2012/06/30/the-busy-trap/ | 2018-01-09 | copyrighted-excerpt | 144 |
| human_prose_04 | prose | Mark Manson, "7 Strange Questions That Help You Find Your Life Purpose" | http://web.archive.org/web/20190102021242/https://markmanson.net/life-purpose | 2019-01-02 | copyrighted-excerpt | 166 |
| human_technical_01 | technical | Pro Git (Git-SCM, 2nd ed.), Chacon & Straub | https://web.archive.org/web/20190531022734/https://git-scm.com/book/en/v2/Git-Basics-Getting-a-Git-Repository | 2019-05-31 | CC-BY-SA | 162 |
| human_technical_02 | technical | Real Python, "Python Virtual Environments: A Primer" | https://web.archive.org/web/20191213155508/https://realpython.com/python-virtual-environments-a-primer/ | 2019-12-13 | copyrighted-excerpt | 125 |
| human_technical_03 | technical | DigitalOcean Community (Justin Ellingwood) | https://web.archive.org/web/20191226200432/https://www.digitalocean.com/community/tutorials/understanding-systemd-units-and-unit-files | 2019-12-26 | CC-BY-NC-SA | 120 |
| human_technical_04 | technical | MDN Web Docs (Mozilla), "What is JavaScript?" | https://web.archive.org/web/20191231232426/https://developer.mozilla.org/en-US/docs/Learn/JavaScript/First_steps/What_is_JavaScript | 2019-12-31 | CC-BY-SA | 136 |
| human_cover_letter_01 | cover_letter | Purdue OWL, academic cover letter sample | http://web.archive.org/web/20200422124359/https://owl.purdue.edu/owl/job_search_writing/job_search_letters/academic_cover_letters/academic_cover_letter_sample.html | 2020-04-22 | copyrighted-excerpt | 140 |
| human_cover_letter_02 | cover_letter | Harvard Office of Career Services | http://web.archive.org/web/20200821000847/https://hwpi.harvard.edu/files/ocs/files/undergrad_resumes_and_cover_letters.pdf | 2020-08-21 | copyrighted-excerpt | 146 |
| human_cover_letter_03 | cover_letter | Yeshiva University Career Development Center | http://web.archive.org/web/20220905211723/https://www.yu.edu/sites/default/files/legacy/uploadedFiles/Student_Life/Resources_and_Services/Career_Development_Center/Students/Tips_and_Resources/COVER%20LETTERS.pdf | 2022-09-05 | copyrighted-excerpt | 155 |
| human_cover_letter_04 | cover_letter | Towson University Career Center | http://web.archive.org/web/20210912090441/https://www.towson.edu/careercenter/media/documents/cover_letters_and_employer_correspondences/sample_cover_letter_education2.pdf | 2021-09-12 | copyrighted-excerpt | 151 |
| human_marketing_01 | marketing | Apple, AirPods Pro | http://web.archive.org/web/20210102043326/https://www.apple.com/airpods-pro/ | 2021-01-02 | copyrighted-excerpt | 132 |
| human_marketing_02 | marketing | Patagonia, Black Hole Duffel 60L (two consecutive paras concatenated) | http://web.archive.org/web/20160817234202/http://www.patagonia.com:80/product-black-hole-duffel-bag-60-liters/49341.html | 2016-08-17 | copyrighted-excerpt | 134 |
| human_marketing_03 | marketing | Cotopaxi, Allpa 35L Travel Pack (two consecutive paras concatenated) | http://web.archive.org/web/20200211083451/https://www.cotopaxi.com/products/allpa-35l-travel-pack | 2020-02-11 | copyrighted-excerpt | 133 |
| human_marketing_04 | marketing | Filson, Mackinaw Wool Vest | http://web.archive.org/web/20220922223709/https://www.filson.com/mackinaw-wool-vest.html | 2022-09-22 | copyrighted-excerpt | 125 |

Copyrighted samples are short excerpts retained for internal, non-redistributed
evaluation, with attribution above.

## AI pile (known-AI, raw default-voice output, un-humanized)

Generated by a **naive subagent** (validity guard #3): given only genre + topic +
target word count, with **no humanizer rules and no sight of the human text**, so
the output is genuinely typical and not rule-aware. Generating model: Claude
(single-family; see the caveat below). Verbatim instruction: *"draft 16 short
writing samples for a content project … write each one naturally and well … hit
the target word count within about ±15%, at least 5 sentences."* No detection,
humanness, or em-dash guidance was given.

Each AI file is paired to the human file of the same name suffix (same topic,
matched length within ±15% (actual match was within ~2 words).

| File | Genre | Paired topic | Words |
|---|---|---|---|
| ai_prose_01 | prose | work vs. play as a child | 148 |
| ai_prose_02 | prose | days left with siblings/old friends | 128 |
| ai_prose_03 | prose | busyness as a boast | 145 |
| ai_prose_04 | prose | rediscovering an abandoned childhood hobby | 167 |
| ai_technical_01 | technical | getting a Git repository (init vs. clone) | 161 |
| ai_technical_02 | technical | Python virtual environments | 124 |
| ai_technical_03 | technical | systemd units and unit files | 121 |
| ai_technical_04 | technical | what is JavaScript | 137 |
| ai_cover_letter_01 | cover_letter | assistant professor of English | 141 |
| ai_cover_letter_02 | cover_letter | marketing/comms at an education nonprofit | 145 |
| ai_cover_letter_03 | cover_letter | program coordinator, children's nonprofit | 156 |
| ai_cover_letter_04 | cover_letter | elementary school teacher | 150 |
| ai_marketing_01 | marketing | wireless noise-cancelling earbuds | 133 |
| ai_marketing_02 | marketing | weather-resistant 60L travel duffel | 135 |
| ai_marketing_03 | marketing | 35L carry-on adventure backpack | 132 |
| ai_marketing_04 | marketing | heritage wool vest | 126 |

### Other-model slots (open, for true multi-model diversity)

The AI pile is currently single-family (Claude). To harden it, drop raw,
un-humanized samples from other models here as `ai_<genre>_05`, `_06`, … (one per
real model, e.g. GPT, Gemini, an open model) on any of the four topics, then add a
row above. The corpus test allows `len(ai) >= len(human)`, so additions don't
break the suite. Keep them raw; never run them through the humanizer first.

## Spike verdict (recorded 2026-06-29, against the pre-registered 0.75 AUC bar)

Pooled (`python3 -m eval.spike`, n=16 vs 16): **PASS**: best feature
`hapax_ratio = 0.82`. `type_token_ratio` and `bigram_repetition` follow at 0.744.
Notably the **burstiness** features do NOT separate (`sentence_length_stdev` 0.516,
`_range` 0.514): the well-written AI pile has human-like sentence-length
variation, so the discriminating signal is **lexical diversity**, not rhythm.

L0 sanity note (compliance, not separation): human 24.69 vs AI 3.01 weighted
findings per 1k words; human text trips the house-style checker *more* (it
contains em-dashes), exactly as the methodology predicts. L0 is not a human/AI
discriminator.

Per-genre diagnostic (`python3 -m eval.per_genre`, n=4 vs 4 each, direction only):
every genre has ≥1 feature separating cleanly, but the winning feature differs:
prose: `type_token_ratio`/`hapax_ratio` 1.0; technical: `bigram_repetition` 1.0;
cover_letter & marketing: `mean_word_length` 1.0. No single feature is robust
across all four → Step 2 should evaluate a combined signal, not one feature.
