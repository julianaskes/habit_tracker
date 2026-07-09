import sqlite3
from datetime import datetime, date
from habit import Habit


class Storage:
    def __init__(self, db_file="habits.db"):
        self.db_file = db_file
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_file)

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
            for completion_date in habit.completed_dates:
                cursor.execute('''
                    INSERT INTO completions (habit_name, completion_date)
                    VALUES (?, ?)
                ''', (habit.name, completion_date.isoformat()))

            conn.commit()

    def remove_habit(self, habit_name):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM habits WHERE name = ?', (habit_name,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted

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

            # Create habit object
            habit = Habit(
                name=habit_row[0],
                period=habit_row[1],
                created_at=datetime.fromisoformat(habit_row[2])
            )
            habit.streak = habit_row[3]
            habit.longest_streak = habit_row[4]

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

            return habit

    def get_all_habits(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get all habits
            cursor.execute('SELECT name FROM habits')
            habit_names = cursor.fetchall()

            return [
                self.get_habit(name[0])
                for name in habit_names
            ]
