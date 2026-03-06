from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os

app = Flask(__name__)

app.secret_key = "secretkey"

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
# DATABASE MODELS
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


class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True)

    password = db.Column(db.String(100))


# -----------------------------
# LOAD DATASET
# -----------------------------

with app.app_context():

    db.create_all()

    if Player.query.count() == 0:

        csv_path = os.path.join(os.path.dirname(__file__), "ipl_dataset.csv")

        df = pd.read_csv(csv_path)

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
# LOGIN PAGE
# -----------------------------

@app.route("/", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username, password=password).first()

        if user:

            session["user"] = username

            return redirect("/dashboard")

        else:

            return "Invalid Login"

    return render_template("login.html")


# -----------------------------
# REGISTER PAGE
# -----------------------------

@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User(username=username, password=password)

        db.session.add(user)
        db.session.commit()

        return redirect("/")

    return render_template("register.html")


# -----------------------------
# DASHBOARD
# -----------------------------

@app.route("/dashboard")
def dashboard():

    search = request.args.get("search")

    if search:

        players = Player.query.filter(Player.name.contains(search)).all()

    else:

        players = Player.query.order_by(Player.current_bid.desc()).all()

    return render_template("app.html", players=players, page="dashboard")


# -----------------------------
# PLAYER DETAILS PAGE
# -----------------------------

@app.route("/player/<int:id>")
def player_page(id):

    player = Player.query.get(id)

    return render_template("app.html", player=player, page="player")


# -----------------------------
# BID SYSTEM
# -----------------------------

@app.route("/bid/<int:id>", methods=["POST"])
def bid(id):

    player = Player.query.get(id)

    bid_amount = int(request.form["bid"])

    if bid_amount > player.current_bid:

        player.current_bid = bid_amount
        db.session.commit()

    return redirect("/dashboard")


# -----------------------------
# LOGOUT
# -----------------------------

@app.route("/logout")
def logout():

    session.pop("user", None)

    return redirect("/")


# -----------------------------

if __name__ == "__main__":
    app.run()