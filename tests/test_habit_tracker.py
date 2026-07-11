import unittest
from datetime import datetime, date, timedelta
import os
import sys
import subprocess
import tempfile
from habit import Habit
from storage import Storage
from analytics import get_habit_stats, get_completion_rate


class TestHabitTracker(unittest.TestCase):
    def setUp(self):
        # Use in-memory database for testing
        self.storage = Storage(":memory:")

    def test_habit_creation(self):
        habit = Habit("Exercise", "daily")
        self.storage.add_habit(habit)

        saved_habit = self.storage.get_habit("Exercise")
        self.assertEqual(saved_habit.name, "Exercise")
        self.assertEqual(saved_habit.period, "daily")
        self.assertEqual(saved_habit.streak, 0)

    def test_habit_completion(self):
        habit = Habit("Exercise", "daily")
        self.storage.add_habit(habit)

        today = date.today()
        habit.complete(today)
        self.storage.add_habit(habit)  # Update in storage

        saved_habit = self.storage.get_habit("Exercise")
        self.assertEqual(len(saved_habit.completed_dates), 1)
        self.assertEqual(saved_habit.streak, 1)

    def test_streak_calculation_daily(self):
        habit = Habit("Exercise", "daily")
        self.storage.add_habit(habit)

        today = date.today()
        # Complete habit for three consecutive days
        for i in range(3):
            habit.complete(today - timedelta(days=i))
        self.storage.add_habit(habit)

        saved_habit = self.storage.get_habit("Exercise")
        self.assertEqual(saved_habit.streak, 3)

    def test_streak_calculation_weekly(self):
        habit = Habit("Weekly Review", "weekly")
        self.storage.add_habit(habit)

        today = date.today()
        # Complete habit for three consecutive weeks
        for i in range(3):
            habit.complete(today - timedelta(weeks=i))
        self.storage.add_habit(habit)

        saved_habit = self.storage.get_habit("Weekly Review")
        self.assertEqual(saved_habit.streak, 3)

    def test_streak_break(self):
        habit = Habit("Exercise", "daily")
        self.storage.add_habit(habit)

        today = date.today()
        # Complete habit for today and two days ago (missing yesterday)
        habit.complete(today)
        habit.complete(today - timedelta(days=2))
        self.storage.add_habit(habit)

        saved_habit = self.storage.get_habit("Exercise")
        self.assertEqual(saved_habit.streak, 1)

    def test_completion_rate(self):
        habit = Habit("Exercise", "daily")
        self.storage.add_habit(habit)

        today = date.today()
        # Complete every other day; the earliest is 28 days ago, so the habit
        # is measured over its 29-day tracked span (not the full 30-day window).
        for i in range(0, 30, 2):
            habit.complete(today - timedelta(days=i))
        self.storage.add_habit(habit)

        completion_rate = get_completion_rate(habit)
        self.assertAlmostEqual(completion_rate, 15 / 29 * 100, places=5)

    def test_remove_habit(self):
        habit = Habit("Exercise", "daily")
        self.storage.add_habit(habit)

        self.assertTrue(self.storage.remove_habit("Exercise"))
        self.assertIsNone(self.storage.get_habit("Exercise"))

    def test_longest_streak(self):
        habit = Habit("Exercise", "daily")
        self.storage.add_habit(habit)

        today = date.today()
        # First streak of 5 days
        for i in range(5):
            habit.complete(today - timedelta(days=i))

        # Break the streak
        # Second streak of 3 days
        for i in range(7, 10):
            habit.complete(today - timedelta(days=i))

        self.storage.add_habit(habit)
        saved_habit = self.storage.get_habit("Exercise")
        self.assertEqual(saved_habit.longest_streak, 5)

    def test_streak_grace_period(self):
        # A run ending yesterday is still "current" (not yet broken today).
        habit = Habit("Exercise", "daily")
        today = date.today()
        habit.complete(today - timedelta(days=1))
        habit.complete(today - timedelta(days=2))

        self.assertEqual(habit.streak, 2)

    def test_streak_lapses_when_stale(self):
        # A completed run entirely in the past no longer counts as current,
        # but it is still reflected in the longest streak.
        habit = Habit("Exercise", "daily")
        today = date.today()
        for i in range(5, 8):  # three consecutive days, a week ago
            habit.complete(today - timedelta(days=i))

        self.assertEqual(habit.streak, 0)
        self.assertEqual(habit.longest_streak, 3)

    def test_weekly_streak_lapses_when_stale(self):
        habit = Habit("Weekly Review", "weekly")
        today = date.today()
        habit.complete(today - timedelta(weeks=3))
        habit.complete(today - timedelta(weeks=4))

        self.assertEqual(habit.streak, 0)
        self.assertEqual(habit.longest_streak, 2)

    def test_read_recomputes_stale_streak(self):
        # A habit saved with an active streak whose completions are now all
        # in the past should read back with a current streak of 0.
        habit = Habit("Exercise", "daily")
        today = date.today()
        for i in range(5, 8):  # 3-day run, a week ago
            habit.complete(today - timedelta(days=i))
        habit.streak = 3  # simulate a value persisted while the run was active
        self.storage.add_habit(habit)

        saved = self.storage.get_habit("Exercise")
        self.assertEqual(saved.streak, 0)
        self.assertEqual(saved.longest_streak, 3)

        listed = self.storage.get_all_habits()[0]
        self.assertEqual(listed.streak, 0)
        self.assertEqual(listed.longest_streak, 3)

    def test_daily_completion_rate_capped_at_100(self):
        # 31 completions fit the inclusive 30-day window; rate must not exceed 100%.
        habit = Habit("Exercise", "daily")
        today = date.today()
        for i in range(31):
            habit.complete(today - timedelta(days=i))

        self.assertEqual(get_completion_rate(habit), 100.0)

    def test_weekly_rate_ignores_duplicate_weeks(self):
        # A second completion in the same week must not change the rate.
        created = datetime.now() - timedelta(days=90)
        today = date.today()
        monday = today - timedelta(days=today.weekday())

        once = Habit("Once", "weekly", created_at=created)
        once.complete(monday)

        twice = Habit("Twice", "weekly", created_at=created)
        twice.complete(monday)
        twice.complete(today)  # same (current) week as monday

        self.assertEqual(get_completion_rate(once), get_completion_rate(twice))

    def test_new_habit_not_penalized_for_time_before_creation(self):
        # Created and completed today: fully done for its entire lifetime.
        habit = Habit("Fresh", "daily")
        habit.complete(date.today())

        self.assertEqual(get_completion_rate(habit), 100.0)

    def test_uncomplete_removes_completion_and_recomputes(self):
        habit = Habit("Exercise", "daily")
        today = date.today()
        habit.complete(today)
        habit.complete(today - timedelta(days=1))
        self.assertEqual(habit.streak, 2)

        self.assertTrue(habit.uncomplete(today))
        self.assertEqual(len(habit.completed_dates), 1)
        self.assertEqual(habit.streak, 1)

        # Removing a date that was never completed is a no-op returning False.
        self.assertFalse(habit.uncomplete(today - timedelta(days=10)))

    def test_uncomplete_reduces_longest_streak(self):
        # Correcting a mistaken completion should also correct the longest streak.
        habit = Habit("Exercise", "daily")
        today = date.today()
        habit.complete(today)
        habit.complete(today - timedelta(days=1))
        self.assertEqual(habit.longest_streak, 2)

        habit.uncomplete(today - timedelta(days=1))
        self.assertEqual(habit.longest_streak, 1)

    def test_uncomplete_persists_through_storage(self):
        habit = Habit("Exercise", "daily")
        today = date.today()
        habit.complete(today)
        self.storage.add_habit(habit)

        habit.uncomplete(today)
        self.storage.add_habit(habit)

        saved = self.storage.get_habit("Exercise")
        self.assertEqual(len(saved.completed_dates), 0)


class TestCLI(unittest.TestCase):
    """End-to-end checks that the CLI reports failure via exit code + stderr."""

    def _run(self, *args, cwd):
        repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return subprocess.run(
            [sys.executable, os.path.join(repo, "cli.py"), *args],
            cwd=cwd, capture_output=True, text=True)

    def test_success_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self._run("add", "Exercise", cwd=tmp)
            self.assertEqual(result.returncode, 0)

    def test_error_exits_nonzero_on_stderr(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self._run("complete", "Nonexistent", cwd=tmp)
            self.assertEqual(result.returncode, 1)
            self.assertIn("not found", result.stderr)
            self.assertEqual(result.stdout, "")


if __name__ == '__main__':
    unittest.main()
