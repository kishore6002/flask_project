from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3, random, datetime, os
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from database import init_db


app = Flask(__name__)
app.secret_key = "secret123"
init_db()
# ---------------- DATABASE ----------------
def get_db():
    return sqlite3.connect("database.db")


# ---------------- ROOM STRUCTURE ----------------
blocks = {
    "WB": [f"WB{n}" for n in range(301, 311)],
    "EB": [f"EB{n}" for n in range(301, 311)],
    "SB": [f"SB{n}" for n in range(301, 311)],
    "NB": [f"NB{n}" for n in range(301, 311)],
    "CB": [f"CB{n}" for n in range(301, 311)],
    "LAB": [f"LAB{n:02}" for n in range(1, 13)]
}

sections = ["A", "B", "C", "D", "E"]

def generate_rooms():
    rooms = []
    for r in blocks.values():
        rooms.extend(r)
    random.shuffle(rooms)
    return rooms

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor()
        cur.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (request.form["username"], request.form["password"])
        )
        user = cur.fetchone()
        db.close()

        if user:
            session["user"] = user[0]
            session["dept"] = user[2]
            session["role"] = user[3]
            return redirect("/dashboard")

    return render_template("login.html")

# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        db = get_db()
        db.execute(
            "INSERT INTO users VALUES (?,?,?,?)",
            (
                request.form["username"],
                request.form["password"],
                request.form["dept"],
                request.form["role"]
            )
        )
        db.commit()
        db.close()
        return redirect("/")

    return render_template("signup.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    if session["role"] == "admin":
        return redirect("/admin")
    return redirect("/student")

# ---------------- ADMIN ----------------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if session.get("role") != "admin":
        return redirect("/")

    day = str(datetime.date.today())
    depts = ["CSE", "ECE", "MECH", "CIVIL", "EEE"]
    years = ["1st", "2nd", "3rd", "4th"]

    db = get_db()
    cur = db.cursor()

    if request.method == "POST":
        rooms = generate_rooms()
        cur.execute("DELETE FROM allotments WHERE day=?", (day,))
        i = 0

        for d in depts:
            for y in years:
                for s in sections:
                    cur.execute(
                        "INSERT INTO allotments VALUES (?,?,?,?,?)",
                        (d, y, s, rooms[i % len(rooms)], day)
                    )
                    i += 1

        db.commit()

    cur.execute(
        "SELECT dept, year, section, room, day FROM allotments WHERE day=?",
        (day,)
    )
    data = cur.fetchall()
    db.close()

    return render_template("admin.html", data=data, day=day)


# ---------------- ADMIN MANUAL UPDATE ----------------
@app.route("/update", methods=["POST"])
def update():
    if session.get("role") != "admin":
        return redirect("/")

    db = get_db()
    db.execute(
        "UPDATE allotments SET room=? WHERE dept=? AND year=? AND section=? AND day=?",
        (
            request.form["room"],
            request.form["dept"],
            request.form["year"],
            request.form["section"],
            request.form["day"]
        )
    )
    db.commit()
    db.close()

    return redirect("/admin")

# ---------------- STUDENT ----------------
@app.route("/student")
def student():
    if session.get("role") != "student":
        return redirect("/")

    db = get_db()
    cur = db.cursor()
    cur.execute(
        "SELECT year, section, room, day FROM allotments WHERE dept=?",
        (session["dept"],)
    )
    data = cur.fetchall()
    db.close()

    return render_template("student.html", data=data)

# ---------------- PDF DOWNLOAD ----------------
@app.route("/download_pdf")
def download_pdf():
    if session.get("role") != "admin":
        return redirect("/")

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT dept, year, section, room, day FROM allotments")
    rows = cur.fetchall()
    db.close()

    if not rows:
        return "No allotment data available. Please shuffle first."

    filename = f"class_allotment_{datetime.date.today()}.pdf"
    file_path = os.path.join(os.getcwd(), filename)

    pdf = SimpleDocTemplate(file_path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Class Allotment List", styles["Title"]))
    elements.append(Paragraph("<br/>", styles["Normal"]))

    table_data = [["Department", "Year", "Section", "Room No", "Day"]]
    for r in rows:
        table_data.append([r[0], r[1], r[2], r[3], r[4]])

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.darkblue),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BACKGROUND", (0,1), (-1,-1), colors.whitesmoke),
        ("BOTTOMPADDING", (0,0), (-1,0), 10),
    ]))

    elements.append(table)
    pdf.build(elements)

    return send_file(file_path, as_attachment=True)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)

