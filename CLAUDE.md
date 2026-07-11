# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Habit Tracker CLI — a Python command-line app for tracking daily/weekly habits with streaks and completion rates, backed by SQLite3. No external dependencies; standard library only (`argparse`, `sqlite3`, `datetime`).

## Commands

Run the CLI (from repo root):
```bash
python cli.py add "Exercise" --period daily
python cli.py complete "Exercise" --date 2025-10-07
python cli.py uncomplete "Exercise" --date 2025-10-07   # remove a logged completion
python cli.py show "Exercise"                            # one habit + completion history
python cli.py list
python cli.py remove "Exercise"
```

Commands exit non-zero and write errors to stderr on failure (e.g. unknown
habit, bad date), so they compose in scripts; success messages go to stdout.

Run tests:
```bash
python -m pytest                          # all tests (pytest.ini sets testpaths=tests)
python -m pytest tests/test_habit_tracker.py::TestHabitTracker::test_habit_completion  # single test
python -m pytest --cov                     # with coverage (coverage config lives in pytest.ini)
```

Generate sample data for manual testing/exploration:
```bash
python tests/generate_test_data.py         # writes to test_habits.db, 4 weeks of synthetic habits
```

## Architecture

Four modules, each with a single responsibility:

- `habit.py` — `Habit` is a plain in-memory model (name, period, completed_dates, streak, longest_streak). `complete()`/`uncomplete()` add/remove a date and recompute via `_calculate_streak()`. Streak math differs by period: `daily` habits require consecutive calendar days (step=1); `weekly` habits collapse completions to their Monday-aligned week before checking consecutive weeks (step=7). The **current streak lapses**: it only counts if the most recent completion is within one step of today/this week (a grace period), else it's 0 — so it depends on `date.today()`. `longest_streak` is derived purely from the full history (so `uncomplete` can lower it). Storage read paths call the public `recalculate_streaks()` after loading so reads reflect today.
- `storage.py` — `Storage` owns the SQLite connection and schema (`habits` + `completions` tables, FK cascade on delete). `add_habit()` does a full replace: upserts the habit row, then deletes and re-inserts all completions (via `executemany`). The whole `Habit` object is round-tripped on every save. `get_all_habits()` avoids the N+1 pattern by batch-loading all completions in one query. The persisted `streak`/`longest_streak` columns are effectively a cache — reads always recompute. Defaults to `habits.db`; tests use `Storage(":memory:")`.
- `analytics.py` — pure functions producing stats dicts. `get_completion_rate()` measures completions against the habit's **tracked span** (from `created_at`, or its first completion if earlier) intersected with the last N days, so new habits aren't judged against days they didn't exist; weekly counts distinct Monday-weeks, and the rate is clamped to 100%.
- `cli.py` — `HabitTrackerCLI` wraps a `Storage` and adapts `argparse` subcommands (`add`, `complete`, `uncomplete`, `remove`, `show`, `list`) to storage/analytics calls. Each command method returns a bool; `main()` maps that to the process exit code, and errors print to stderr via `_error()`. Note the read-modify-write pattern: fetch the habit, mutate in memory, `storage.add_habit()` to persist (see `add_habit`'s full-replace behavior above).

Data flows one direction per command: CLI parses args → loads/creates a `Habit` → mutates it → persists the whole object back via `Storage`. There's no in-process caching between commands; each CLI invocation is a fresh process with its own SQLite connection.
