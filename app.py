from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "smart_canteen_super_secret_key"
DB_NAME = "canteen.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS menu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        category TEXT,
        price REAL,
        in_stock INTEGER DEFAULT 1
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token_id TEXT,
        student_name TEXT,
        items TEXT,
        total_amount REAL,
        status TEXT,
        timestamp TEXT
    )''')
    c.execute("INSERT OR IGNORE INTO users (id, fullname, email, password, role) VALUES (1, 'Student Adarsh', 'student@college.edu', 'pass123', 'student')")
    c.execute("INSERT OR IGNORE INTO users (id, fullname, email, password, role) VALUES (2, 'Canteen Master', 'staff@college.edu', 'staff123', 'staff')")
    c.execute("SELECT count(*) FROM menu")
    if c.fetchone()[0] == 0:
        default_items = [
            ('Samosa Pav', 'Snacks', 20.00, 1),
            ('Veg Cheese Sandwich', 'Snacks', 45.00, 1),
            ('Masala Dosa', 'Meals', 50.00, 1),
            ('Cold Coffee', 'Beverages', 30.00, 1),
            ('Hot Chai', 'Beverages', 15.00, 1)
        ]
        c.executemany("INSERT INTO menu (name, category, price, in_stock) VALUES (?, ?, ?, ?)", default_items)
    conn.commit()
    conn.close()

init_db()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT fullname, role FROM users WHERE email=? AND password=? AND role=?", (email, password, role))
        user = c.fetchone()
        conn.close()
        if user:
            session["username"] = user[0]
            session["email"] = email
            session["role"] = user[1]
            return redirect(url_for("kitchen" if user[1] == "staff" else "menu"))
        return render_template("login.html", error="Invalid credentials or role.")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form.get("fullname")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        role = request.form.get("role", "student")
        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match!")
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT INTO users (fullname, email, password, role) VALUES (?, ?, ?, ?)", (fullname, email, password, role))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return render_template("register.html", error="Email already registered.")
    return render_template("register.html")

@app.route("/menu")
def menu():
    if session.get("role") != "student":
        return redirect(url_for("login"))
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, name, category, price, in_stock FROM menu")
    items = c.fetchall()
    conn.close()
    return render_template("menu.html", items=items, username=session.get("username", "Student"))

@app.route("/cart", methods=["GET", "POST"])
def cart():
    if session.get("role") != "student":
        return redirect(url_for("login"))
    if request.method == "POST":
        order_details = request.form.get("order_items", "1x Veg Cheese Sandwich, 1x Cold Coffee")
        total_amount = float(request.form.get("total_amount", 75.00))
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT count(*) FROM orders")
        order_count = c.fetchone()[0] + 101
        token_id = f"T-{order_count}"
        now = datetime.now().strftime("%I:%M %p")
        c.execute("INSERT INTO orders (token_id, student_name, items, total_amount, status, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                  (token_id, session.get("username"), order_details, total_amount, "Received", now))
        conn.commit()
        conn.close()
        return redirect(url_for("token", token_id=token_id))
    return render_template("cart.html")

@app.route("/token/<token_id>")
def token(token_id):
    if "role" not in session:
        return redirect(url_for("login"))
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT token_id, student_name, items, total_amount, status, timestamp FROM orders WHERE token_id=?", (token_id,))
    order = c.fetchone()
    conn.close()
    if not order:
        return redirect(url_for("menu"))
    return render_template("token.html", order=order)

@app.route("/kitchen")
def kitchen():
    if session.get("role") != "staff":
        return redirect(url_for("login"))
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, token_id, student_name, items, total_amount, status, timestamp FROM orders ORDER BY id DESC")
    orders = c.fetchall()
    c.execute("SELECT id, name, price, in_stock FROM menu")
    menu_items = c.fetchall()
    conn.close()
    return render_template("kitchen.html", orders=orders, menu_items=menu_items, staff_name=session.get("username"))

@app.route("/api/order/status", methods=["POST"])
def update_order_status():
    if session.get("role") != "staff":
        return jsonify({"error": "Unauthorized"}), 403
    order_id = request.form.get("order_id")
    new_status = request.form.get("status")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE orders SET status=? WHERE id=?", (new_status, order_id))
    conn.commit()
    conn.close()
    return redirect(url_for("kitchen"))

@app.route("/api/menu/stock", methods=["POST"])
def toggle_menu_stock():
    if session.get("role") != "staff":
        return jsonify({"error": "Unauthorized"}), 403
    item_id = request.form.get("item_id")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE menu SET in_stock = 1 - in_stock WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("kitchen"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
