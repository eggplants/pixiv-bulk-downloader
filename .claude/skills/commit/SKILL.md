---
name: commit
description: Analyze the git diff and commit it following this project's conventions.
---

## Steps

1. Read every change with `git status` and `git diff HEAD`
2. Split the changes into logical units and draft a message for each
3. Show the split to the user and wait for approval before committing
4. Commit each unit with `git add <files>` then `git commit -m "..."`
5. Confirm the result with `git log --oneline -5`

## Commit convention

### Subject

```
type: what changed, in English
```

- **type**: `feat` / `fix` / `refactor` / `chore` / `docs` / `test`
- No scope. `feat(cli): ...` is wrong; write `feat: ...`
- Lowercase after the colon, no trailing period, under 50 characters
- A bare noun phrase is fine when it is obvious what happened to it:
  `feat: pyinstaller`, `docs: installation`, `fix: gh pages`
- Otherwise use the imperative or a short phrase naming the change:
  `feat: remove --batch-id from otpa cm`, `fix: skip waiting if already logged-in`
- The very first commit of a repository is `init`, with no type

### Body

Most commits have no body. Add one only when the subject leaves a real question
open, and keep it to a sentence or two saying **why**, not what — the diff
already says what. Bullets are for the rare commit that changes several
unrelated things at once, which usually means it should have been split.

## How to split

| Situation | Call |
|-----------|------|
| A shared/base change plus the callers that use it | Separate commits |
| A feature and its tests | One commit |
| A bug fix and an unrelated refactor | Separate commits |
| Formatter-only churn | Its own `chore: format` commit (usually unnecessary) |
| The same edit repeated across several files | One commit |

## Never

- Add a `Co-Authored-By` or `Claude-Session` trailer
- Write the message in Japanese
- Run `git add -A` or `git add .`; name the files you changed
- Pass `--no-verify`
