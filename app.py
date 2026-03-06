from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os

app = Flask(__name__)

# -----------------------------
# DATABASE CONFIGURATION
# -----------------------------

database_url = os.getenv("DATABASE_URL")

if database_url:
    database_url = database_url.replace("postgres://", "postgresql://")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///ipl.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# -----------------------------
# DATABASE MODEL
# -----------------------------

class Player(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100))
    role = db.Column(db.String(50))
    country = db.Column(db.String(50))

    runs = db.Column(db.Integer)
    strike_rate = db.Column(db.Float)

    base_price = db.Column(db.Integer)
    current_bid = db.Column(db.Integer)


# -----------------------------
# LOAD DATASET INTO DATABASE
# -----------------------------

with app.app_context():

    db.create_all()

    if Player.query.count() == 0:

        # Correct CSV path for Render
        csv_path = os.path.join(os.path.dirname(__file__), "ipl_dataset.csv")

        df = pd.read_csv(csv_path, encoding="utf-8")

        for _, row in df.iterrows():

            player = Player(
                name=row["Player"],
                role="Batsman",
                country=row["COUNTRY"],
                runs=row["Runs"],
                strike_rate=row["SR"],
                base_price=1000000,
                current_bid=1000000
            )

            db.session.add(player)

        db.session.commit()


# -----------------------------
# DASHBOARD
# -----------------------------

@app.route("/")
def dashboard():

    players = Player.query.order_by(Player.current_bid.desc()).all()

    return render_template(
        "app.html",
        players=players,
        page="dashboard"
    )


# -----------------------------
# PLAYER DETAILS PAGE
# -----------------------------

@app.route("/player/<int:id>")
def player_page(id):

    player = Player.query.get_or_404(id)

    return render_template(
        "app.html",
        player=player,
        page="player"
    )


# -----------------------------
# BID SYSTEM
# -----------------------------

@app.route("/bid/<int:id>", methods=["POST"])
def bid(id):

    player = Player.query.get_or_404(id)

    bid_amount = int(request.form["bid"])

    if bid_amount > player.current_bid:
        player.current_bid = bid_amount
        db.session.commit()

    return redirect("/")


# -----------------------------
# RUN APP (LOCAL ONLY)
# -----------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)