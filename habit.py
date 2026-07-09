from datetime import datetime, date


class Habit:
    def __init__(self, name, period="daily", created_at=None):
        self.name = name
        self.period = period  # "daily" or "weekly"
        self.created_at = created_at or datetime.now()
        self.completed_dates = []
        self.streak = 0
        self.longest_streak = 0

    def complete(self, completion_date=None):
        completion_date = completion_date or date.today()
        if completion_date not in self.completed_dates:
            self.completed_dates.append(completion_date)
            self._calculate_streak()

    def _calculate_streak(self):
        if not self.completed_dates:
            self.streak = 0
            return

        sorted_dates = sorted(self.completed_dates)
        current_streak = 1
        for i in range(len(sorted_dates) - 1):
            date_diff = (sorted_dates[i + 1] - sorted_dates[i]).days
            if (self.period == "daily" and date_diff == 1) or \
               (self.period == "weekly" and date_diff <= 7):
                current_streak += 1
            else:
                current_streak = 1

        self.streak = current_streak
        self.longest_streak = max(self.longest_streak, current_streak)

    def __repr__(self):
        return f"Habit(name='{self.name}', period='{self.period}', streak={self.streak})"
