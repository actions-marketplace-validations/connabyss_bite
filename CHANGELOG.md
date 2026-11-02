# Changelog

What changed in each Bite release, newest first. Numbers link to the pull request on
github.com/connabyss/bite. Install or update: `pipx install --force bite-check --pip-args="--no-cache-dir"`.

## 1.0.1 (2026-11-02)

Fixed:
- A hung test run stops early. Undoing a fix that bounds a loop can make the tests loop forever, and Bite used to wait
  out the full test_timeout (10 minutes) several times for one change. Now, once the tests have passed with the change
  in, a run without it stops at 5 times that length (at least 60 seconds). That counts as the tests noticing the
  change, and the report says so: "Without this change your tests hang (stopped after 66s; they take 13s with it)".
  Same in `bite live` and `bite mcp`. On Scrapling, two loop fixes went from most of an hour to 3.6 minutes (#145).
- With `--jobs`, a failing run is repeated alone only if another run overlapped it, and the flaky rerun serves as that
  repeat. A noticed change costs three test runs again, not five (#145).
- The log says what each test run is ("running the tests with the change taken out (they took 1m 25s with it
  in)..."), so a long check no longer goes quiet (#145).

## 1.0.0 (2026-11-02)

The first stable release. The names in results.json and `--json` stay as they are from here on.

New:
- Bite score: every run says how many of the checked changes a test noticed (7/9), on the report as a ring, in the
  PR comment and results.json, with a README badge and bite_proof/badge.json (#118).
- When several changes have no test, Bite names the one to write first, and why (#119).
- Bite remembers each run's score: "up from 5/9 last run", "Bite-proof 3 runs in a row" (#121).
- Action `badge-branch`: a score badge that updates itself on each push (#123).
- bite_proof/card.svg: the score as a picture to share (#125).
- `bite ask` finds a fix by the function it changed: "is the make_metavar fix guarded?" (#128).
- Python doctests (pytest --doctest-modules) a fix wrote count as its test, like Rust doc examples (#124).
- Rust: a fix tested by a unit test in the same file (`#[cfg(test)] mod tests`) counts as noticed. Go: a change only
  to files built for another system (`x_windows.go`) is skipped, not flagged (#120).
- README: "Why you need this", in plain words, for people who code with an AI (#129).
- Faster checks. `--shard 2/5` runs one part of a check, so 5 machines can split it (#137). `--jobs 4` checks 4 changes
  at a time, and a run that failed alongside others counts only if it fails again on its own. Bite remembers the
  changes it checked with ✅ and skips them next time, unless a test, setting or dependency changed (`--again` checks them all);
  the Action keeps that memory between runs. A slow run ends with tips to speed it up (#138).
- Bite's own weekly check runs on 20 machines at once, and its tests run 4 at a time (#137).
- The Action and the workflows Bite suggests use the newest GitHub actions (checkout v7, setup-python v7,
  upload-artifact v7, cache v6, ...), so they no longer warn that Node.js 20 is deprecated (#22).
- `--write-tests` says what it's doing at each step in plain words ("Asking Claude to write the missing test…",
  "Running it with the change taken out (it must fail)…", "✅ Test written" or why none was kept), with a line every
  minute while a step runs. On GitHub Actions the job page gets a table of every change checked, and the weekly
  self-check gathers one table from all its machines (#140).

Fixed:
- The comeback alarm stays quiet when a later commit did the fix another way, a revert came undone, or a tidy-up
  came undone, and it names the commit that put the old code back instead of a merge (#116).
- A link to a code file no longer stops the whole run, and a file error in one commit's copy only stops that
  commit's check (#117).
- A fix that also deletes a file no longer stops the whole run with an error, and putting the deleted file back
  no longer counts as a piece of the change on its own (#122).
- A source file that isn't UTF-8 (Latin-1, Windows-1252) no longer hides an untested piece of a fix: Bite keeps
  every byte of it when it takes a piece out (#126).
- A fix in a big generated file (a 60,000-line bundle.js) no longer takes minutes to check: Bite reads code
  for comments about 50 times faster and stops splitting a change once it has more pieces than it can test (#127).
- Plain answers for odd inputs: an option with no value, a negative `--last`, a folder that isn't there given to
  `bite mcp`, and links in `bite live` (#130).
- A submodule whose folder is named like a code file (vendor/chart.js) no longer stops a check or bite live (#130).
- Bite's pull request comment no longer pings people named in a commit title ("thanks @alice") (#131).
- The pull request comment stays under GitHub's 65,536-character limit (over it, the Action posted nothing): very
  long commit titles are cut, and long tests Bite wrote point to their file instead (#131).
- `.bite.ini` saved by Windows Notepad works; a setting Bite can't use is named in a sentence instead of a Python
  error (#132).
- A test Bite or its worker wrote now runs when the project's pytest command has an option with a value: `-n auto`
  (pytest-xdist) lost its `auto`, so every claim test and every `--write-tests` test failed to start and was
  thrown out (#143).
- A tidy-up right next to a fix (removing an import beside it) no longer hides a later test that guards it: the
  fix showed NO TEST NOTICED. The comeback alarm also notices an undo that tidied the line beside the fix (#141).
- The self-check's issue no longer asks for the API key when Bite has one but didn't keep the test it wrote; it
  says why the test was thrown out (#140).
- The "check it yourself" steps quote file paths with spaces, so they work when pasted (#133).
- On Windows, Bite's copies keep file names that aren't plain ASCII (`café.py`); before, such a project read as
  "tests already fail" (#134).
- In a shallow clone (git clone --depth 1) Bite says so and gives `git fetch --unshallow`, instead of "try a larger
  --last" (#135).

## 0.11.0 (2026-11-01)
- Harder to trick: 16 of the tricks we threw at Bite no longer fool it. That includes a tested change that vouches
  for an untested one in the same commit, a test deleted later, flaky tests, and `#` inside strings. See
  TRICKS.md (#112).
- Quicker: the piece-by-piece check has one budget for the whole run (`--part-runs`, 6 by default), and `--quick`
  skips the extra checks (#113).
- Plain words when the tests already fail, and the right newest commit (#114).
- One line to update that always works, and `bite --version` says when a new one is out (#111).

## 0.10.0 (2026-11-01)
- Java and Kotlin: Maven and Gradle projects, with the project's own mvnw or gradlew first (#106).
- The comeback alarm: "UNDONE BY A LATER COMMIT" names a later commit that quietly put a fix's old code back
  (`bite --demo comeback`) (#108).
- `bite ask` answers are easier to read (#107), and a crash on an undone fix is fixed (#110).
- Clearer text for people finding Bite on the Marketplace and PyPI (#109). Logo on the report (#90, #105).

## 0.9.0 (2026-11-01)
- `bite --json`, and bite_proof/results.json on every run: results other tools can read, under names that won't
  change (#102).
- `bite ask "is last week's login fix guarded?"`: ask in plain words (#100).
- One set of names for 1.0: NO TEST NOTICED, ITS TESTS DIDN'T NOTICE; `.bite.ini` starts with `[bite]` (old
  `[kit]` still works) (#101).

## 0.8.0 (2026-10-31)
- `bite mcp`: the live check as a tool any coding AI can call (Claude Code, Cursor, Copilot in VS Code, Windsurf,
  Codex, Gemini CLI) (#97).
- Rust doc examples a commit wrote count as its test (#96).

## 0.7.0 (2026-10-31)
- `bite live` and a Claude Code plugin: the free check on your coding AI's changes as it finishes each turn (#70).
- Bite checks Bite: a weekly self-check opens an issue for each gap, and a PR with the test (#71, #73, #79, #81, #84).
- `--write-tests` keeps a written test only if a second fresh check calls it fair (#83).
- The scoreboard: Bite's free check on 20 well-known projects (#82, #85).
- Fewer false alarms: a passing test named "parse error" (#78), JavaScript copies in hidden folders (#74).

## 0.6.0 (2026-10-31)
- `bite --write-tests` and the Action's `write-tests`: write the missing test for each change no test noticed (#66).
- Go: a written test runs as its own package (#67). Release commits and Go `interface{}` to `any` swaps are skipped (#64).

## 0.5.1 (2026-10-30)
- Says why pytest crashed, and turns the check red when the tests already fail (#63).

## 0.5.0 (2026-10-30)
- `bite --demo`: try Bite on a tiny made-up project first (#58).
- tape, tap, ava, uvu, jasmine, nyc and c8 known as JavaScript runners (#59).

## 0.4.1 (2026-10-30)
- On PyPI as `bite-check` (#56).
- Only takes out code in the language the tests run (#55).
- Skips type-hint-only, other-Python-version and speed-up commits (#52).
- `--roast` and the Bite-proof badge (#50). Option values are checked (#47).

## 0.4.0 (2026-10-30)
- Checks every commit by default, whoever or whatever wrote it (#45).

## 0.3.0 (2026-10-30)
- Plain words for what Bite found, naming the test that noticed (#43). Three false flags stopped (#42).

## 0.2.0 (2026-10-30)
- The GitHub Action: Bite's free check on every pull request, with one plain-words comment (#33, #34, #36).
- AGENTS.md, so any coding AI can run Bite (#32).

## 0.1.0 (2026-10-29)
- First release: one-line install, first-run checks that name the fix, and a one-page report after every run.
