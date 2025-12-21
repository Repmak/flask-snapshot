import threading
import csv
import os
from datetime import datetime
from flask import request, has_request_context
from sqlalchemy import event


class FlaskSnapshot:
    def __init__(self, app=None, db=None, log_file="flask_snapshot_data.csv"):
        self.log_file = log_file
        if app and db:
            self.init_app(app, db)

    def init_app(self, app, db):
        # Create the log file if it doesn't exist.
        if not os.path.exists(self.log_file):
            with open(self.log_file, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "thread_id", "status", "endpoint", "type", "statement", "parameters"])

        # Attach the listener to SQLAlchemy.
        with app.app_context():
            @event.listens_for(db.engine, "before_cursor_execute")
            def intercept(conn, cursor, statement, parameters, context, executemany):
                self._log_event(statement, parameters)

    def _log_event(self, statement, parameters):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")
        thread_id = threading.get_ident()

        # Get the route name.
        endpoint = request.path if has_request_context() else "SYSTEM"

        # Identify if it's a read or write request.
        sql_type = "READ" if statement.strip().upper().startswith("SELECT") else "WRITE"

        with open(self.log_file, mode='a', newline='') as f:
            writer = csv.writer(f)
            # todo get status code to work, instead of placeholder 0
            writer.writerow([timestamp, thread_id, '0', endpoint, sql_type, statement, str(parameters)])

        print(f"[*] Logged {sql_type} for {endpoint}")
