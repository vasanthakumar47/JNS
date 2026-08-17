import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from functools import wraps

# Setup Flask with explicit static path
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = "jnstech_secure_super_secret_key_2026"

# Vercel serverless environment check & writable DB path fix
if os.environ.get("VERCEL"):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/jnstech_local.db'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jnstech_local.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

ADMIN_PASSWORD = "vasanth@123"

# Explicit Static File Handler for Vercel
@app.route('/static/<path:filename>')
def serve_static(filename):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(os.path.join(root_dir, 'static'), filename)

# Product Model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    price = db.Column(db.String(50), nullable=False)
    badge = db.Column(db.String(50), default='OEM Grade')
    image_url = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=False)

# Safe Database Initializer
def init_db():
    with app.app_context():
        db.create_all()
        if Product.query.count() == 0:
            jns_catalog = [
                Product(
                    name="Maintenance Kit for All Cutters",
                    category="Cutter Spares",
                    price="₹18,500",
                    badge="High Precision",
                    image_url="/static/Images/Maintenance kit for All Cutters.jpg",
                    description="Complete industrial overhaul and periodic service kit tailored for CNC multi-ply apparel cutting machines."
                ),
                Product(
                    name="Modular Cutting Table Bristle Blocks",
                    category="Bristle Surface",
                    price="₹1,450 / pc",
                    badge="High Durability",
                    image_url="/static/Images/Bristle block.jpg",
                    description="High-density virgin polymer bristle blocks designed for low vacuum loss and extended knife blade life."
                ),
                Product(
                    name="Blade Grinding Stones & Sharpening Belts",
                    category="Sharpening Systems",
                    price="₹2,800",
                    badge="In Stock",
                    image_url="/static/Images/Grinding stone and belt.jpg",
                    description="Precision-grit diamond sharpening wheels and abrasive belts for consistent, burr-free cutter blade edges."
                ),
                Product(
                    name="High-Speed Garment Cutting Blades",
                    category="Industrial Knives",
                    price="₹4,200",
                    badge="Tungsten Carbide",
                    image_url="/static/Images/Blades.jpg",
                    description="Hardened HSS & tungsten carbide reciprocating blades engineered for thick denim, knitwear, and woven plies."
                ),
                Product(
                    name="Spreader Electronic Control PCB & Sensor Unit",
                    category="Spreader Electronics",
                    price="₹16,000",
                    badge="OEM Certified",
                    image_url="/static/Images/All Spreader parts and PCB.jpg",
                    description="Mainboard servo drive controllers, optical edge sensors, and wiring harness sets for automatic spreading machines."
                ),
                Product(
                    name="Heavy-Duty Garment Factory Workstations & Tables",
                    category="Factory Infrastructure",
                    price="₹32,000",
                    badge="Custom Built",
                    image_url="/static/Images/Factory Furniture.jpg",
                    description="Modular combined cutting tables with air flotation blowers, pinning tables, and ergonomic operator chairs."
                )
            ]
            db.session.bulk_save_objects(jns_catalog)
            db.session.commit()

# Admin Auth Guard
def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function

# ==================== PUBLIC ROUTES ====================

@app.route("/")
def home():
    init_db()
    products = Product.query.order_by(Product.id.asc()).all()
    return render_template("index.html", products=products)

@app.route("/products")
def products():
    init_db()
    all_products = Product.query.order_by(Product.id.asc()).all()
    return render_template("products.html", products=all_products)

@app.route("/enquiry", methods=["POST"])
def send_enquiry():
    name = request.form.get("name")
    phone = request.form.get("phone")
    flash(f"Thank you {name}! Your enquiry has been received. JNS Tech will contact you at {phone}.", "success")
    return redirect(url_for("home") + "#enquiry")

# ==================== SECURED ADMIN ROUTES ====================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Incorrect Password! Please try again.", "danger")
    return render_template("admin/login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))

@app.route("/admin")
@admin_login_required
def admin_dashboard():
    init_db()
    all_products = Product.query.order_by(Product.id.desc()).all()
    return render_template("admin/dashboard.html", products=all_products)

@app.route("/admin/add", methods=["GET", "POST"])
@admin_login_required
def admin_add_product():
    if request.method == "POST":
        new_item = Product(
            name=request.form.get("name"),
            category=request.form.get("category"),
            price=request.form.get("price"),
            badge=request.form.get("badge"),
            image_url=request.form.get("image_url") or "/static/Images/overall.jpg",
            description=request.form.get("description")
        )
        db.session.add(new_item)
        db.session.commit()
        return redirect(url_for("admin_dashboard"))
    return render_template("admin/add_product.html")

@app.route("/admin/edit/<int:id>", methods=["GET", "POST"])
@admin_login_required
def admin_edit_product(id):
    product = Product.query.get_or_404(id)
    if request.method == "POST":
        product.name = request.form.get("name")
        product.category = request.form.get("category")
        product.price = request.form.get("price")
        product.badge = request.form.get("badge")
        if request.form.get("image_url"):
            product.image_url = request.form.get("image_url")
        product.description = request.form.get("description")
        db.session.commit()
        return redirect(url_for("admin_dashboard"))
    return render_template("admin/edit_product.html", product=product)

@app.route("/admin/delete/<int:id>")
@admin_login_required
def admin_delete_product(id):
    item = Product.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("admin_dashboard"))

# Vercel entry handler#
app = app

if __name__ == "__main__":
    init_db()
    app.run(debug=True)