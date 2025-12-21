import os
import csv
import time
import threading
from datetime import datetime
from flask import Flask, request, has_request_context, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event


class FlaskSnapshot:
    def __init__(self, app=None, db=None, log_file="flask_snapshot_data.csv"):
        self.log_file = log_file
        if app and db:
            self.init_app(app, db)

    def init_app(self, app, db):
        # Create CSV file if it doesn't exist.
        if not os.path.exists(self.log_file):
            with open(self.log_file, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "start_time", "end_time", "duration_ms", "thread_id", "status_code", "endpoint", "sql_type", "statement", "parameters"
                ])

        with app.app_context():
            @event.listens_for(db.engine, "before_cursor_execute")
            def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
                # Store the start time on the context object itself to ensure thread safety
                context._query_start_time = time.time()

            @event.listens_for(db.engine, "after_cursor_execute")
            def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
                if not has_request_context():
                    return

                now = time.time()
                duration = (now - context._query_start_time) * 1000

                start_dt = datetime.fromtimestamp(context._query_start_time)
                end_dt = datetime.fromtimestamp(now)

                if 'sql_logs' not in g:
                    # Create an array for storage if not already created.
                    g.sql_logs = []

                sql_type = "READ" if statement.strip().upper().startswith("SELECT") else "WRITE"

                g.sql_logs.append({
                    "start_time": start_dt.strftime("%H:%M:%S.%f")[:-1],
                    "end_time": end_dt.strftime("%H:%M:%S.%f")[:-1],
                    "duration": round(duration, 3),
                    "thread_id": threading.get_ident(),
                    "endpoint": request.path,
                    "type": sql_type,
                    "statement": statement.replace('\n', ' ').strip(),
                    "parameters": str(parameters)
                })

        # Write to CSV once the request is finished.
        @app.after_request
        def finalize_logging(response):
            if hasattr(g, 'sql_logs') and g.sql_logs:
                try:
                    with open(self.log_file, mode='a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        for log in g.sql_logs:
                            writer.writerow([
                                log["start_time"],
                                log["end_time"],
                                log["duration"],
                                log["thread_id"],
                                response.status_code,
                                log["endpoint"],
                                log["type"],
                                log["statement"],
                                log["parameters"]
                            ])
                except Exception as e:
                    app.logger.error(f"Failed to write SQL logs: {e}")

            return response
