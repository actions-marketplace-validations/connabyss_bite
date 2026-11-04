"""On Windows, Bite's output sent to a file (`> run.log`) was written in the system's code page, cp1252: the ✅
and ⚠️ marks came out as "?" and a cut-off subject's "…" as a stray byte (seen in marked's run.log). Output to a
file is now UTF-8; a pipe keeps the system's encoding, since the program reading it decodes with that (UTF-8 there
broke every Windows test that read Bite's output). Here cp1252 is forced with PYTHONIOENCODING, as on that PC.
No key, no network."""

import os
import subprocess
import sys
from pathlib import Path

RECENT = str(Path(__file__).resolve().parent.parent / "recent.py")


def test_marks_survive_output_to_a_file_on_a_cp1252_system(tmp_path):
    log = tmp_path / "run.log"
    with open(log, "wb") as f:
        subprocess.run([sys.executable, RECENT, "--demo"], stdout=f, stderr=subprocess.STDOUT, timeout=300,
                       cwd=tmp_path, env={**os.environ, "PYTHONIOENCODING": "cp1252"})
    out = log.read_bytes().decode("utf-8")
    assert "✅ noticed by" in out and "⚠️ NO TEST NOTICED" in out, out


def test_a_pipe_keeps_the_systems_encoding(tmp_path):
    p = subprocess.run([sys.executable, RECENT, "--demo"], capture_output=True, timeout=300, cwd=tmp_path,
                       env={**os.environ, "PYTHONIOENCODING": "cp1252:replace"})
    p.stdout.decode("cp1252")  # what a program reading it on Windows does; UTF-8 bytes like ✅ broke it
