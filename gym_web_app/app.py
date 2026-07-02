import sqlite3
from flask import Flask, render_template, request, redirect, session, jsonify
from database import init_db, get_db
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "secret123"

# Init DB
init_db()


# -------- LOGIN --------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin":
            session["user"] = "admin"
            return redirect("/dashboard")
        else:
            return render_template("auth/login.html", error="Invalid login")

    return render_template("auth/login.html")


# -------- DASHBOARD --------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    conn = get_db()
    cursor = conn.cursor()

    # -------- STATS --------
    total_customers = cursor.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    total_packages = cursor.execute("SELECT COUNT(*) FROM packages").fetchone()[0]
    total_revenue = cursor.execute("SELECT SUM(amount) FROM payments").fetchone()[0] or 0

    # -------- CHART --------
    data = cursor.execute("""
        SELECT strftime('%m', date), SUM(amount)
        FROM payments
        GROUP BY strftime('%m', date)
    """).fetchall()

    month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    months = []
    revenue = []

    revenue_dict = {}
    for row in data:
        revenue_dict[row[0]] = row[1]

    for i in range(1, 13):
        key = f"{i:02d}"
        months.append(month_names[i-1])
        revenue.append(revenue_dict.get(key, 0))

    # -------- ALERTS --------
    today = datetime.now().date()

    alerts_data = cursor.execute("""
        SELECT c.name, m.end_date
        FROM memberships m
        JOIN customers c ON m.customer_id = c.id
    """).fetchall()

    alerts = []

    for row in alerts_data:
        end_date = datetime.strptime(row["end_date"], "%Y-%m-%d").date()
        days_left = (end_date - today).days

        if days_left < 0:
            alerts.append({
                "name": row["name"],
                "status": "Expired",
                "days": days_left
            })
        elif days_left <= 3:
            alerts.append({
                "name": row["name"],
                "status": "Expiring",
                "days": days_left
            })

    conn.close()

    return render_template(
        "dashboard/dashboard.html",
        total_customers=total_customers,
        total_packages=total_packages,
        total_revenue=total_revenue,
        months=months,
        revenue=revenue,
        alerts=alerts   # ✅ IMPORTANT
    )


# -------- CUSTOMERS --------
@app.route("/view_customers")
def view_customers():
    if "user" not in session:
        return redirect("/")

    conn = get_db()
    rows = conn.execute("SELECT * FROM customers").fetchall()
    conn.close()

    return render_template("customers/view_customers.html",
        customers=[dict(x) for x in rows]
    )


@app.route("/add_customer", methods=["POST"])
def add_customer():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO customers (name, phone, date) VALUES (?, ?, ?)",
        (request.form["name"], request.form["phone"], request.form["date"])
    )

    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({"id": new_id})


@app.route("/delete_customer/<int:id>")
def delete_customer(id):
    conn = get_db()
    conn.execute("DELETE FROM customers WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "deleted"})


# -------- PACKAGES --------
@app.route("/view_packages")
def view_packages():
    conn = get_db()
    rows = conn.execute("SELECT * FROM packages").fetchall()
    conn.close()

    return render_template("packages/view_packages.html",
        packages=[dict(x) for x in rows]
    )
  


#   ADD PACKAGES 

@app.route("/add_package", methods=["POST"])
def add_package():
    conn = get_db()
    cursor = conn.cursor()

    duration = request.form.get("duration") or 30

    cursor.execute("""
        INSERT INTO packages (type, facilities, cost, duration)
        VALUES (?, ?, ?, ?)
    """, (
        request.form["type"],
        request.form["facilities"],
        request.form["cost"],
        int(duration)
    ))

    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({
    "id": new_id,
    "type": request.form["type"],
    "facilities": request.form["facilities"],
    "cost": request.form["cost"],
    "duration": duration
})


  

#   DELETE PACKAGE 

@app.route("/delete_package/<int:id>")
def delete_package(id):
    conn = get_db()
    conn.execute("DELETE FROM packages WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "deleted"})


# -------- MEMBERSHIP ASSIGN --------
@app.route("/assign_membership", methods=["POST"])
def assign_membership():
    conn = get_db()
    cursor = conn.cursor()

    customer_id = request.form["customer_id"]
    package_id = request.form["package_id"]

    pkg = cursor.execute(
        "SELECT duration FROM packages WHERE id=?",
        (package_id,)
    ).fetchone()

    duration = pkg["duration"] if pkg and pkg["duration"] else 30

    start = datetime.now()
    end = start + timedelta(days=int(duration))

    cursor.execute("""
        INSERT INTO memberships (customer_id, package_id, start_date, end_date, status)
        VALUES (?, ?, ?, ?, ?)
    """, (
        customer_id,
        package_id,
        start.strftime("%Y-%m-%d"),
        end.strftime("%Y-%m-%d"),
        "Active"
    ))

    conn.commit()
    conn.close()

    return redirect("/memberships")


# -------- MEMBERSHIPS VIEW --------
@app.route("/memberships")
def memberships():
    if "user" not in session:
        return redirect("/")
    conn = get_db()
    cursor = conn.cursor()

    today = datetime.now().date()

    data = cursor.execute("""
        SELECT m.id, c.name, p.type, m.start_date, m.end_date
        FROM memberships m
        JOIN customers c ON m.customer_id = c.id
        JOIN packages p ON m.package_id = p.id
    """).fetchall()

    result = []

    for row in data:
        end_date = datetime.strptime(row["end_date"], "%Y-%m-%d").date()
        days = (end_date - today).days

        if days < 0:
            status = "Expired"
        elif days <= 3:
            status = "Expiring"
        else:
            status = "Active"

        result.append({
            "id": row["id"],
            "name": row["name"],
            "type": row["type"],
            "start_date": row["start_date"],
            "end_date": row["end_date"],
            "status": status,
            "days_left": days
        })

    customers = cursor.execute("SELECT * FROM customers").fetchall()
    packages = cursor.execute("SELECT * FROM packages").fetchall()

    conn.close()

    return render_template("memberships/view.html",
        memberships=result,
        customers=[dict(x) for x in customers],
        packages=[dict(x) for x in packages]
    )



# EDIT MEMBERSHIPS 
@app.route("/edit_membership", methods=["POST"])
def edit_membership():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE memberships
        SET start_date=?, end_date=?
        WHERE id=?
    """, (
        request.form["start_date"],
        request.form["end_date"],
        request.form["id"]
    ))

    conn.commit()
    conn.close()

    return redirect("/memberships")

# -------- PAYMENTS --------
@app.route("/add_payment", methods=["GET", "POST"])
def add_payment():
    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        cursor.execute("""
            INSERT INTO payments (customer_id, amount, date)
            VALUES (?, ?, ?)
        """, (
            request.form["customer_id"],
            request.form["amount"],
            request.form["date"]
        ))

        conn.commit()
        conn.close()
        return jsonify({"status": "success"})

    customers = cursor.execute("SELECT * FROM customers").fetchall()
    conn.close()

    return render_template("payments/add_payment.html",
        customers=[dict(x) for x in customers]
    )

@app.route("/delete_membership/<int:id>")
def delete_membership(id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM memberships WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return jsonify({"status": "deleted"})


# -------- LOGOUT --------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# -------- RUN --------
if __name__ == "__main__":
    app.run(debug=True)