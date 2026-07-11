import sqlite3
from datetime import datetime, date
from habit import Habit


class Storage:
    def __init__(self, db_file="habits.db"):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file)
        self.conn.execute('PRAGMA foreign_keys = ON')
        self.init_db()

    def get_connection(self):
        return self.conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Create habits table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS habits (
                    name TEXT PRIMARY KEY,
                    period TEXT,
                    created_at TEXT,
                    streak INTEGER,
                    longest_streak INTEGER
                )
            ''')

            # Create completions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS completions (
                    habit_name TEXT,
                    completion_date TEXT,
                    FOREIGN KEY (habit_name) REFERENCES habits (name) ON DELETE CASCADE,
                    UNIQUE(habit_name, completion_date)
                )
            ''')

            conn.commit()

    def add_habit(self, habit):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO habits (name, period, created_at, streak, longest_streak)
                VALUES (?, ?, ?, ?, ?)
            ''', (habit.name, habit.period, habit.created_at.isoformat(),
                  habit.streak, habit.longest_streak))

            # Clear and re-insert completions
            cursor.execute(
                'DELETE FROM completions WHERE habit_name = ?', (habit.name,))
            cursor.executemany('''
                INSERT INTO completions (habit_name, completion_date)
                VALUES (?, ?)
            ''', [(habit.name, d.isoformat()) for d in habit.completed_dates])

            conn.commit()

    def remove_habit(self, habit_name):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM habits WHERE name = ?', (habit_name,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted

    def _build_habit(self, habit_row):
        habit = Habit(
            name=habit_row[0],
            period=habit_row[1],
            created_at=datetime.fromisoformat(habit_row[2])
        )
        habit.streak = habit_row[3]
        habit.longest_streak = habit_row[4]
        return habit

    def get_habit(self, habit_name):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get habit details
            cursor.execute('''
                SELECT name, period, created_at, streak, longest_streak
                FROM habits WHERE name = ?
            ''', (habit_name,))

            habit_row = cursor.fetchone()
            if not habit_row:
                return None

            habit = self._build_habit(habit_row)

            # Get completion dates
            cursor.execute('''
                SELECT completion_date FROM completions
                WHERE habit_name = ?
                ORDER BY completion_date
            ''', (habit_name,))

            habit.completed_dates = [
                date.fromisoformat(row[0])
                for row in cursor.fetchall()
            ]

            # The persisted current streak may have lapsed since it was
            # written; refresh it so reads always reflect today.
            habit.recalculate_streaks()
            return habit

    def get_all_habits(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # One query for all habits, one for all completions (avoids N+1).
            cursor.execute('''
                SELECT name, period, created_at, streak, longest_streak
                FROM habits ORDER BY name
            ''')
            habit_rows = cursor.fetchall()
            if not habit_rows:
                return []

            cursor.execute('''
                SELECT habit_name, completion_date FROM completions
                ORDER BY completion_date
            ''')
            completion_rows = cursor.fetchall()

        dates_by_habit = {}
        for habit_name, completion_date in completion_rows:
            dates_by_habit.setdefault(habit_name, []).append(
                date.fromisoformat(completion_date))

        habits = []
        for habit_row in habit_rows:
            habit = self._build_habit(habit_row)
            habit.completed_dates = dates_by_habit.get(habit_row[0], [])
            habit.recalculate_streaks()
            habits.append(habit)
        return habits
