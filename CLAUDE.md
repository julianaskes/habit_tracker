# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Habit Tracker CLI — a Python command-line app for tracking daily/weekly habits with streaks and completion rates, backed by SQLite3. No external dependencies; standard library only (`argparse`, `sqlite3`, `datetime`).

## Commands

Run the CLI (from repo root):
```bash
python cli.py add "Exercise" --period daily
python cli.py complete "Exercise" --date 2025-10-07
python cli.py list
python cli.py remove "Exercise"
```

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

- `habit.py` — `Habit` is a plain in-memory model (name, period, completed_dates, streak, longest_streak). `complete()` appends a date and recalculates streaks via `_calculate_streak()`. Streak math differs by period: `daily` habits require consecutive calendar days (step=1); `weekly` habits collapse completions to their Monday-aligned week before checking for consecutive weeks (step=7), so multiple completions in the same week don't inflate the streak.
- `storage.py` — `Storage` owns the SQLite connection and schema (`habits` + `completions` tables, FK cascade on delete). `add_habit()` does a full replace: upserts the habit row, then deletes and re-inserts all completions for that habit. There's no incremental completion insert — the whole `Habit` object (with its full `completed_dates` list) is round-tripped through storage on every save. Defaults to `habits.db` in the working directory; tests use `Storage(":memory:")`.
- `analytics.py` — pure functions operating on a `Habit` (or list of `Habit`s) to produce stats dicts. `get_completion_rate()` compares actual completions in the last N days against an expected count (`days` for daily, `days // 7` for weekly).
- `cli.py` — `HabitTrackerCLI` wraps a `Storage` instance and adapts `argparse` subcommands (`add`, `complete`, `remove`, `list`) to storage/analytics calls. Note the read-modify-write pattern in `complete_habit()`: it fetches the habit from storage, mutates it in memory, then calls `storage.add_habit()` again to persist (see `add_habit`'s full-replace behavior above).

Data flows one direction per command: CLI parses args → loads/creates a `Habit` → mutates it → persists the whole object back via `Storage`. There's no in-process caching between commands; each CLI invocation is a fresh process with its own SQLite connection.
