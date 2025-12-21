import sqlalchemy.event as event


class FlaskSnapshot:
    def __init__(self, app=None, db=None):
        if app and db:
            self.init_app(app, db)

    def init_app(self, app, db):
        # Listen for every query execution on the engine
        event.listen(db.engine, "before_cursor_execute", self.log_query)

    def log_query(self, conn, cursor, statement, parameters, context, executemany):
        # Here you extract the SQL and the thread ID
        # Send this data to your dashboard!
        print(f"Intercepted SQL: {statement}")
