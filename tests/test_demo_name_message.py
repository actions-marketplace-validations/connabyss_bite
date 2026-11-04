"""`bite --demo nosuch` said "unknown option 'nosuch'", which sounds like a flag typo even though there are
two demos and neither is named in the message. Name them where the mistake is made."""

import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
RECENT = str(KIT / "recent.py")


def test_an_unknown_demo_name_lists_the_two_demos(tmp_path):
    p = subprocess.run([sys.executable, RECENT, "--demo", "nosuch"], cwd=tmp_path, capture_output=True,
                       text=True, timeout=300)
    out = p.stdout + p.stderr
    assert p.returncode == 2, out
    assert "Bite: there's no demo called 'nosuch'. Try bite --demo, or bite --demo comeback." in out, out
    assert "unknown option" not in out, out


def test_a_flag_typo_after_demo_still_says_unknown_option(tmp_path):
    p = subprocess.run([sys.executable, RECENT, "--demo", "--no-such-flag"], cwd=tmp_path, capture_output=True,
                       text=True, timeout=300)
    out = p.stdout + p.stderr
    assert p.returncode == 2, out
    assert "unknown option '--no-such-flag'" in out, out
