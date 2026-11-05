# Ask Bite in plain words

[← Back to the README](https://github.com/connabyss/bite#readme)

## Ask in plain words

```
bite ask "is last week's login fix guarded?"
```

Bite finds the commit(s) that match your words (their message and the files they changed, and the time if you
name one: today, yesterday, this week, last week, the last 10 days) and runs its free check on each. The answer
opens in a few words, then gives a short block per commit:

```
Yes, it's guarded.

✅ YES, A TEST NOTICED
   Fix login letting an empty password in
   3f2a9c1, Oct 27
   With it taken out, test_empty_password_is_refused fails.
```

When no test notices a fix, its block says ⚠️ NO TEST NOTICED. Where emoji can't show (output sent to a file
or another program, or an old Windows console) the labels are the same words without them.

Matching is free. Only when your words match nothing clearly, and you have an API key, a small AI call picks the
commit instead (about a cent); `--free` never uses the key. `--last 200` looks further back. Coding AIs get the
same thing through `bite mcp`, as the tool `ask_bite`.
