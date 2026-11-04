# Contributing to Bite

Thanks for helping. Bite is small on purpose, so the best PRs are small too.

## Set up (one minute)

```
git clone https://github.com/connabyss/bite && cd bite
pip install -e .[test]
python -m pytest -n auto
```

`-n auto` runs the tests several at a time (pytest-xdist, in `[test]`): about a minute instead of three, and
much faster on Windows. Plain `python -m pytest` runs them one at a time.

The tests need no key and no network. They should all pass before and after your change.

## Try Bite in 2 minutes

With Bite installed (above), this builds a two-file repo, makes a fix no test covers, then adds the test that
catches it. Linux/macOS:

```bash
mkdir bite-demo && cd bite-demo
git init -q
git config user.name "Bite Demo"
git config user.email "demo@example.com"

cat > calc.py <<'EOF'
def add(a, b):
    return a + b + 1


def label(name):
    return name.strip()
EOF

cat > test_calc.py <<'EOF'
from calc import label


def test_label():
    assert label("  hi  ") == "hi"
EOF

git add . && git commit -qm "Start the calculator"

cat > calc.py <<'EOF'
def add(a, b):
    return a + b


def label(name):
    return name.strip()
EOF
git commit -qam "Fix add adding one too many"

bite --free
```

Bite prints one checked commit and `NO TEST NOTICED`: the fix is real, but nothing would catch it coming back.
Add the missing test and commit it:

```bash
cd bite-demo
cat >> test_calc.py <<'EOF'


def test_add():
    from calc import add
    assert add(1, 2) == 3
EOF
git add test_calc.py
git commit -qm "Test add"

bite --free
```

The same fix is now `✅ a later test notices`, and the score is `1/1`. The test was added in a later commit,
which is fine: Bite re-runs today's tests against each old change.

Windows PowerShell:

```powershell
mkdir bite-demo; cd bite-demo
git init -q
git config user.name "Bite Demo"
git config user.email "demo@example.com"

@'
def add(a, b):
    return a + b + 1


def label(name):
    return name.strip()
'@ | Set-Content calc.py

@'
from calc import label


def test_label():
    assert label("  hi  ") == "hi"
'@ | Set-Content test_calc.py

git add .; git commit -qm "Start the calculator"

@'
def add(a, b):
    return a + b


def label(name):
    return name.strip()
'@ | Set-Content calc.py
git commit -qam "Fix add adding one too many"

bite --free

@'


def test_add():
    from calc import add
    assert add(1, 2) == 3
'@ | Add-Content test_calc.py
git add test_calc.py; git commit -qm "Test add"

bite --free
```

Delete `bite-demo` when you are done; its `bite_proof/` folder holds the reports.

## What helps most

- **Bite was wrong about your repo.** It flagged a fix that holds, or stayed quiet about one that doesn't. Open
  an issue with the commit link and what Bite printed. These reports make Bite better than anything else.
- **Fixes.** Something crashes, a message is confusing, a test runner isn't guessed right, a path breaks on
  Windows. Issues labeled "good first issue" are a good place to start.
- Bite's scope is deliberately narrow: it checks "fixed" claims in commits. Please open an issue before
  building something bigger, so we can talk first.

## PR checklist

Opening a PR fills in a short checklist for you. Its check never blocks your PR; it only reminds you of a box
left unticked. The one real ask:

- **For a bug fix, a test that fails without your change.** That's Bite's whole point, so we hold ourselves to
  it too. Not sure your test catches it? Run `bite live` before you commit: it tells you whether any test
  notices your change.
- `python -m pytest` passes, and CI is green (those checks do block the merge).
- One fix per PR, with plain words in the description: what was wrong, what you changed, how you checked.

Nice to have, never required: light and dark screenshots if it changes how something looks (we can take them).
If a small piece is left over, a maintainer may finish it for you and keep you as co-author.

## AI-assisted PRs

Welcome. Bite exists to check AI-written fixes, so it would be odd to turn them away. Please add an
`Assisted-by: <tool>` line (for example `Assisted-by: Claude Code`) to the commit message or the PR
description, and make sure you've read and run the change yourself. Bite will probably be run on your PR.
