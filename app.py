from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bitacora.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Riego(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    planta = db.Column(db.String(50))
    cantidad = db.Column(db.String(50))
    fecha = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50))
    precio = db.Column(db.Float)

class Carrito(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'))
    producto = db.relationship('Producto')

class HistorialCompra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'))
    producto = db.relationship('Producto')
    fecha = db.Column(db.String(50))

@app.route("/", methods=["GET", "POST"])
def index():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and check_password_hash(user.password, request.form["password"]):
            session["user_id"] = user.id
            return redirect(url_for("bitacora"))
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        hashed_pw = generate_password_hash(request.form["password"])
        db.session.add(User(username=request.form["username"], password=hashed_pw))
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/bitacora", methods=["GET", "POST"])
def bitacora():
    if "user_id" not in session: return redirect(url_for("login"))
    if request.method == "POST":
        db.session.add(Riego(planta=request.form["planta"], cantidad=request.form["cantidad"], fecha=request.form["fecha"], user_id=session["user_id"]))
        db.session.commit()
    registros = Riego.query.filter_by(user_id=session["user_id"]).all()
    return render_template("bitacora.html", registros=registros)

@app.route("/tienda", methods=["GET", "POST"])
def tienda():
    if "user_id" not in session: return redirect(url_for("login"))
    if request.method == "POST":
        db.session.add(Carrito(user_id=session["user_id"], producto_id=request.form["producto_id"]))
        db.session.commit()
    productos = Producto.query.all()
    return render_template("tienda.html", productos=productos)

@app.route("/carrito", methods=["GET", "POST"])
def carrito():
    if "user_id" not in session: return redirect(url_for("login"))
    items = Carrito.query.filter_by(user_id=session["user_id"]).all()
    if request.method == "POST":
        for item in items:
            db.session.add(HistorialCompra(user_id=item.user_id, producto_id=item.producto_id, fecha=datetime.now().strftime("%Y-%m-%d %H:%M")))
            db.session.delete(item)
        db.session.commit()
        return redirect(url_for("historial"))
    return render_template("carrito.html", carrito=items)

@app.route("/historial")
def historial():
    if "user_id" not in session: return redirect(url_for("login"))
    historial = HistorialCompra.query.filter_by(user_id=session["user_id"]).all()
    return render_template("historial_compras.html", historial=historial)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not Producto.query.first():
            db.session.add(Producto(nombre="Abono orgánico", precio=100.0))
            db.session.add(Producto(nombre="Maceta ecológica", precio=50.0))
            db.session.commit()
    app.run(debug=True)
