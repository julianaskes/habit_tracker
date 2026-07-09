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


if __name__ == '__main__':
    unittest.main()
