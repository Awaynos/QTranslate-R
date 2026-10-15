# How to help the project

[Русский](CONTRIBUTING.md) · **English**

Thanks for stopping by. QTranslate Remake is a small personal project, and any help is welcome: a bug report, a one-line fix, an interface translation, an idea.

## What you can do

- **Report a bug** — [open an issue](https://github.com/Awaynos/QTranslate-R/issues/new) and describe how to reproduce it: what you did, what you expected, what you got.
- **Fix a bug** — even if it is a single line.
- **Add an interface language** — copy `languages/en.json`, rename it for your language (for example `de.json`), translate the values. No code changes needed.
- **Improve the documentation** — README, comments, this guide.
- **Suggest an idea** — short and to the point, in an issue.

## Before you start

- A small fix (a typo, a bug in one function) can be sent right away.
- For a bigger change, open an issue first and describe the plan. That way nobody wastes time.
- Check whether an issue for it is already open.

## Running it locally

```powershell
git clone https://github.com/Awaynos/QTranslate-R.git
cd QTranslate-R

python -m venv _local\.venv
& "_local\.venv\Scripts\python.exe" -m pip install -r requirements.txt
& "_local\.venv\Scripts\python.exe" run.py
```

You need **Python 3.11+**. Only Windows is supported for now.

## Checks

There is no test framework — the `tools/` folder holds small scripts you run manually:

```powershell
.\.venv\Scripts\python.exe tools\core_test.py        # core logic, no network
.\.venv\Scripts\python.exe tools\autopair_test.py    # the "Native–Second" auto pair
.\.venv\Scripts\python.exe tools\providers_test.py   # translators (network required)
.\.venv\Scripts\python.exe tools\dictionary_test.py  # dictionary
.\.venv\Scripts\python.exe tools\document_test.py    # documents
.\.venv\Scripts\python.exe tools\persist_test.py     # settings persistence
```

If you add a feature, add a check next to it, in the same style.

## Code style

- Python 3.11, type annotations, 4-space indentation.
- Comments only where they explain **why**, not **what**. Do not comment the obvious.
- Do not hardcode interface strings: they come from `languages/*.json` through `tr(...)`.
- Do not mix the layers: `domain` knows nothing about the UI, `services` describe contracts, `ui` contains no business logic.
- A new service (translator, dictionary, speech) is a separate module in `qtranslate_r/services/providers/`, registered in `core/setup.py`.

## Commits

Conventional Commits, in English, imperative mood:

```
feat(services): add Mozhi translator
fix(ui): stop clipping the copy button
docs: fix typo in README
```

The scope in brackets is the area: `services`, `ui`, `core`, `config`, `docs`.

## Branches and pull requests

- Branch off `main`: `feature/short-name` or `fix/short-name`.
- In the PR description: what was done, why, and how to verify it.
- If you changed the interface, attach a screenshot.
- One PR — one task.

## Contribution license

The project is distributed under [PolyForm Noncommercial 1.0.0](LICENSE).

By submitting a pull request, you agree that your contribution is licensed under the same terms — it may be freely used, modified and distributed for non-commercial purposes.
