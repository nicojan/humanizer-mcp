from src.checker.punctuation import (
    find_comma_splices,
    find_stacked_marks,
    find_unterminated,
)


def test_stacked_comma_period_detected():
    v = find_stacked_marks("We shipped it,. then waited.")
    assert len(v) == 1
    assert v[0]["type"] == "stacked_punctuation"
    assert v[0]["rule"] == "AR-003"


def test_stacked_semicolon_period_detected():
    v = find_stacked_marks("It works;. mostly.")
    assert len(v) == 1


def test_double_comma_detected():
    v = find_stacked_marks("She said,, then left.")
    assert len(v) == 1


def test_four_periods_detected():
    v = find_stacked_marks("She trailed off....")
    assert len(v) == 1


def test_three_periods_ellipsis_not_detected():
    assert find_stacked_marks("She trailed off... then continued.") == []


def test_abbreviation_period_comma_not_detected():
    # 'etc.,' 'e.g.,' 'i.e.,' 'Inc.,' all use period-then-comma.
    assert find_stacked_marks("Use semicolons, commas, etc., to vary marks.") == []
    assert find_stacked_marks("Frameworks (e.g., React) ship updates.") == []
    assert find_stacked_marks("That is, i.e., the underlying claim.") == []
    assert find_stacked_marks("Apple Inc., based in Cupertino, ships chips.") == []


def test_clean_text_no_stacked():
    assert find_stacked_marks("A clean paragraph. With proper marks; including semicolons.") == []


def test_unterminated_final_fragment_flagged():
    v = find_unterminated("We shipped on Tuesday. The team was glad it landed")
    assert any(f["type"] == "missing_terminal_mark" for f in v)


def test_properly_terminated_text_passes():
    assert find_unterminated("We shipped on Tuesday. The team was glad it landed.") == []


def test_terminal_followed_by_closing_quote_passes():
    assert find_unterminated('She said, "we shipped it."') == []


def test_terminal_followed_by_closing_paren_passes():
    assert find_unterminated("We shipped it (finally).") == []


def test_run_on_flagged():
    # 50-word stretch with no period inside.
    long = "word " * 50
    v = find_unterminated(long + ".")
    assert any(f["type"] == "run_on_without_terminal" for f in v)


def test_normal_long_paragraph_with_periods_passes():
    # 80 words but broken into multiple sentences — should NOT trigger.
    t = (
        "We shipped the update on Tuesday morning. "
        "The team had been working on it for weeks. "
        "Several pieces still needed integration, but everyone agreed it was time. "
        "The bug that surfaced in staging turned out to be a simple typo. "
        "By Wednesday the metrics were already trending up. "
        "Nobody quite believed it."
    )
    assert all(f["type"] != "run_on_without_terminal" for f in find_unterminated(t))


def test_empty_text_no_findings():
    assert find_stacked_marks("") == []
    assert find_unterminated("") == []


def test_findings_carry_offset_and_excerpt():
    v = find_stacked_marks("We shipped it,. then waited.")
    assert v[0]["offset"] == len("We shipped it")
    assert "excerpt" in v[0] and "," in v[0]["excerpt"]


# --- comma splices (AR-003) ---------------------------------------------------
# A comma splice joins two independent clauses with only a comma. This is the
# classic artifact of AR-002 em-dash replacement: an em-dash pivot between two
# independent clauses gets swapped for a comma. Detection must stay conservative
# — legitimate complex sentences, parentheticals, and lists must NOT trip it.


def test_comma_splice_basic_past_tense():
    v = find_comma_splices("It was late, we went home.")
    assert len(v) == 1
    assert v[0]["type"] == "comma_splice"
    assert v[0]["rule"] == "AR-003"


def test_comma_splice_from_emdash_replacement():
    # "The results were clear — we shipped …" → comma → splice.
    v = find_comma_splices(
        "The results were clear, we shipped the feature the next morning."
    )
    assert any(f["type"] == "comma_splice" for f in v)


def test_comma_splice_with_be_verb():
    v = find_comma_splices("She liked the plan, it was bold.")
    assert len(v) == 1


def test_comma_splice_with_modal():
    v = find_comma_splices("The deadline slipped, they would miss the launch.")
    assert len(v) == 1


def test_subordinate_clause_lead_not_flagged():
    # Dependent clause first → the comma is correct (complex sentence).
    assert find_comma_splices("When it rains, it pours.") == []


def test_conditional_lead_not_flagged():
    assert find_comma_splices("If you build it, they will come.") == []


def test_concessive_lead_not_flagged():
    assert find_comma_splices("Although we tried, it failed.") == []


def test_parenthetical_not_flagged():
    # "it seemed" is a parenthetical aside, not a spliced clause.
    assert find_comma_splices("The plan, it seemed, would work.") == []


def test_coordinating_conjunction_not_flagged():
    # ", but we went home" is a correct compound sentence.
    assert find_comma_splices("It was late, but we went home.") == []


def test_list_not_flagged():
    assert find_comma_splices("We packed apples, oranges, and pears.") == []


def test_object_pronoun_not_flagged():
    # "us" is an object pronoun, not a clause subject.
    assert find_comma_splices("She thanked us before the meeting.") == []


def test_clean_two_sentences_not_flagged():
    assert find_comma_splices("It was late. We went home.") == []


def test_conjunctive_adverb_intro_not_flagged():
    # "However" is not an independent clause; ", it was too late" is the main
    # clause. Correct sentence, must not trip.
    assert find_comma_splices("However, it was too late.") == []


def test_temporal_intro_phrase_not_flagged():
    assert find_comma_splices("In 2020, it changed everything.") == []


def test_adverb_intro_not_flagged():
    assert find_comma_splices("Yesterday, we shipped the release.") == []


def test_sentence_adverb_intro_not_flagged():
    assert find_comma_splices("Honestly, they were right about it.") == []


def test_enumeration_intro_not_flagged():
    assert find_comma_splices("First, we tested the build carefully.") == []


def test_infinitive_intro_not_flagged():
    # "To be fair" is an infinitive phrase, not an independent clause.
    assert find_comma_splices("To be fair, it was a hard call.") == []


def test_present_participle_intro_not_flagged():
    assert find_comma_splices("Having finished the work, we left early.") == []


def test_past_participle_intro_not_flagged():
    assert find_comma_splices("Frustrated by the delay, they quit the project.") == []


def test_comma_splice_offset_points_at_comma():
    v = find_comma_splices("It was late, we went home.")
    assert v[0]["offset"] == len("It was late")
