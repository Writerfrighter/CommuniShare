from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
import sqlite3

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.secret_key = "I really hope this is really a secret and nobody finds this."
db = SQLAlchemy(app)
connection = sqlite3.connect("requests.db", check_same_thread=False)
c = connection.cursor()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return "<User %r>" % self.username


@app.route("/", methods=["GET", "POST"])
def index():
    errorMsg = None
    if "username" in session:
        loginStatus = session["username"]
    else:
        loginStatus = False

    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    if username.__contains__('"') or username.__contains__("'"):
        return render_template("index.html", message="Invalid Username or Password")
    user = User.query.filter_by(username=username).first()
    if user and password == user.password:
        session["username"] = username
        return redirect("/home")
    else:
        return render_template("index.html", message="Invalid Username or Password")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm-password")

        if username.__contains__('"') or username.__contains__("'"):
            return render_template(
                "signup.html", message="Invalid Username or Password"
            )
        elif User.query.filter_by(username=username).first():
            return render_template(
                "create-account.html", message="Username is allready taken."
            )
        elif password != confirm_password:
            return render_template("signup.html", message="Passwords do not match")

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        session["username"] = username
        return redirect("/home")

    else:
        return render_template("signup.html")


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/")


@app.route("/home")
def home():
    return render_template(
        "home.html",
        list=c.execute("""SELECT * FROM requests""").fetchall(),
        user=session["username"],
    )


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        requester = session["username"]
        description = request.form.get("description")
        day = request.form.get("day")
        time = request.form.get("time")
        print(requester, description, day, time)
        c.execute(
            """INSERT INTO requests (requester, description, date, time, completed) VALUES ('{}', '{}', '{}', '{}', 'Still Active')""".format(
                requester, description, day, time
            )
        )
        connection.commit()

        return redirect("/home")
    else:
        return render_template("add.html", user=session["username"])


@app.route("/myrequests")
def myrequests():
    return render_template(
        "myrequests.html",
        user=session["username"],
        list=c.execute(
            """SELECT * FROM requests WHERE requester="{}" """.format(session["username"])
        ),
    )


@app.route("/update/<id>", methods=["GET", "POST"])
def update(id):
    if request.method == "POST":
        description = request.form.get("description")
        day = request.form.get("day")
        time = request.form.get("time")
        status = request.form.get("status")

        c.execute(
            """UPDATE requests SET description = '{}', date = '{}', time = '{}', completed= '{}' WHERE id = {} """.format(
                description, day, time, status, id
            )
        )
        connection.commit()

        return redirect("/home")
    else:
        return render_template(
            "edit.html",
            user=session["username"],
            request=c.execute(
                """SELECT * FROM requests WHERE id={} """.format(id)
            ).fetchone(),
        )


@app.before_request
def create_tables():
    db.create_all()


def initRequestDataBase():
    c.execute(
        "CREATE TABLE IF NOT EXISTS requests (id INTEGER PRIMARY KEY, requester TEXT, description TEXT, date TEXT, time TEXT, completed TEXT)"
    )
    connection.commit()


initRequestDataBase()
app.run(host="0.0.0.0", port=8000, debug=True)
