import unittest
from datetime import datetime, date, timedelta
import os
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
        # Complete habit for 15 out of last 30 days
        for i in range(0, 30, 2):  # Every other day
            habit.complete(today - timedelta(days=i))
        self.storage.add_habit(habit)

        completion_rate = get_completion_rate(habit)
        self.assertEqual(completion_rate, 50.0)

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

    def test_weekly_completion_rate_counts_distinct_weeks(self):
        # Five completions in a single week count as one week, not five.
        habit = Habit("Weekly Review", "weekly")
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        for i in range(5):  # Mon..Fri of the current week
            habit.complete(monday + timedelta(days=i))

        rate = get_completion_rate(habit)
        self.assertLessEqual(rate, 100.0)
        self.assertEqual(rate, (1 / (30 // 7)) * 100)


if __name__ == '__main__':
    unittest.main()
