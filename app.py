from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
import random

app = Flask(__name__)

# Database connection - using the credentials from your docker run command
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://my_user:my_password@my-postgres:5432/my_database')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

# Create tables
with app.app_context():
    db.create_all()

# Tour Package Data
tour_packages = [
    {"id": 1, "location": "Paris", "price": 1500, "days": 5, "food": True},
    {"id": 2, "location": "Maldives", "price": 2000, "days": 7, "food": False},
    {"id": 3, "location": "Tokyo", "price": 1800, "days": 6, "food": True},
    {"id": 4, "location": "New York", "price": 1200, "days": 4, "food": False},
]

# Store booked packages
booked_packages = []

# Redirect home to the login page
@app.route("/")
def home():
    return redirect(url_for("login"))

# Render the sign-up page
@app.route("/signin")
def signin():
    return render_template("signin.html")

# Render and process the login form
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        # Check credentials (in production, use hashed passwords)
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session["user_id"] = user.id  # Store user ID in session
            return redirect(url_for("dashboard"))
        return "Invalid credentials", 401
    return render_template("login.html")

# Process the sign-up form
@app.route("/signup", methods=["POST"])
def signup():
    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]
    # Check if user already exists
    if User.query.filter((User.username == username) | (User.email == email)).first():
        return "User already exists", 400
    new_user = User(username=username, email=email, password=password)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for("login"))

# Dashboard route (protected page)
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:  # Ensure the user is logged in
        return redirect(url_for("login"))
    
    # Fetch user details
    user = User.query.get(session["user_id"])
    
    return render_template(
        "dashboard.html",
        username=user.username,
        email=user.email,
        tour_packages=tour_packages,
        booked_packages=booked_packages,
    )

# Logout route
@app.route("/logout")
def logout():
    session.pop("user_id", None)  # Remove user session
    return redirect(url_for("login"))

@app.route("/book_ticket", methods=["POST"])
def book_ticket():
    if "user_id" not in session:  # Ensure the user is logged in
        return redirect(url_for("login"))
    
    # Get form data
    start_location = request.form["start_location"]
    final_location = request.form["final_location"]
    travel_date = request.form["travel_date"]
    
    # Generate a random price between 1000 and 2000
    ticket_price = random.randint(1000, 2000)
    
    # Fetch user details from the database
    user = User.query.get(session["user_id"])
    
    # Render the ticket details
    return render_template(
        "dashboard.html",
        username=user.username,
        email=user.email,
        start_location=start_location,
        final_location=final_location,
        travel_date=travel_date,
        ticket_price=ticket_price,
        ticket_generated=True  # Flag to show ticket details
    )

@app.route("/book_package", methods=["POST"])
def book_package():
    if "user_id" not in session:  # Ensure the user is logged in
        return redirect(url_for("login"))
    
    # Get the selected package ID from the form
    package_id = int(request.form["package_id"])
    
    # Find the selected package
    selected_package = next((pkg for pkg in tour_packages if pkg["id"] == package_id), None)
    
    if selected_package:
        # Fetch user details
        user = User.query.get(session["user_id"])
        
        # Add user details to the package
        booked_package = {
            "username": user.username,
            "email": user.email,
            "location": selected_package["location"],
            "price": selected_package["price"],
            "days": selected_package["days"],
            "food": "Yes" if selected_package["food"] else "No",
        }
        booked_packages.append(booked_package)
    
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
