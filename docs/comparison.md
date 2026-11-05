# Bite, mutmut and coverage

[← Back to the README](https://github.com/connabyss/bite#readme)

All three help answer "are my tests any good?". They answer different parts of it, and they work fine together.

| | [coverage.py](https://coverage.readthedocs.io/) | [mutmut](https://github.com/boxed/mutmut) | Bite |
|---|---|---|---|
| **It asks** | Which lines did the tests run? | If this code were slightly wrong, would a test fail? | If this real fix were taken back out, would a test fail? |
| **How** | Watches one test run and notes each line that ran (with `--branch`, each jump too) | Makes many small made-up changes, like `<` to `<=` or `5` to `6`, and runs the tests on each | Takes out the code part of each recent fix commit, one at a time, and runs the tests |
| **Looks at** | All the code you measure | All the code in its `source_paths` | Recent commits that say they fix something (`--last 40` by default; `--any` for all) |
| **Test runs** | One | One per made-up change (it picks which tests to run and remembers past work) | One per change checked |
| **Languages** | Python | Python (it runs pytest) | Python, JavaScript/TypeScript, Rust, Go, .NET, Java/Kotlin ([full list](https://github.com/connabyss/bite/blob/main/SUPPORTS.md)) |
| **Windows** | Yes | Inside WSL only (it needs `fork`) | Yes |

## What each one can't tell you

- **coverage.py:** a line can run during a test without any test checking what it did. 100% coverage means every
  line ran, not that a test would fail if a line were wrong.
- **mutmut:** its changes are made up, so you may decide some "survivors" (changes no test failed on) don't
  matter. Its docs list ways to cut that noise: comments that skip lines or blocks, and a type checker that filters
  out changes. Many changes means many test runs.
- **Bite:** it takes out a whole fix at once, so "a test noticed" means some test caught the fix going missing, not
  that every line of it is tested. It only looks at recent commits, not at code nobody changed lately.

## When to use which

- **coverage.py** to find code no test even runs. It needs just one test run, so it's a good first step.
- **mutmut** for a deep check of a Python project's tests, line by line, when you have time for a long run.
- **Bite** when someone (often an AI) says "fixed" and you want to know if a test would catch that bug coming back.
  The free check needs no key.

Facts about coverage.py and mutmut come from their own docs (coverage.py 7.17.2, mutmut 3.8.1, November 2026). If
something here is out of date or unfair to either tool, please [open an issue](https://github.com/connabyss/bite/issues/new/choose).
