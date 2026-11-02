# What Bite supports

Bite runs your project's own tests. It works anywhere those tests run on your computer or in CI, and it needs
Python 3.10+ and git. Everything below is free unless it says "API key".

## Languages and test runners

| Language | Test command Bite guesses (and other runners it knows) | What Bite takes out | Checked on (SCOREBOARD.md) |
|---|---|---|---|
| Python | `python3 -m pytest -q`, `python` on Windows (also tox, nox, unittest, hatch) | `.py`, `.pyw`, `.pyx`, `.pxd` | Click, marshmallow, Rich and others |
| JavaScript and TypeScript | `npm test` (also yarn, pnpm, node, bun, deno, jest, vitest, mocha, tape, tap, ava, uvu, jasmine, nyc, c8) | `.js`, `.mjs`, `.cjs`, `.ts`, `.tsx`, `.jsx`, `.mts`, `.cts`, `.vue`, `.svelte` | qs, minimist, object-inspect, Express |
| Go | `go test ./...` | `.go` | chi, cobra, testify, uuid |
| Rust | `cargo test` (doc examples count as tests) | `.rs` | bytes, indexmap, serde_json |
| C# and F# (.NET) | `dotnet test` | `.cs`, `.fs` | FluentValidation |
| Java and Kotlin | the project's `mvnw` or `gradlew`, else `mvn -B test` or `gradle test` | `.java`, `.kt` | JSON-java (not on the scoreboard yet) |
| Anything else | set `test_command` in `.bite.ini` | every code change | |

Unity: set `test_command` yourself (Unity's `-batchmode -runTests`).

## Where you can run it

| Where | How | Cost |
|---|---|---|
| Your terminal | `bite --free` | free |
| Every pull request | the GitHub Action (bite-free-check on the Marketplace) | free |
| While a coding AI works | `bite live`, the Claude Code plugin, or `bite mcp` for Cursor, Copilot in VS Code, Windsurf, Codex, Gemini CLI | free |
| In plain words | `bite ask "is last week's login fix guarded?"` | free |
| Other programs | `bite --json`, and bite_proof/results.json | free |
| Testing a claim, or writing the missing test | plain `bite`, or `bite --write-tests` | your own Anthropic API key, capped by `--budget` ($1 by default) |

Systems: Bite's own tests run on Linux, Windows and macOS with Python 3.10 and 3.13.

## What it doesn't do
- It can't prove a commit has no other bugs. A claim that holds is just that.
- It doesn't run tests that only work in a full git checkout (they show as "tests already fail").
- It doesn't check code your tests can't run (TypeScript under pytest, say). It lists that code instead.
- It never uses a Claude login or plan. The paid step needs an API key.
