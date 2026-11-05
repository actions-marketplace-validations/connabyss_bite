# Try Bite in 2 minutes, by hand

[← Back to CONTRIBUTING](../CONTRIBUTING.md)

With Bite installed (`pip install -e .[test]` in a clone, or `pipx install bite-check`), this builds a
two-file repo, makes a fix no test covers, then adds the test that catches it. Linux/macOS:

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
