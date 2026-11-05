"""The @claude workflow spends the repo's API key, so only the owner and collaborators may start it."""

import re
from pathlib import Path

FLOW = (Path(__file__).resolve().parent.parent / ".github" / "workflows" / "claude.yml").read_text(encoding="utf-8")
TRUSTED = """contains(fromJSON('["OWNER","MEMBER","COLLABORATOR"]'), github.event.{}.author_association)"""


def _condition() -> str:
    return re.search(r"^    if: \|\n((?:      .*\n)+)", FLOW, re.M).group(1)


def test_every_trigger_needs_a_trusted_author():
    # One clause per event the workflow listens to, and each clause checks who wrote the @claude.
    clauses = re.split(r"\)\s*\|\|\s*\n", _condition())
    events = re.findall(r"^  (\w+):\n    types:", FLOW, re.M)
    assert len(clauses) == len(events) == 4
    who = {"issue_comment": "comment", "pull_request_review_comment": "comment",
           "pull_request_review": "review", "issues": "issue"}
    for event in events:
        clause = next(c for c in clauses if f"github.event_name == '{event}'" in c)
        assert TRUSTED.format(who[event]) in clause, event


def test_it_stays_cheap_and_bounded():
    assert "--max-turns" in FLOW and "--model sonnet" in FLOW
    assert re.search(r"timeout-minutes: \d+", FLOW)
    # The key is only ever handed to the action, never printed or put in the environment of a run step.
    assert FLOW.count("secrets.ANTHROPIC_API_KEY") == 1
    assert "anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}" in FLOW
