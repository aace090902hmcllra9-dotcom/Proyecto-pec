from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "reutilizacion_del_agua"

# ---------- DOMINIOS PERMITIDOS ----------
DOMINIOS_PERMITIDOS = [
    "@gmail.com",
    "@outlook.com",
    "@hotmail.com",
    "@yahoo.com",
    "@icloud.com"
]

def correo_valido(correo):
    return any(correo.endswith(d) for d in DOMINIOS_PERMITIDOS)

# ---------- BASE DE DATOS ----------
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            correo TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# ---------- LOGIN ----------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form.get("correo")
        password = request.form.get("password")

        if not correo or not password:
            return "❌ Debes llenar todos los campos"

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT nombre FROM users WHERE correo=? AND password=?",
            (correo, password)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user"] = user[0]
            return redirect("/inicio")
        else:
            return "❌ Correo o contraseña incorrectos"

    return render_template("login.html")

# ---------- REGISTRO ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nombre = request.form["nombre"]
        correo = request.form["correo"]
        password = request.form["password"]

        if not nombre or not correo or not password:
            return "❌ Todos los campos son obligatorios"

        if not correo_valido(correo):
            return "❌ Correo no permitido"

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (nombre, correo, password) VALUES (?, ?, ?)",
                (nombre, correo, password)
            )
            conn.commit()
        except:
            conn.close()
            return "❌ Este correo ya está registrado"

        conn.close()
        return redirect("/")

    return render_template("register.html")

# ---------- INICIO ----------
@app.route("/inicio")
def inicio():
    if "user" not in session:
        return redirect("/")
    return render_template("index.html", nombre=session["user"])

# ---------- JUEGO ----------
@app.route("/juego")
def juego():
    if "user" not in session:
        return redirect("/")
    return render_template("juego.html")

# ---------- TABLA ----------
@app.route("/tabla")
def tabla():
    if "user" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, correo FROM users")
    usuarios = cursor.fetchall()
    conn.close()

    return render_template("tabla.html", usuarios=usuarios)

# ---------- BUSCAR ----------
@app.route("/buscar", methods=["GET"])
def buscar():
    if "user" not in session:
        return redirect("/")

    q = request.args.get("q", "")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nombre, correo FROM users WHERE nombre LIKE ? OR correo LIKE ?",
        (f"%{q}%", f"%{q}%")
    )
    usuarios = cursor.fetchall()
    conn.close()

    return render_template("tabla.html", usuarios=usuarios, q=q)

# ---------- INSERTAR ----------
@app.route("/insertar", methods=["GET", "POST"])
def insertar():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        nombre = request.form["nombre"]
        correo = request.form["correo"]
        password = request.form["password"]

        if not correo_valido(correo):
            return "❌ Correo no permitido"

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (nombre, correo, password) VALUES (?, ?, ?)",
                (nombre, correo, password)
            )
            conn.commit()
        except:
            conn.close()
            return "❌ El correo ya existe"

        conn.close()
        return redirect("/tabla")

    return render_template("insertar.html")

# ---------- EDITAR (ÚNICO CAMBIO AQUÍ) ----------
@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    if "user" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT nombre, correo, password FROM users WHERE id=?",
        (id,)
    )
    usuario = cursor.fetchone()

    if not usuario:
        conn.close()
        return "❌ Usuario no encontrado"

    if request.method == "POST":
        nombre = request.form["nombre"]
        correo = request.form["correo"]
        password_ingresada = request.form["password"]

        # 🔐 VALIDACIÓN REAL DE CONTRASEÑA
        if password_ingresada != usuario[2]:
            conn.close()
            return "❌ Contraseña incorrecta"

        if not correo_valido(correo):
            conn.close()
            return "❌ Correo no permitido"

        cursor.execute(
            "UPDATE users SET nombre=?, correo=? WHERE id=?",
            (nombre, correo, id)
        )
        conn.commit()
        conn.close()
        return redirect("/tabla")

    conn.close()
    return render_template("editar.html", usuario=usuario, id=id)

# ---------- ELIMINAR ----------
@app.route("/eliminar/<int:id>")
def eliminar(id):
    if "user" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/tabla")

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------- EJECUCIÓN ----------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
