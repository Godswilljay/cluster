from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class Customers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=False, nullable=False)
    phone = db.Column(db.String(100), unique=False, nullable=False)
    product = db.Column(db.Text, unique=False, nullable=False)
    quantity = db.Column(db.String(100), unique=False, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f"<User {self.name}>"

class Burger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.Text, unique=False, nullable=False)
    name = db.Column(db.Text, unique=False, nullable=False)
    price = db.Column(db.Float, unique=False, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f"<User {self.name}>"

class Pizza(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.Text, unique=False, nullable=False)
    name = db.Column(db.Text, unique=False, nullable=False)
    price = db.Column(db.Float, unique=False, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f"<User {self.name}>"

class Taco(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.Text, unique=False, nullable=False)
    name = db.Column(db.Text, unique=False, nullable=False)
    price = db.Column(db.Float, unique=False, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f"<User {self.name}>"

class Dessert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.Text, unique=False, nullable=False)
    name = db.Column(db.Text, unique=False, nullable=False)
    price = db.Column(db.Float, unique=False, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f"<User {self.name}>"

# login
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(100), unique=False, nullable=False)
    email = db.Column(db.Text, unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    s_admin = db.Column(db.Boolean, default=False)
    password = db.Column(db.Text, nullable=False)

    cart = db.relationship("Cart", backref="user", uselist=False)


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

  # one-to-many relationship (a cart can have many items)
    items = db.relationship("CartItem", backref="cart", lazy=True)

    def total_cost(self):
        return sum(item.price * item.quantity for item in self.items)


# ---------------- CART ITEM ----------------
class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("cart.id"), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, default=1)
    added_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f"<Item {self.product_name} (x{self.quantity})>"