import time
import atexit
import threading
from collections import deque
import datetime
from flask import request, has_request_context, g
from sqlalchemy import event
from rich.console import Console

from .FlaskSnapshotTimeline import FlaskSnapshotTimeline


class FlaskSnapshot:
    def __init__(self, app=None, db=None, max_entries=100):
        self.logs = deque(maxlen=max_entries)
        self.console = Console()

        if app and db:
            self.init_app(app, db)

    def init_app(self, app, db):
        with app.app_context():
            @event.listens_for(db.engine, "before_cursor_execute")
            def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
                context._query_start_time = time.time()

            @event.listens_for(db.engine, "after_cursor_execute")
            def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
                if not has_request_context(): return

                now = time.time()
                start_dt = datetime.datetime.fromtimestamp(context._query_start_time)
                end_dt = datetime.datetime.fromtimestamp(now)

                if 'sql_logs' not in g: g.sql_logs = []
                sql_type = "WRITE" if any(x in statement.upper() for x in ["UPDATE", "INSERT", "DELETE"]) else "READ"

                g.sql_logs.append({
                    "start_time": start_dt.strftime("%H:%M:%S.%f")[:-3],
                    "end_time": end_dt.strftime("%H:%M:%S.%f")[:-3],
                    "duration": round((now - context._query_start_time) * 1000, 2),
                    "thread_id": threading.get_ident(),
                    "endpoint": request.path,
                    "type": sql_type,
                    "statement": statement.strip()
                })

        # Write to the queue once the request is finished.
        @app.after_request
        def finalise_logging(response):
            if hasattr(g, 'sql_logs') and g.sql_logs:
                self.logs.extend(g.sql_logs)
            return response
        atexit.register(self.print_summary)

    def print_summary(self):
        timeline_generator = FlaskSnapshotTimeline(list(self.logs))
        timeline_generator.generate()
