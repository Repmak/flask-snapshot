import time
import atexit
import threading
from collections import deque
import datetime
import sqlparse
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

                start_dt, end_dt, duration = self.get_start_dt_end_dt_duration(context._query_start_time)
                statement_tokens = self.get_statement_type(statement)
                g.sql_logs.append({
                    "start_time": start_dt.strftime("%H:%M:%S.%f")[:-3],
                    "end_time": end_dt.strftime("%H:%M:%S.%f")[:-3],
                    "duration": round(duration, 2),
                    "thread_id": threading.get_ident(),
                    "endpoint": request.path,
                    "statement": statement.strip(),
                    "tokens": statement_tokens,
                    "parameters": parameters
                })

            @event.listens_for(db.session, "after_commit")
            def receive_after_commit(session):
                if not has_request_context(): return

                # start_dt, end_dt, duration = self.get_datetimes_and_duration(context._query_start_time)
                # statement_type = self.get_statement_type(statement)
                # g.sql_logs.append({
                #     "start_time": start_dt.strftime("%H:%M:%S.%f")[:-3],
                #     "end_time": end_dt.strftime("%H:%M:%S.%f")[:-3],
                #     "duration": round(duration, 2),
                #     "thread_id": threading.get_ident(),
                #     "endpoint": request.path,
                #     "statement": "COMMIT",
                #     "type": "TRANSACTION",
                #     "parameters": None,
                #     "status": "committed"
                # })

            @event.listens_for(db.session, "after_rollback")
            def receive_after_rollback(session):
                if not has_request_context(): return

                # start_dt, end_dt, duration = self.get_datetimes_and_duration(context._query_start_time)
                # statement_type = self.get_statement_type(statement)
                # g.sql_logs.append({
                #     "start_time": start_dt.strftime("%H:%M:%S.%f")[:-3],
                #     "end_time": end_dt.strftime("%H:%M:%S.%f")[:-3],
                #     "duration": round(duration, 2),
                #     "thread_id": threading.get_ident(),
                #     "endpoint": request.path,
                #     "statement": "COMMIT",
                #     "type": "TRANSACTION",
                #     "parameters": None,
                #     "status": "committed"
                # })

        # todo can be useful to see how delay between api request and actual db access?
        # @app.before_request
        # def start_timer():
        #     g.sql_logs = []
        #     g.request_start_time = time.time()

        # Write to the queue once the request is completed.
        @app.after_request
        def finalise_logging(response):
            if hasattr(g, 'sql_logs') and g.sql_logs:
                self.logs.extend(g.sql_logs)
            return response
        atexit.register(self.print_summary)  # Print summary when the program exits.

    @staticmethod
    def get_start_dt_end_dt_duration(start_time):
        now = time.time()
        start_dt = datetime.datetime.fromtimestamp(start_time)
        end_dt = datetime.datetime.fromtimestamp(now)
        return start_dt, end_dt, (now - start_time) * 1000

    @staticmethod
    def get_statement_type(statement):
        parsed = sqlparse.parse(statement)
        tables = set()
        for token in parsed.flatten():
            if token.ttype is sqlparse.tokens.Name:
                tables.add(str(token))
        return tables

    def print_summary(self):
        timeline_generator = FlaskSnapshotTimeline(list(self.logs))
        timeline_generator.generate_timeline()
