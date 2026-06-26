from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import random
import os

app = Flask(__name__)
app.secret_key = "quizy123"

DATABASE = "database.db"


# ======================================
# KONEKSI DATABASE
# ======================================
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ======================================
# MEMBUAT DATABASE
# ======================================
def init_db():

    conn = get_db_connection()
    cursor = conn.cursor()

    # ===============================
    # Tabel Soal
    # ===============================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        question TEXT NOT NULL,

        option_a TEXT NOT NULL,

        option_b TEXT NOT NULL,

        option_c TEXT NOT NULL,

        option_d TEXT NOT NULL,

        answer TEXT NOT NULL

    )
    """)

    # ===============================
    # Tabel Hasil
    # ===============================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS results(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        student TEXT,

        score INTEGER

    )
    """)

    conn.commit()

    # ==========================================
    # INPUT SOAL JIKA DATABASE MASIH KOSONG
    # ==========================================

    jumlah = cursor.execute(
        "SELECT COUNT(*) FROM questions"
    ).fetchone()[0]

    if jumlah == 0:

        data = [

            (
                "Rumus volume kubus adalah ....",
                "s²",
                "s³",
                "6s²",
                "p × l × t",
                "B"
            ),

            (
                "Kubus memiliki berapa sisi?",
                "4",
                "6",
                "8",
                "12",
                "B"
            ),

            (
                "Kubus memiliki berapa rusuk?",
                "8",
                "10",
                "12",
                "14",
                "C"
            ),

            (
                "Rumus luas permukaan kubus adalah ....",
                "6s²",
                "s³",
                "4s²",
                "2pl + 2pt + 2lt",
                "A"
            ),

            (
                "Volume balok dihitung dengan ....",
                "p × l × t",
                "6s²",
                "s³",
                "2(p+l)",
                "A"
            ),

            (
                "Balok memiliki .... titik sudut.",
                "6",
                "8",
                "10",
                "12",
                "B"
            ),

            (
                "Balok memiliki .... sisi.",
                "6",
                "8",
                "10",
                "12",
                "A"
            ),

            (
                "Rumus luas permukaan balok adalah ....",
                "2(pl + pt + lt)",
                "p × l × t",
                "6s²",
                "4s²",
                "A"
            ),

            (
                "Kubus adalah bangun ruang yang semua rusuknya ....",
                "berbeda",
                "sama panjang",
                "miring",
                "tidak sama",
                "B"
            ),

            (
                "Balok memiliki pasangan sisi yang ....",
                "berbeda semua",
                "sejajar dan sama luas",
                "melingkar",
                "segitiga",
                "B"
            )

        ]

        cursor.executemany("""

        INSERT INTO questions(
            question,
            option_a,
            option_b,
            option_c,
            option_d,
            answer
        )

        VALUES(?,?,?,?,?,?)

        """, data)

        conn.commit()

    conn.close()


# ======================================
# MEMANGGIL DATABASE
# ======================================
init_db()
# ======================================
# HALAMAN HOME
# ======================================
@app.route("/")
def index():
    return render_template("index.html")


# ======================================
# LOGIN SISWA
# ======================================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        nama = request.form.get("nama")

        if nama == "":
            flash("Nama tidak boleh kosong!")
            return redirect(url_for("login"))

        session["student"] = nama

        return redirect(url_for("dashboard"))

    return render_template("login.html")


# ======================================
# DASHBOARD
# ======================================
@app.route("/dashboard")
def dashboard():

    if "student" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    total_soal = conn.execute(
        "SELECT COUNT(*) FROM questions"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        student=session["student"],
        total=total_soal
    )


# ======================================
# MULAI KUIS
# ======================================
@app.route("/start")
def start_quiz():

    if "student" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    questions = conn.execute("""
        SELECT *
        FROM questions
    """).fetchall()

    conn.close()

    questions = list(questions)

    random.shuffle(questions)

    session["questions"] = [dict(q) for q in questions]

    session["current"] = 0

    session["score"] = 0

    return redirect(url_for("quiz"))


# ======================================
# LOGOUT
# ======================================
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("index"))
# ======================================
# HALAMAN QUIZ
# ======================================
@app.route("/quiz", methods=["GET", "POST"])
def quiz():

    # Cek apakah siswa sudah login
    if "student" not in session:
        return redirect(url_for("login"))

    # Ambil daftar soal dari session
    questions = session.get("questions", [])

    # Jika tidak ada soal
    if len(questions) == 0:
        return redirect(url_for("dashboard"))

    # Nomor soal saat ini
    current = session.get("current", 0)

    # ======================================
    # PROSES JAWABAN
    # ======================================
    if request.method == "POST":

        jawaban = request.form.get("answer")

        soal = questions[current]

        if jawaban == soal["answer"]:
            session["score"] += 10

        current += 1
        session["current"] = current

        # Jika semua soal sudah selesai
        if current >= len(questions):
            return redirect(url_for("result"))

        return redirect(url_for("quiz"))

    # ======================================
    # TAMPILKAN SOAL
    # ======================================
    soal = questions[current]

    progress = int((current / len(questions)) * 100)

    return render_template(
        "quiz.html",
        soal=soal,
        nomor=current + 1,
        total=len(questions),
        progress=progress
    )
# ======================================
# HALAMAN HASIL
# ======================================
@app.route("/result")
def result():

    if "student" not in session:
        return redirect(url_for("login"))

    student = session["student"]
    score = session["score"]

    conn = get_db_connection()

    # Simpan hanya sekali
    saved = session.get("saved_result", False)

    if not saved:
        conn.execute(
            """
            INSERT INTO results(student, score)
            VALUES (?, ?)
            """,
            (student, score)
        )

        conn.commit()
        session["saved_result"] = True

    conn.close()

    return render_template(
        "result.html",
        student=student,
        score=score
    )


# ======================================
# HALAMAN ADMIN
# ======================================
@app.route("/admin")
def admin():

    conn = get_db_connection()

    questions = conn.execute("""
        SELECT *
        FROM questions
        ORDER BY id
    """).fetchall()

    results = conn.execute("""
        SELECT *
        FROM results
        ORDER BY score DESC
    """).fetchall()

    total_soal = conn.execute(
        "SELECT COUNT(*) FROM questions"
    ).fetchone()[0]

    total_siswa = conn.execute(
        "SELECT COUNT(DISTINCT student) FROM results"
    ).fetchone()[0]

    nilai_tertinggi = conn.execute(
        "SELECT MAX(score) FROM results"
    ).fetchone()[0]

    rata_rata = conn.execute(
        "SELECT AVG(score) FROM results"
    ).fetchone()[0]

    conn.close()

    if nilai_tertinggi is None:
        nilai_tertinggi = 0

    if rata_rata is None:
        rata_rata = 0

    return render_template(
        "admin.html",
        questions=questions,
        results=results,
        total_soal=total_soal,
        total_siswa=total_siswa,
        nilai_tertinggi=nilai_tertinggi,
        rata_rata=round(rata_rata, 2)
    )
# ======================================
# TAMBAH SOAL
# ======================================
@app.route("/add_question", methods=["GET", "POST"])
def add_question():

    if request.method == "POST":

        question = request.form["question"]
        option_a = request.form["option_a"]
        option_b = request.form["option_b"]
        option_c = request.form["option_c"]
        option_d = request.form["option_d"]
        answer = request.form["answer"]

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO questions
            (question, option_a, option_b, option_c, option_d, answer)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
        (question, option_a, option_b, option_c, option_d, answer))

        conn.commit()
        conn.close()

        return redirect(url_for("admin"))

    return render_template("add_question.html")


# ======================================
# RESET QUIZ
# ======================================
@app.route("/reset")
def reset():

    session.pop("questions", None)
    session.pop("current", None)
    session.pop("score", None)
    session.pop("saved_result", None)

    return redirect(url_for("dashboard"))


# ======================================
# JALANKAN APLIKASI
# ======================================
if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=True)