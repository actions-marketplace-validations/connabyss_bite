# Security

Bite runs your project's tests, and its paid step lets a worker run commands on a copy of your project. So a
security hole in Bite matters. Please tell us about one privately first, not in a public issue.

## How to report one

- Best: the **Report a vulnerability** button on the
  [Security tab](https://github.com/connabyss/bite/security/advisories/new). Only the maintainer sees it.
- Or email connabyss.code@proton.me with "Bite security" in the subject.

Say what you did, what happened, and which Bite version (`bite --version`). A small repo or command that shows
it helps most. You'll get an answer within a week, and credit in the release notes if you'd like it.

## Which versions get fixes

Only the newest release on [PyPI](https://pypi.org/project/bite-check/). Update with
`pipx install --force bite-check --pip-args="--no-cache-dir"`.

## What counts

- The worker's command filter letting a command reach outside its copy of the project.
- Bite sending your code, your API key or anything else somewhere you didn't ask it to.
- The GitHub Action or the bot leaking a secret, or running untrusted pull request code with secrets.

Known limits that aren't holes: without Docker, your project's own tests run with your user's rights.
[AGENTS.md](AGENTS.md) shows `contain_command`, which runs them in a Docker box with no network. A commit that fools Bite into a wrong
result is a [Fool Bite](https://github.com/connabyss/bite/issues/156) entry, not a security report.
