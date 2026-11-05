"""The commit-confidence easter egg: a commit that sounds very sure (or not sure at all) gets one extra, true line."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import recent  # noqa: E402

SHA = "c" * 40


def said(subject, undo, **extra):
    return recent.say({"sha": SHA, "subject": subject, "undo": undo, **extra})[2]


def test_sure_commit_with_no_test_gets_told():
    text = said("Fix the totals for real this time", "unguarded")
    assert "It said “for real this time”. No test agrees." in text
    assert text.index("No test agrees.") < text.index("**Next:**")


def test_sure_commit_with_a_test_gets_credit():
    text = said("Fix the totals for real this time", "guarded", caught="`test_total`")
    assert text.endswith("It said “for real this time”. This time, a test agrees.")
    assert "And a test agrees." in said("Finally fixed the cart", "guarded")


def test_unsure_commit():
    assert "“Hopefully,” it said. No test backs it up." in said("Hopefully fixes the cart (#12)", "unguarded")
    assert said("This should fix login", "guarded").endswith("“Should fix,” it said. A test backs it up.")


def test_its_own_tests_missing_counts_as_no_test():
    text = said("Actually fixed rounding", "TEST GUARDS NOTHING", test_code=["test_x"])
    assert "It said “actually fixed”. No test agrees." in text


def test_quiet_when_the_words_are_not_there_or_the_result_is_mixed():
    plain = recent.say_plain({"sha": SHA, "subject": "Fix the totals", "undo": "unguarded"})[2]
    assert said("Fix the totals", "unguarded") == plain
    assert "It said" not in said("Fix the forreal parser", "unguarded")
    # Part noticed, tests failing, skipped: "no test agrees" wouldn't be true, so nothing is added.
    assert "It said" not in said("Fix it for real", "unguarded: part", part="`b()`")
    assert "It said" not in said("Fix it for real", "tests fail at this commit")
    assert "it said" not in said("Hopefully fixes it", "not flagged: tidy-up commit")


def test_label_and_kind_never_change():
    for undo in ("unguarded", "guarded", "TEST GUARDS NOTHING"):
        c = {"sha": SHA, "subject": "Fixed for real this time, hopefully", "undo": undo, "test_code": ["t"]}
        assert recent.say(c)[:2] == recent.say_plain(c)[:2]
