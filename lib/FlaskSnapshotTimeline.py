from datetime import datetime
from rich.console import Console
from enum import Enum
from rich.table import Table
from rich.text import Text


# For sorting.
def parse_time(time_str):
    return datetime.strptime(time_str, '%H:%M:%S.%f')


class ConflictSeverity(Enum):
    # todo ai generated below, needs to be revisited
    STALE_DATA = 10        # Low severity: Non-repeatable/phantom reads.
    USER_ERROR = 20        # Medium severity: Unique constraint violations.
    VALIDATION_BYPASS = 30 # High severity: Data integrity is at risk.
    DATA_LOSS = 40         # Critical severity: Lost update.
    SYSTEM_HALT = 50       # Critical severity: Deadlocks, orphaned records (FK failures).


class FlaskSnapshotTimeline:
    def __init__(self, logs):
        self.logs = logs
        self.console = Console()

    def categorise_conflicts(self, entry1, entry2):
        """
        Determines the type of conflict between two entries (for severity warnings in the console).
        :param entry1: The first entry.
        :param entry2: The second entry.
        :return: An enum value which determines the type of conflict.
        """
        if entry1['type'] == "WRITE" and entry2['type'] == "READ":
            # Thread 1 updates row, but hasn't commited.
            # Thread 2 reads the uncommited value.
            # If thread 1 rolls back, thread 2 will be working with data that never existed.
            return None
        # elif
        return None

    def catch_conflicts(self):
        """
        Iterates through the entries in the logs array to find conflicts.
        :return: A dictionary of all times where conflicts were detected.
        """

        # Sort entries in self.logs by start_time and end_time.
        self.logs.sort(key=lambda x: (parse_time(x['start_time']), parse_time(x['end_time'])))

        conflicts = {}
        left = 0

        for right, entry in enumerate(self.logs):
            # Keep sliding window in a valid range.
            break

            # while left < right and left :


        return conflicts

    def generate_timeline(self):
        if not self.logs:
            self.console.print("Logs empty.")
            return

        # Find conflicts.
        conflicts = self.catch_conflicts()

        return conflicts
