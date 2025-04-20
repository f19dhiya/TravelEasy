from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
import random
from datetime import datetime
from flask_login import LoginManager, login_required, current_user, UserMixin, login_user, logout_user

app = Flask(__name__)

# Database connection (uses DATABASE_URL environment variable if set)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://my_user:my_password@my-postgres:5432/my_database')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')  # Secret key for session management
db = SQLAlchemy(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Redirect to login page if user is not logged in

# User model - Add UserMixin
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    # Add backref for bookings
    bookings = db.relationship('Booking', backref='user', lazy=True)

# Booking model
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    days = db.Column(db.Integer, nullable=False)
    food = db.Column(db.String(10), nullable=False)
    booking_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # e.g., "Completed", "Pending"

# Create tables
with app.app_context():
    db.create_all()

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Tour Package Data
tour_packages = [
    {"id": 1, "location": "Paris", "price": 15000, "days": 5, "food": True, "image_url": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1473&q=80", "description": "Experience the romance and charm of the City of Lights."},
    {"id": 2, "location": "Maldives", "price": 20000, "days": 7, "food": False, "image_url": "https://images.unsplash.com/photo-1573843981267-be1999ff37cd?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1374&q=80", "description": "Relax in luxury overwater bungalows and pristine beaches."},
    {"id": 3, "location": "Tokyo", "price": 18000, "days": 6, "food": True, "image_url": "https://assets.vogue.com/photos/676453250b3225e1868dca9c/master/w_2560%2Cc_limit/1345059895", "description": "Explore the vibrant culture and futuristic cityscape of Japan's capital."},
    {"id": 4, "location": "New York", "price": 12000, "days": 4, "food": False, "image_url": "https://images.unsplash.com/photo-1485871981521-5b1fd3805eee?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1470&q=80", "description": "Discover the iconic landmarks and bustling energy of the Big Apple."},
    {"id": 5, "location": "Rome", "price": 16000, "days": 6, "food": True, "image_url": "https://images.unsplash.com/photo-1529260830199-42c24126f198?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1476&q=80", "description": "Step back in time and explore ancient ruins and timeless art."},
    {"id": 6, "location": "Bali", "price": 17500, "days": 8, "food": False, "image_url": "https://images.unsplash.com/photo-1573790387438-4da905039392?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1527&q=80", "description": "Find serenity amidst lush rice paddies and beautiful temples."},
    {"id": 7, "location": "Santorini", "price": 22000, "days": 7, "food": True, "image_url": "https://plus.unsplash.com/premium_photo-1661964149725-fbf14eabd38c?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D", "description": "Witness breathtaking sunsets over the caldera in this Greek paradise."}, # Changed URL
    {"id": 8, "location": "London", "price": 14000, "days": 5, "food": True, "image_url": "https://images.unsplash.com/photo-1505761671935-60b3a7427bad?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1470&q=80", "description": "Explore historic landmarks, royal palaces, and vibrant markets."},
    {"id": 9, "location": "Sydney", "price": 19000, "days": 9, "food": False, "image_url": "https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1470&q=80", "description": "See the iconic Opera House and enjoy stunning harbor views."},
    {"id": 10, "location": "Rio de Janeiro", "price": 17000, "days": 7, "food": True, "image_url": "https://images.unsplash.com/photo-1516306580123-e6e52b1b7b5f?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1470&q=80", "description": "Experience the energy of Carnival, Christ the Redeemer, and Copacabana."},
    {"id": 11, "location": "Cape Town", "price": 18500, "days": 8, "food": False, "image_url": "https://images.unsplash.com/photo-1580060839134-75a5edca2e99?q=80&w=2071&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D", "description": "Discover stunning Table Mountain, penguins, and vibrant culture."}, # Changed URL
    {"id": 12, "location": "Bangkok", "price": 13000, "days": 6, "food": True, "image_url": "https://plus.unsplash.com/premium_photo-1661963646506-e822afdd50cb?q=80&w=2071&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D", "description": "Immerse yourself in ornate temples, bustling markets, and delicious street food."}
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
            login_user(user)  # Use flask_login's login_user
            return redirect(url_for("dashboard"))
        flash('Invalid credentials', 'danger')
        return redirect(url_for("login"))
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
@login_required
def dashboard():
    # Fetch user's booking history
    booking_history = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_date.desc()).all()
    
    return render_template(
        "dashboard.html",
        username=current_user.username,
        email=current_user.email,
        tour_packages=tour_packages,
        booked_packages=booked_packages,
        booking_history=booking_history
    )

# Logout route
@app.route("/logout")
def logout():
    logout_user()  # Use flask_login's logout_user
    return redirect(url_for("login"))

@app.route("/book_ticket", methods=["POST"])
@login_required
def book_ticket():
    # Get form data
    start_location = request.form["start_location"]
    final_location = request.form["final_location"]
    travel_date = request.form["travel_date"]
    
    # Generate a random price between 1000 and 2000
    ticket_price = random.randint(1000, 2000)
    
    return render_template(
        "dashboard.html",
        username=current_user.username,
        email=current_user.email,
        start_location=start_location,
        final_location=final_location,
        travel_date=travel_date,
        ticket_price=ticket_price,
        ticket_generated=True  # Flag to show ticket details
    )

@app.route("/book_package", methods=["POST"])
@login_required
def book_package():
    # Get the selected package ID from the form
    package_id = int(request.form["package_id"])
    
    # Find the selected package
    selected_package = next((pkg for pkg in tour_packages if pkg["id"] == package_id), None)
    
    if selected_package:
        # Add user details to the package
        booked_package = {
            "username": current_user.username,
            "email": current_user.email,
            "location": selected_package["location"],
            "price": selected_package["price"],
            "days": selected_package["days"],
            "food": "Yes" if selected_package["food"] else "No",
            "image_url": selected_package["image_url"]    # <-- Added this line
        }
        booked_packages.append(booked_package)
    
    return redirect(url_for("dashboard"))

@app.route("/cart")
@login_required
def cart():
    # Calculate the total cost of booked packages
    total_cost = sum(package["price"] for package in booked_packages)
    
    return render_template(
        "cart.html",
        booked_packages=booked_packages,
        total_cost=total_cost
    )

@app.route("/remove_from_cart", methods=["POST"])
@login_required
def remove_from_cart():
    # Get the index of the package to remove
    package_index = int(request.form["package_index"])
    
    # Remove the package from the booked_packages list
    if 0 <= package_index < len(booked_packages):
        booked_packages.pop(package_index)
    
    return redirect(url_for("cart"))

@app.route("/payment", methods=["GET", "POST"])
@login_required
def payment():
    if request.method == "POST":
        payment_method = request.form["payment_method"]
        session["payment_method"] = payment_method  # Store payment method in session
        return redirect(url_for("bill"))  # Redirect to the bill page
    
    return render_template("payment.html")

@app.route("/bill")
@login_required
def bill():
    # Fetch payment method from session
    payment_method = session.get("payment_method", "Unknown")
    
    # Get current date and time
    transaction_date = datetime.now()
    
    # Save booked packages to the database
    for package in booked_packages:
        new_booking = Booking(
            user_id=current_user.id,
            location=package["location"],
            price=package["price"],
            days=package["days"],
            food=package["food"],
            booking_date=transaction_date,
            status="Completed"
        )
        db.session.add(new_booking)
    db.session.commit()
    
    # Calculate total cost
    total_cost = sum(package["price"] for package in booked_packages)
    
    # Render the bill
    rendered_bill = render_template(
        "bill.html",
        username=current_user.username,
        email=current_user.email,
        booked_packages=booked_packages,
        total_cost=total_cost,
        payment_method=payment_method,
        transaction_date=transaction_date.strftime("%Y-%m-%d %H:%M:%S")
    )
    
    # Clear booked packages after saving to the database
    booked_packages.clear()
    
    return rendered_bill

@app.route('/bill/<int:booking_id>')
@login_required
def view_bill(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        flash('You are not authorized to view this bill.', 'danger')
        return redirect(url_for('dashboard'))
    return render_template('bill.html', booking=booking)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
