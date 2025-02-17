from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, send_file
from fpdf import FPDF
import os

app = Flask(__name__)
app.secret_key = "clave_secreta_para_sesion"

# Simulación de usuarios registrados (almacenados en memoria)
users = {}  # Formato: { username: { "password": ..., "email": ... } }

# Diccionario para almacenar citas agendadas por usuario
citas_agendadas = {}

# Configuración de carpetas para uploads y resultados
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
RESULTS_FOLDER = os.path.join(os.getcwd(), 'results')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(RESULTS_FOLDER):
    os.makedirs(RESULTS_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ruta de la página principal (opción: un home que redirige a login)
@app.route("/")
def home():
    return render_template("home.html")

# Registro de usuario
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        if username in users:
            flash("El usuario ya existe.", "danger")
        else:
            users[username] = {"password": password, "email": email}
            flash("Registro exitoso. Por favor, inicia sesión.", "success")
            return redirect(url_for("login"))
    return render_template("register.html")

# Inicio de sesión
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in users and users[username]["password"] == password:
            session["username"] = username
            # Inicializa las citas para el usuario si no existen
            if username not in citas_agendadas:
                citas_agendadas[username] = []
            flash("Inicio de sesión exitoso.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Usuario o contraseña incorrectos.", "danger")
            return redirect(url_for("login"))
    return render_template("login.html")

# Dashboard con mensaje flotante y enlaces a módulos
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        flash("Debe iniciar sesión.", "warning")
        return redirect(url_for("login"))
    return render_template("dashboard.html", username=session["username"])

# Módulo de agendamiento de citas (multicitas)
@app.route("/citas", methods=["GET", "POST"])
def citas():
    if "username" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        # Se reciben listas de datos, ya que el formulario permite múltiples citas
        especialidades = request.form.getlist("especialidad")
        medicos = request.form.getlist("medico")
        fechas = request.form.getlist("fecha")
        horas = request.form.getlist("hora")
        username = session["username"]
        for esp, med, fecha, hora in zip(especialidades, medicos, fechas, horas):
            cita = {"especialidad": esp, "medico": med, "fecha": fecha, "hora": hora}
            citas_agendadas[username].append(cita)
        flash("Citas agendadas exitosamente.", "success")
        return redirect(url_for("dashboard"))
    return render_template("citas.html")

# Módulo de contacto (para quejas o felicitaciones)
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        email = request.form.get("email")
        mensaje = request.form.get("mensaje")
        # Aquí podrías enviar el mensaje por correo o almacenarlo en una base de datos
        flash("Gracias por tu mensaje. Nos comunicaremos contigo pronto.", "success")
        return redirect(url_for("dashboard"))
    return render_template("contact.html")

# Módulo de autorización (cargar documentos)
@app.route("/authorization", methods=["GET", "POST"])
def authorization():
    if request.method == "POST":
        if "document" not in request.files:
            flash("No se ha seleccionado ningún archivo.", "danger")
            return redirect(request.url)
        file = request.files["document"]
        if file.filename == "":
            flash("No se ha seleccionado ningún archivo.", "danger")
            return redirect(request.url)
        if file:
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash("Documento cargado exitosamente.", "success")
            return redirect(url_for("dashboard"))
    return render_template("authorization.html")

# Módulo de resultados médicos (descargar resultados)
@app.route("/results")
def results():
    # Lista los archivos en RESULTS_FOLDER
    files = os.listdir(RESULTS_FOLDER)
    return render_template("results.html", files=files)

@app.route("/results/download/<filename>")
def download_result(filename):
    return send_from_directory(RESULTS_FOLDER, filename, as_attachment=True)

# Generar PDF de citas agendadas y descargar
@app.route("/descargar_pdf")
def descargar_pdf():
    if "username" not in session:
        return redirect(url_for("login"))
    username = session["username"]
    citas = citas_agendadas.get(username, [])
    if not citas:
        flash("No hay citas agendadas para generar PDF.", "warning")
        return redirect(url_for("dashboard"))
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Citas Agendadas para {username}", ln=True, align="C")
    pdf.ln(10)
    for cita in citas:
        line = f"{cita['especialidad']} con {cita['medico']} el {cita['fecha']} a las {cita['hora']}"
        pdf.multi_cell(0, 10, txt=line)
    pdf_filename = f"citas_{username}.pdf"
    pdf.output(pdf_filename)
    return send_file(pdf_filename, as_attachment=True)

# Cerrar sesión
@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("Sesión cerrada.", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
