import time
import threading
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from lib.FlaskSnapshot import FlaskSnapshot


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bank.db'
db = SQLAlchemy(app)
flask_snapshot = FlaskSnapshot(app, db)

USERNAME = 'admin'
USER_FUNDS = 100


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    balance = db.Column(db.Integer)


@app.route('/status')
def status():
    acc = Account.query.filter_by(name=USERNAME).first()
    return {"name": acc.name, "balance": acc.balance}


@app.route('/withdraw', methods=['POST'])
def withdraw():
    data = request.get_json()
    amount = data.get('amount', 0)
    acc = Account.query.filter_by(name=USERNAME).first()
    current_balance = acc.balance

    # Simulate processing time to trigger race condition.
    print(f"Thread {threading.get_ident()} is processing...")
    time.sleep(3)

    if current_balance >= amount:
        acc.balance = current_balance - amount
        db.session.commit()
        return {"msg": f"Withdrew {amount}", "new_balance": acc.balance}, 200
    return {"msg": "Insufficient funds"}, 400


with app.app_context():
    # Clear tables and re-create them.
    db.drop_all()
    db.create_all()
    # Insert data.
    user = Account(name=USERNAME, balance=USER_FUNDS)
    db.session.add(user)
    db.session.commit()


if __name__ == "__main__":
    app.run(debug=True, port=5000, threaded=True)
