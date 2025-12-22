import datetime
from rich.console import Console
from rich.table import Table
from rich.text import Text


class FlaskSnapshotTimeline:
    def __init__(self, logs):
        self.logs = logs
        self.console = Console()

    def generate(self):
        if not self.logs:
            self.console.print("Logs empty.")
            return

        # todo code for race condition checking etc

        self.console.print("\n")
