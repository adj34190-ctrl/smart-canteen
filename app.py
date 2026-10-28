from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='student')
    wallet_balance = db.Column(db.Float, default=500.00)

class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    is_veg = db.Column(db.Boolean, default=True)
    in_stock = db.Column(db.Boolean, default=True)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    token_id = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_name = db.Column(db.String(100), nullable=False)
    items_summary = db.Column(db.Text, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), default='Received')
    special_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def setup_database():
    try:
        db.create_all()

        # Seed initial demo users
        if not User.query.filter_by(email='student@college.edu').first():
            db.session.add(User(fullname='Student Adarsh', email='student@college.edu', password='pass123', role='student', wallet_balance=750.0))
            db.session.add(User(fullname='Canteen Master', email='staff@college.edu', password='staff123', role='staff', wallet_balance=0.0))
            db.session.commit()

        # Complete Updated Menu Items List
        master_menu = [
            # Original Essentials
            {'name': 'Samosa Pav (2 Pcs)', 'category': 'Snacks', 'price': 25.0, 'is_veg': True},
            {'name': 'Mumbai Special Vada Pav', 'category': 'Snacks', 'price': 20.0, 'is_veg': True},
            {'name': 'Crispy Butter Masala Dosa', 'category': 'South Indian', 'price': 65.0, 'is_veg': True},
            {'name': 'Creamy White Sauce Pasta', 'category': 'Continental', 'price': 80.0, 'is_veg': True},
            {'name': 'Veg Steamed Momos (6 Pcs)', 'category': 'Street Food', 'price': 50.0, 'is_veg': True},
            {'name': 'Chicken Steamed Momos (6 Pcs)', 'category': 'Street Food', 'price': 70.0, 'is_veg': False},
            {'name': 'Veg Cheese Schezwan Frankie', 'category': 'Rolls & Frankie', 'price': 55.0, 'is_veg': True},
            {'name': 'Crispy Chicken Frankie', 'category': 'Rolls & Frankie', 'price': 75.0, 'is_veg': False},
            {'name': 'Grilled Veg Cheese Sandwich', 'category': 'Snacks', 'price': 55.0, 'is_veg': True},
            {'name': 'Chole Bhature Thali', 'category': 'Meals', 'price': 90.0, 'is_veg': True},
            {'name': 'Cold Coffee with Chocolate', 'category': 'Beverages', 'price': 40.0, 'is_veg': True},
            {'name': 'Fresh Ginger Masala Chai', 'category': 'Beverages', 'price': 15.0, 'is_veg': True}
        ]

        # Sync items without wiping existing orders
        for item_data in master_menu:
            existing = MenuItem.query.filter_by(name=item_data['name']).first()
            if not existing:
                new_item = MenuItem(
                    name=item_data['name'],
                    category=item_data['category'],
                    price=item_data['price'],
                    is_veg=item_data['is_veg'],
                    in_stock=True
                )
                db.session.add(new_item)
        db.session.commit()
    except Exception as e:
        print(f"Database bootstrap warning: {e}")

with app.app_context():
    setup_database()

@app.route("/", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        action = request.form.get("action")
        email = request.form.get("email")
        password = request.form.get("password")

        if action == "login":
            role = request.form.get("role")
            user = User.query.filter_by(email=email, password=password, role=role).first()
            if user:
                session["user_id"] = user.id
                session["username"] = user.fullname
                session["role"] = user.role
                if user.role == "staff":
                    return redirect(url_for("staff_dashboard"))
                return redirect(url_for("student_dashboard"))
            flash("Invalid credentials or role selected.", "error")

        elif action == "register":
            fullname = request.form.get("fullname")
            role = request.form.get("role", "student")
            existing = User.query.filter_by(email=email).first()
            if existing:
                flash("College email already registered.", "error")
            else:
                new_u = User(fullname=fullname, email=email, password=password, role=role, wallet_balance=500.0)
                db.session.add(new_u)
                db.session.commit()
                flash("Registration complete! You can now log in.", "success")

    return render_template("auth.html")

@app.route("/dashboard")
def student_dashboard():
    if session.get("role") != "student":
        return redirect(url_for("auth"))
    
    user = User.query.get(session["user_id"])
    menu_items = MenuItem.query.all()
    user_orders = Order.query.filter_by(user_id=user.id).order_by(Order.id.desc()).all()
    active_order = Order.query.filter(
        Order.user_id == user.id, 
        Order.status.in_(['Received', 'Preparing', 'Ready'])
    ).order_by(Order.id.desc()).first()

    return render_template("student_dashboard.html", user=user, menu=menu_items, orders=user_orders, active_order=active_order)

@app.route("/api/order/place", methods=["POST"])
def place_order():
    if session.get("role") != "student":
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    user = User.query.get(session["user_id"])
    data = request.json or {}
    items = data.get("items", [])
    total_amount = float(data.get("total", 0.0))
    notes = data.get("notes", "")

    if not items or total_amount <= 0:
        return jsonify({"success": False, "message": "Cart cannot be empty!"})

    if user.wallet_balance < total_amount:
        return jsonify({"success": False, "message": "Insufficient Campus Wallet Balance. Please recharge!"})

    user.wallet_balance -= total_amount
    total_orders = Order.query.count() + 101
    token_id = f"T-{total_orders}"

    items_summary = ", ".join([f"{item['qty']}x {item['name']}" for item in items])
    new_order = Order(
        token_id=token_id,
        user_id=user.id,
        student_name=user.fullname,
        items_summary=items_summary,
        total_amount=total_amount,
        special_notes=notes,
        status="Received"
    )
    db.session.add(new_order)
    db.session.commit()

    return jsonify({"success": True, "token_id": token_id, "new_balance": user.wallet_balance})

@app.route("/api/wallet/add-funds", methods=["POST"])
def add_funds():
    if "user_id" not in session:
        return redirect(url_for("auth"))
    amount = float(request.form.get("amount", 200.0))
    user = User.query.get(session["user_id"])
    user.wallet_balance += amount
    db.session.commit()
    return redirect(url_for("student_dashboard"))

@app.route("/staff-console")
def staff_dashboard():
    if session.get("role") != "staff":
        return redirect(url_for("auth"))

    orders = Order.query.order_by(Order.id.desc()).all()
    menu_items = MenuItem.query.all()
    total_revenue = sum([o.total_amount for o in orders])
    completed_count = len([o for o in orders if o.status == 'Completed'])

    return render_template("staff_dashboard.html", 
                           orders=orders, 
                           menu_items=menu_items, 
                           revenue=total_revenue, 
                           completed=completed_count,
                           staff_name=session.get("username", "Canteen Master"))

@app.route("/api/staff/update-order", methods=["POST"])
def staff_update_order():
    if session.get("role") != "staff":
        return jsonify({"error": "Unauthorized"}), 403
    order_id = request.form.get("order_id")
    new_status = request.form.get("status")
    order = Order.query.get(order_id)
    if order:
        order.status = new_status
        db.session.commit()
    return redirect(url_for("staff_dashboard"))

@app.route("/api/staff/toggle-item", methods=["POST"])
def staff_toggle_item():
    if session.get("role") != "staff":
        return jsonify({"error": "Unauthorized"}), 403
    item_id = request.form.get("item_id")
    item = MenuItem.query.get(item_id)
    if item:
        item.in_stock = not item.in_stock
        db.session.commit()
    return redirect(url_for("staff_dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
