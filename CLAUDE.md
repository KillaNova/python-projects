# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running Scripts

No build system or package manager. Run scripts directly with Python:

```
python <script.py>
```

The only external dependency is `requests` (used in `Python_API.py` and `project_BTC_API`). Install it with:

```
pip install requests
```

## Project Structure

This is a Python learning repository. Each file is a standalone script — not a package:

- `python_project_1` — variables, file I/O (`profiel.txt`), basic OOP (classes `person`, `persoon_1`, `my_religion`)
- `python_course.py` — variables, conditionals, loops, functions
- `Python_getallen.py` — exception handling (`ZeroDivisionError`, `ValueError`), interactive `input()`
- `Libraries.py` — standard library demos: `datetime`, `os`, `json` (writes/reads `profiel.json`)
- `Python_API.py` — fetches live BTC-EUR price from Coinbase API
- `project_BTC_API` — extends `Python_API.py`: fetches BTC price and appends a timestamped entry to `tracker.json`

Generated data files (`profiel.txt`, `profiel.json`, `tracker.json`) are outputs of the scripts, not source files.

Note: several files (`python_project_1`, `project_BTC_API`, `BASIC`) have no `.py` extension — they are still plain Python scripts.

The `.vscode/CRUD_API-FAST_API/` directory is a work-in-progress FastAPI CRUD project. If expanding it, `fastapi` and `uvicorn` will be needed (`pip install fastapi uvicorn`).

## Language

Code comments and variable names mix Dutch and English. Both are intentional — keep that convention when editing.
