# The comeback alarm

[← Back to the README](https://github.com/connabyss/bite#readme)

## The comeback alarm: a fix that quietly came undone

A fix with no test can be undone by a later commit, and nobody hears about it: a "simplify", a bad merge, an old
copy pasted back. Every free check also looks at whether each fix is still in today's code. If a later commit put
the old code back, Bite says so and names that commit:

```
  e5c329ec 🔁 UNDONE BY A LATER COMMIT   Fix totals showing long decimals like 0.30000000000000004

🔁 UNDONE BY A LATER COMMIT: e5c329ec "Fix totals showing long decimals like 0.30000000000000004": Commit e8b75da4
(“Simplify total()”) put the old code back, so this fix is gone from today's code.
```

`bite --demo comeback` shows it on a tiny made-up shop. It's free and runs no tests: Bite only checks whether the
fix's own change would apply again to today's code (and can't be taken back out of it). It works for fixes a test
noticed too, since a fix and its test can be deleted together. A later commit whose title says it's a revert was
done on purpose, so that one gets a quiet note instead of the alarm. A fix rewritten into new code doesn't count as
undone, and neither does one a later commit did another way (it took the fix's lines out but wrote its own code for
the same thing in the same function). A revert or a tidy-up that came undone gets no alarm either. When a branch is
merged after the undo, Bite names the commit that put the old code back, not the merge.
