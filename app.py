import mysql.connector
from functools import wraps
from datetime import datetime
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
)


def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="",
        database="alteruse",
    )
    return connection


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session.permanent = True
        if "loggedin" not in session:
            print("Please log in to access this page.")
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated_function


app = Flask(__name__)
app.secret_key = "AlterUSE"


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM user WHERE user_email = %s", (email,))
            account = cursor.fetchone()

            if account and account["user_password"] == password:
                session.update(
                    {
                        "loggedin": True,
                        "id": account["user_id"],
                        "username": account["user_name"],
                        "password": account["user_password"],
                        "email": account["user_email"],
                        "points": account["user_points"],
                        "date": account["user_joining_date"],
                    }
                )
                return redirect(url_for("dashboard"))
            else:
                print("Incorrect username/password!")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            if "conn" in locals():
                conn.close()

    return render_template("index.html")


@app.route("/signup", methods=["POST", "GET"])
def signup():

    if request.method == "POST":
        name = request.form["name"]
        location = request.form["location"]
        email = request.form["email"]
        password = request.form["password"]
        points = 0

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE user_email = %s", (email,))
            account = cursor.fetchone()

            if account:
                print("Account already exists!")
            else:
                cursor.execute(
                    "INSERT INTO user (user_name, user_email, user_password, user_location, user_points) VALUES (%s, %s, %s, %s, %s)",
                    (name, email, password, location, points),
                )
                print("Account created successfully!")
                conn.commit()

        except Exception as e:
            print(f"Error: {e}")

        finally:
            if "conn" in locals():
                conn.close()

        return redirect(url_for("index"))

    return render_template("signup.html")


@app.route("/logout")
def logout():
    session.clear()
    print("You have been logged out.")
    return redirect(url_for("index"))


@app.route("/logout_inactivity", methods=["POST"])
def logout_inactivity():
    session.clear()
    print("User logged out due to inactivity.")
    return jsonify({"success": True})


@app.route("/dashboard")
@login_required
def dashboard():
    username = session.get("username")
    user_id = session.get("id")
    points = session.get("points")
    date = session.get("date")
    password = session.get("password")

    total_bottles = total_cans = total_cups = 0

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT user_location FROM user WHERE user_id = %s", (user_id,))
        user_data = cursor.fetchone()
        location = user_data.get("user_location", "") if user_data else ""

        cursor.execute(
            """
            SELECT user_history_date, bottles, cans, cups, user_history_branch 
            FROM user_history 
            WHERE user_id = %s 
            ORDER BY user_history_date DESC
            """,
            (user_id,),
        )
        submissions = cursor.fetchall()

        cursor.execute(
            """
                SELECT 
                    COALESCE(SUM(bottles), 0) AS total_bottles,
                    COALESCE(SUM(cans), 0)    AS total_cans,
                    COALESCE(SUM(cups), 0)    AS total_cups
                FROM user_history
                WHERE user_id = %s
            """,
            (user_id,),
        )
        summary = cursor.fetchone() or {}

        total_bottles = summary.get("total_bottles", 0)
        total_cans = summary.get("total_cans", 0)
        total_cups = summary.get("total_cups", 0)
    except Exception as e:
        print(f"Error: {e}")
        submissions = []
        location = ""
        total_bottles = total_cans = total_cups = 0
    finally:
        if "conn" in locals():
            conn.close()

    try:
        date_obj = datetime.strptime(date, "%a, %d %b %Y %H:%M:%S GMT")
        formatted_date = date_obj.strftime("%B %d, %Y")
    except Exception:
        formatted_date = str(date) if date else ""

    return render_template(
        "dashboard.html",
        username=username,
        password=password,
        email=session.get("email"),
        date=formatted_date,
        points=points,
        location=location,
        submissions=submissions,
        total_bottles=total_bottles,
        total_cans=total_cans,
        total_cups=total_cups,
    )


@app.route("/submit", methods=["POST", "GET"])
@login_required
def submit():
    if request.method == "GET":
        return redirect(url_for("dashboard"))

    branch = request.form["branch"]
    bottle_quantity = request.form.get("bottle-quantity", 0, type=int)
    can_quantity = request.form.get("can-quantity", 0, type=int)
    cup_quantity = request.form.get("cup-quantity", 0, type=int)

    user_id = session.get("id")
    if not user_id:
        print("Please log in to submit an order.")
        return redirect(url_for("index"))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
                INSERT INTO user_history (user_id, bottles, cans, cups, user_history_date, user_history_branch) 
                VALUES (%s, %s, %s, %s, NOW(), %s)
            """,
            (user_id, bottle_quantity, can_quantity, cup_quantity, branch),
        )

        bottle_points = bottle_quantity * 2
        can_points = can_quantity * 3
        cup_points = cup_quantity * 1
        total_points = bottle_points + can_points + cup_points

        cursor.execute(
            "UPDATE user SET user_points = user_points + %s WHERE user_id = %s",
            (total_points, user_id),
        )
        session["points"] = session.get("points", 0) + total_points
        conn.commit()
        print("Submission successful!")
    except Exception as e:
        print(f"Error: {e}")
        print("An error occurred during submission.")
    finally:
        if "conn" in locals():
            conn.close()

    return redirect(url_for("dashboard"))


@app.route("/update_profile", methods=["POST"])
@login_required
def update_profile():
    data = request.get_json()
    name = data.get("name")
    password = (data.get("password") or "").strip()
    location = data.get("location")
    user_id = session.get("id")

    if not name or not location:
        return jsonify({"success": False, "message": "Name and location are required"})

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE user SET user_name = %s, user_password = %s, user_location = %s WHERE user_id = %s",
            (name, password, location, user_id),
        )
        conn.commit()

        session["username"] = name
        session["password"] = password

        return jsonify({"success": True})
    except Exception as e:
        print(f"Error updating profile: {e}")
        return jsonify({"success": False, "message": "Database error occurred"})
    finally:
        if "conn" in locals():
            conn.close()


@app.route("/withdraw", methods=["POST"])
@login_required
def withdraw():
    data = request.get_json()
    withdrawal_amount = data.get("amount", 0)
    user_id = session.get("id")
    points = session.get("points", 0)

    if withdrawal_amount <= 0:
        return jsonify({"success": False, "message": "Invalid withdrawal amount."})

    if withdrawal_amount > points:
        return jsonify({"success": False, "message": "Insufficient points available."})

    points -= withdrawal_amount
    session["points"] = points

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE user SET user_points = %s WHERE user_id = %s",
            (points, user_id),
        )
        conn.commit()

    except Exception as e:
        print(f"Error: {e}")
        return jsonify(
            {"success": False, "message": "An error occurred during withdrawal."}
        )
    finally:
        if "conn" in locals():
            conn.close()

    return jsonify({"success": True, "new_balance": points})


if __name__ == "__main__":
    app.run(host="0.0.0.0")
