# Contributing to Game Jam API

Thanks for helping out! This guide explains how we work so your pull request
can be merged quickly.

## Before you start

1. **Search the issues first.** Someone may have already reported it.
2. **Check whether the issue is taken.** If someone commented that they're
   working on it, pick another one or ask if they still need help.
3. **Comment on the issue to claim it** before you start, e.g. "I'd like to
   work on this. My plan is ...".
4. **Big changes need a discussion first.** New features, new dependencies,
   or changes to how things are structured: open an issue and wait for a
   maintainer to agree before you write code.
5. **Security bugs are different.** Don't open an issue. Follow
   [SECURITY.md](SECURITY.md).

## Setting up

```bash
git clone https://github.com/<you>/Opensource-mock.git
cd Opensource-mock
git checkout -b fix/short-description
python -m unittest discover -s tests -t .    # all tests should pass before you change anything
```

## How the code is organized

- **Routes** (`gamejam/routes/`) only read the request and call a service.
  Keep them thin.
- **Services** (`gamejam/services/`) hold the logic. Most fixes go here.
- **Helpers** (`gamejam/utils/`) are shared. **Search them before writing a new
  helper:** there is already code for dates and deadlines, pagination, CSV,
  slugs and more. Pull requests that duplicate an existing helper will be
  asked to reuse it.
- Raise the errors from `gamejam/errors.py` (`NotFound`, `BadRequest`, ...)
  instead of returning error dicts by hand.

## Style

- Follow the style of the code around you (PEP 8, 4 spaces, max ~100 chars).
- Use clear names. No single-letter variables outside short loops.
- Use `?` placeholders in SQL. **Never** build SQL with f-strings and user input.

## Tests

- Every bug fix needs a test that fails before your fix and passes after.
- Every new feature needs tests.
- Run the whole suite before you push:
  `python -m unittest discover -s tests -t .`

## Commits and pull requests

- One fix or feature per pull request. Don't mix unrelated changes.
- Write commit messages in the imperative: "Fix team size check", not
  "fixed stuff".
- Fill in the pull request template: what changed, why, and how you tested it.
- Link the issue with `Fixes #12`.
- Expect review comments. Changes requested is normal!

## Using AI tools

You can use AI assistants, but:

- You must understand and be able to explain every line you submit.
- Check that the AI reused existing helpers instead of inventing new ones.
- Say in your pull request description if AI wrote a significant part of it.

## Code of conduct

Be kind. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
