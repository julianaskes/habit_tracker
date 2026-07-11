from datetime import datetime, date, timedelta


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

    def uncomplete(self, completion_date=None):
        """Remove a logged completion. Returns True if one was removed."""
        completion_date = completion_date or date.today()
        if completion_date in self.completed_dates:
            self.completed_dates.remove(completion_date)
            self._calculate_streak()
            return True
        return False

    def recalculate_streaks(self):
        """Recompute current/longest streak from completed_dates as of today.

        The current streak lapses over time, so a value persisted while a
        habit was active can be stale when re-read on a later day. Callers
        that load a habit from storage should invoke this to refresh it.
        """
        self._calculate_streak()

    def _calculate_streak(self):
        if not self.completed_dates:
            self.streak = 0
            self.longest_streak = 0
            return

        today = date.today()
        if self.period == "weekly":
            # Collapse completions to one entry per calendar week (Monday-aligned)
            # so multiple completions in the same week don't inflate the streak.
            dates = sorted({d - timedelta(days=d.weekday()) for d in self.completed_dates})
            step = 7
            reference = today - timedelta(days=today.weekday())
        else:
            dates = sorted(set(self.completed_dates))
            step = 1
            reference = today

        current_streak = 1
        longest_in_history = 1
        for i in range(len(dates) - 1):
            date_diff = (dates[i + 1] - dates[i]).days
            if date_diff == step:
                current_streak += 1
            else:
                current_streak = 1
            longest_in_history = max(longest_in_history, current_streak)

        # The run above ends at the most recent completion. It only counts as
        # the *current* streak if that completion is still alive: today/this
        # week (gap 0) or one step ago (grace period so an as-yet-undone today
        # doesn't read as broken). If the last completion is older, the streak
        # has lapsed and the current streak is zero.
        gap = (reference - dates[-1]).days
        self.streak = current_streak if gap <= step else 0
        # Derived purely from the full completion history, so it stays accurate
        # even when a completion is removed via uncomplete().
        self.longest_streak = longest_in_history

    def __repr__(self):
        return f"Habit(name='{self.name}', period='{self.period}', streak={self.streak})"
