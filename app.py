from flask import Flask, session, render_template, request, redirect, url_for, flash, jsonify
from database import db, Customers, Users, Cart, CartItem, Burger, Pizza, Taco, Dessert
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests



app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'LONGa23w342q222224'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# app.py
app.config["PAYSTACK_PUBLIC_KEY"] = "pk_test_e21932b882889bfdd6dff83d25c03c0900061a38"
app.config["PAYSTACK_SECRET_KEY"] = "sk_test_70fd3c240878dcccf9766f459984e96c70547cba"


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))
# Initialize & create tables
db.init_app(app)
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def index():
    if 'email' in session:
        user =  Users.query.filter_by(email=session['email']).first()
        carts = user.cart
        items = carts.items
        cart_c = len(items)
        return render_template('home.html', cart_c=cart_c, user=user, id=session['id'], phone=session['phone'], email=session['email'])

    return render_template('home.html')

@app.route('/categories')
def categories():
    if 'email' in session:
        user = Users.query.filter_by(email=session['email']).first()
        carts = user.cart
        items = carts.items
        cart_c = len(items)
        # products
        burger = Burger.query.order_by(Burger.created_at.desc()).all()
        pizza = Pizza.query.order_by(Pizza.created_at.desc()).all()
        taco = Taco.query.order_by(Taco.created_at.desc()).all()
        dessert = Dessert.query.order_by(Dessert.created_at.desc()).all()
        return render_template('categories.html', cart_c=cart_c, burger=burger, pizza=pizza, taco=taco, dessert=dessert)

    # products
    burger = Burger.query.order_by(Burger.created_at.desc()).all()
    pizza = Pizza.query.order_by(Pizza.created_at.desc()).all()
    taco = Taco.query.order_by(Taco.created_at.desc()).all()
    dessert = Dessert.query.order_by(Dessert.created_at.desc()).all()


    return render_template('categories.html', burger=burger, pizza=pizza, taco=taco, dessert=dessert)

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']
        rep_password = request.form['rep_password']
        phone_len = len(phone)

        # check if user exists
        if Users.query.filter((Users.email==email)).first():
            flash("Username or email already exists.", "error")
            return redirect(url_for("register"))

        # check for numbers in phone
        if any(char.isalpha() for char in phone):
            flash("Your phone number is invalid. contains alphabet", 'error')
            return redirect(url_for('register'))

        # check length of number
        if phone_len > 11 or phone_len < 11:
            flash('Phone number is invalid', 'error')
            return redirect(url_for('register'))

        # Required field check
        if not email:
            flash('Email are required!', 'error')
            return redirect(url_for('register'))

        #pass check
        if password != rep_password:
            flash('Password does not match', 'error')
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = Users(phone=phone, email=email, password=hashed_pw)

        db.session.add(new_user)
        db.session.commit()

        new_cart = Cart(user_id=new_user.id)
        db.session.add(new_cart)
        db.session.commit()

        flash("Account created! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# 🔹 User Login
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = Users.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            session['id'] = user.id
            session['email'] = user.email
            session['phone'] = user.phone
            if user.id == 1:
                user.s_admin = True
                db.session.commit()
            return redirect(url_for("index"))
        else:
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))

    return render_template("sign.html")

@app.route('/cart')
def cart():
    if 'email' not in session:
        flash("Please login to view your cart.", "error")
        return redirect(url_for('login'))

    user = Users.query.filter_by(email=session['email']).first()
    carts = user.cart
    items = carts.items if cart else []
    cart_c = len(items)
    return render_template('cart.html', cart_c=cart_c, items=items, email=user.email, carts=carts)

@app.route('/back')
def back():
    return render_template('back.html')


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'email' not in session:
        flash("Login required to add items!", "error")
        return redirect(url_for('login'))

    product_name = request.form['product_name']
    price = float(request.form['price'])
    quantity = int(request.form['quantity'])

    user = Users.query.filter_by(email=session['email']).first()
    carts = user.cart

    # Check if item already exists in cart
    existing_item = CartItem.query.filter_by(cart_id=carts.id, product_name=product_name).first()

    if existing_item:
        existing_item.quantity += quantity
    else:
        new_item = CartItem(cart_id=carts.id, product_name=product_name, price=price, quantity=quantity)
        db.session.add(new_item)

    db.session.commit()
    if request.url == categories:
        return redirect(url_for('back'))
    else:
        return redirect(url_for('back'))

# 🔹 remove items
@app.route('/remove_item/<int:item_id>', methods=['POST'])
def remove_item(item_id):
    if 'email' not in session:
        flash("Login required!", "warning")
        return redirect(url_for('login'))

    user = Users.query.filter_by(email=session['email']).first()
    carts = user.cart

    # Find the item in the user's cart
    item = CartItem.query.filter_by(id=item_id, cart_id=carts.id).first()

    if item:
        db.session.delete(item)
        db.session.commit()
        flash("Item removed from cart.", "success")
    else:
        flash("Item not found in your cart.", "error")

    return redirect(url_for('cart'))

@app.route("/pay", methods=["POST"])
def pay():
    if "email" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user = Users.query.filter_by(email=session['email']).first()
    carts = user.cart
    amount_kobo = int(carts.total_cost() * 100)  # Paystack accepts amount in Kobo (₦)

    # Create transaction payload
    headers = {
        "Authorization": f"Bearer {app.config['PAYSTACK_SECRET_KEY']}",
        "Content-Type": "application/json",
    }
    data = {
        "email": user.email,
        "amount": amount_kobo,
        "callback_url": url_for("payment_callback", _external=True)
    }

    response = requests.post("https://api.paystack.co/transaction/initialize", headers=headers, json=data)
    res_data = response.json()

    if res_data["status"]:
        return redirect(res_data["data"]["authorization_url"])  # Redirect to Paystack checkout
    else:
        flash("Payment initialization failed. Try again.", "error")
        return redirect(url_for("cart"))


@app.route("/payment/callback")
def payment_callback():
    # After payment, Paystack will redirect here with transaction reference
    ref = request.args.get("reference")

    headers = {
        "Authorization": f"Bearer {app.config['PAYSTACK_SECRET_KEY']}"
    }
    response = requests.get(f"https://api.paystack.co/transaction/verify/{ref}", headers=headers)
    res_data = response.json()

    if res_data["status"] and res_data["data"]["status"] == "success":
        flash("Payment successful! 🎉", "success")
        # (Optional) Clear cart after successful payment
       # user = Users.query.filter_by(email=session['email']).first()
       # user.cart.items.clear()

        user = Users.query.filter_by(email=session['email']).first()
        carts = user.cart
        email = user.email
        phone = user.phone
        product_entries = [f"{item.product_name} x{item.quantity}" for item in carts.items]
        product = ", ".join(product_entries)
        print(product)
        quantity = "quantity"

        new_sales = Customers(email=email, phone=phone, product=product, quantity=quantity)
        db.session.add(new_sales)
        db.session.commit()
    else:
        flash("Payment failed or cancelled.", "error")

    return redirect(url_for("cart"))

@app.route("/customers")
def view_customers():
    customers = Customers.query.order_by(Customers.created_at.desc()).all()
    return render_template("customers.html", customers=customers)


# 🔹 Protected Page
@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    # Check if logged-in user is admin
    if "email" not in session:
        flash("Please log in to continue.", "warning")
        return redirect(url_for("login"))

    user = Users.query.filter_by(email=session['email']).first()
    carts = user.cart
    items = carts.items
    cart_c = len(items)
    # Fetch all relevant data
    all_users = Users.query.all()
    all_customers = Customers.query.order_by(Customers.created_at.desc()).all()

    # products
    burger= Burger.query.order_by(Burger.created_at.desc()).all()
    pizza = Pizza.query.order_by(Pizza.created_at.desc()).all()
    taco = Taco.query.order_by(Taco.created_at.desc()).all()
    dessert = Dessert.query.order_by(Dessert.created_at.desc()).all()

    # Optionally, compute summary stats
    total_users = len(all_users)
    total_orders = len(all_customers)

    return render_template(
        "dashboard.html",
        cart_c=cart_c,
        user=user,
        users=all_users,
        customers=all_customers,
        total_users=total_users,
        total_orders=total_orders,
        burger=burger,
        pizza=pizza,
        taco=taco,
        dessert=dessert
    )

@app.route("/admin/edit_user/<int:user_id>", methods=["GET", "POST"])
def edit_user(user_id):
    if "email" not in session:
        flash("Please log in to continue.", "warning")
        return redirect(url_for("login"))

    user = Users.query.filter_by(email=session['email']).first()

    users = Users.query.get_or_404(user_id)

    if request.method == "POST":
        users.phone = request.form["phone"]
        users.email = request.form["email"]
        users.is_admin = "is_admin" in request.form  # checkbox

        try:
            db.session.commit()
            flash("User info updated successfully!", "success")
            return redirect(url_for("admin_dashboard"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating user: {e}", "danger")

    return render_template("edit_user.html", user=user, users=users)

@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    # Optional: Allow only admin users
    if "email" not in session:
        flash("Please log in to continue.", "warning")
        return redirect(url_for("login"))
    user = Users.query.filter_by(email=session['email']).first()
    if request.method == "POST":
        image_url = request.form["image_url"]
        name = request.form["name"]
        price = float(request.form["price"])
        category = request.form["category"]

        if category=="Burger":
            new_product = Burger(image=image_url, name=name, price=price)
            db.session.add(new_product)
            db.session.commit()

        if category=="Pizza":
            new_product = Pizza(image=image_url, name=name, price=price)
            db.session.add(new_product)
            db.session.commit()

        if category=="Taco":
            new_product = Taco(image=image_url, name=name, price=price)
            db.session.add(new_product)
            db.session.commit()

        if category=="Dessert":
            new_product = Dessert(image=image_url, name=name, price=price)
            db.session.add(new_product)
            db.session.commit()


        flash("Product added successfully!", "success")
        return redirect(url_for("add_product"))

    return render_template("add_product.html", user=user)


# 🔹 Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

if __name__ == '__main__':
    app.run(debug=True)
