from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# -------- Email (NEWLY ADDED) --------
import smtplib
from email.mime.text import MIMEText
# -------------------------------------

app = Flask(__name__)
app.secret_key = 'supersecret_quizpay_key'  # change for production

# --- Email Credentials (NEW) ---
EMAIL_ADDRESS = "sakshiitnare92@gmail.com"
EMAIL_PASSWORD = "apkk xysr bsvr htdm"

# --- Email Function (NEW) ---
def send_quiz_email(to_email, username, subject, score, reward):
    try:
        body = f"""
Hello {username},

Your quiz attempt is completed!

Subject: {subject}
Score: {score}/5
Reward Added: ₹{reward}

Amount has been successfully added to your wallet.

Thank you for using QuizPay!
"""
        msg = MIMEText(body)
        msg["Subject"] = "QuizPay – Wallet Updated & Quiz Result"
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        server.quit()

        print("Email sent successfully!")

    except Exception as e:
        print("Email sending failed:", e)

# --- Data folder for SQL dumps ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

USERS_SQL_FILE = os.path.join(DATA_DIR, "users.sql")
QUESTIONS_SQL_FILE = os.path.join(DATA_DIR, "questions.sql")
ATTEMPTS_SQL_FILE = os.path.join(DATA_DIR, "attempts.sql")

# --- Database connection ---
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
)
cursor = conn.cursor()
cursor.execute("CREATE DATABASE IF NOT EXISTS quizpay CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
cursor.execute("USE quizpay")

# --- Users Table Updated ---
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(150),
    email VARCHAR(150) UNIQUE,
    password VARCHAR(255),
    mobile_number VARCHAR(20),
    age INT,
    address VARCHAR(255),
    wallet_balance DECIMAL(10,2) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject VARCHAR(50),
    question TEXT,
    option1 VARCHAR(255),
    option2 VARCHAR(255),
    option3 VARCHAR(255),
    option4 VARCHAR(255),
    correct_option TINYINT(1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS quiz_attempts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    subject VARCHAR(50),
    score INT,
    reward DECIMAL(10,2),
    timestamp DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
""")
conn.commit()

# ---------------- SQL DUMP FUNCTIONS ----------------
def _sql_escape(val):
    if val is None:
        return "NULL"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, datetime):
        return "'" + val.strftime('%Y-%m-%d %H:%M:%S') + "'"
    s = str(val).replace("'", "''")
    return f"'{s}'"

def export_table_to_sql(table_name, filepath):
    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        cols = [d[0] for d in cursor.description]
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"-- Dump of table `{table_name}`\n")
            if not rows:
                return
            col_list = ",".join([f"`{c}`" for c in cols])
            for row in rows:
                vals = [_sql_escape(v) for v in row]
                stmt = f"INSERT INTO `{table_name}` ({col_list}) VALUES ({','.join(vals)});\n"
                f.write(stmt)
    except Exception as e:
        print(f"[EXPORT ERROR] {e}")

def import_sql_file_if_table_empty(table_name, filepath):
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        if cursor.fetchone()[0] > 0:
            return
    except:
        return
    if not os.path.isfile(filepath):
        return
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            sql_text = f.read()
        statements = [s.strip() for s in sql_text.split(";") if s.strip()]
        for stmt in statements:
            try:
                cursor.execute(stmt)
            except Exception as e:
                print(f"[IMPORT ERROR] {e}")
        conn.commit()
    except Exception as e:
        print(f"[IMPORT ERROR] {e}")

def export_all_tables():
    export_table_to_sql("users", USERS_SQL_FILE)
    export_table_to_sql("questions", QUESTIONS_SQL_FILE)
    export_table_to_sql("quiz_attempts", ATTEMPTS_SQL_FILE)

def import_all_if_empty():
    import_sql_file_if_table_empty("users", USERS_SQL_FILE)
    import_sql_file_if_table_empty("questions", QUESTIONS_SQL_FILE)
    import_sql_file_if_table_empty("quiz_attempts", ATTEMPTS_SQL_FILE)

import_all_if_empty()

# ---------------- DB HELPERS ----------------
def get_user_by_email(email):
    cursor.execute("SELECT id, username, email, password, wallet_balance FROM users WHERE email=%s", (email,))
    return cursor.fetchone()

def get_user_by_id(uid):
    cursor.execute("SELECT id, username, email, password, wallet_balance FROM users WHERE id=%s", (uid,))
    return cursor.fetchone()

def create_user(username, email, password_hash, mobile_number, age, address):
    cursor.execute(
        "INSERT INTO users (username, email, password, mobile_number, age, address, wallet_balance) VALUES (%s,%s,%s,%s,%s,%s,0)",
        (username, email, password_hash, mobile_number, age, address)
    )
    conn.commit()
    export_table_to_sql("users", USERS_SQL_FILE)
    return cursor.lastrowid

# ---------------- Other DB Helpers (unchanged) ----------------
def add_question_db(subject, question, o1, o2, o3, o4, correct):
    cursor.execute(
        "INSERT INTO questions (subject,question,option1,option2,option3,option4,correct_option) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (subject, question, o1, o2, o3, o4, correct)
    )
    conn.commit()
    export_table_to_sql("questions", QUESTIONS_SQL_FILE)
    return cursor.lastrowid

def get_questions_by_subject(subject, limit=5):
    cursor.execute("SELECT id,question,option1,option2,option3,option4,correct_option FROM questions WHERE subject=%s ORDER BY RAND() LIMIT %s", (subject, limit))
    return cursor.fetchall()

def get_all_questions_for_subject(subject):
    cursor.execute("SELECT id,question,option1,option2,option3,option4,correct_option FROM questions WHERE subject=%s ORDER BY id ASC", (subject,))
    return cursor.fetchall()

def get_question_by_id(qid):
    cursor.execute("SELECT id,subject,question,option1,option2,option3,option4,correct_option FROM questions WHERE id=%s", (qid,))
    return cursor.fetchone()

def update_question(qid, subject, question, o1,o2,o3,o4,correct):
    cursor.execute("""
        UPDATE questions
        SET subject=%s, question=%s, option1=%s, option2=%s, option3=%s, option4=%s, correct_option=%s
        WHERE id=%s
    """, (subject,question,o1,o2,o3,o4,correct,qid))
    conn.commit()
    export_table_to_sql("questions", QUESTIONS_SQL_FILE)

def delete_question(qid):
    cursor.execute("DELETE FROM questions WHERE id=%s", (qid,))
    conn.commit()
    export_table_to_sql("questions", QUESTIONS_SQL_FILE)

def save_quiz_attempt(user_id, subject, score, reward):
    now = datetime.now()
    cursor.execute("INSERT INTO quiz_attempts (user_id,subject,score,reward,timestamp) VALUES (%s,%s,%s,%s,%s)", (user_id,subject,score,reward,now))
    conn.commit()
    export_table_to_sql("quiz_attempts", ATTEMPTS_SQL_FILE)
    export_table_to_sql("users", USERS_SQL_FILE)
    return cursor.lastrowid

def get_all_users():
    cursor.execute("SELECT id,username,email,wallet_balance,mobile_number,age,address FROM users")
    return cursor.fetchall()


def delete_user(uid):
    cursor.execute("DELETE FROM users WHERE id=%s", (uid,))
    conn.commit()
    export_table_to_sql("users", USERS_SQL_FILE)

def get_all_attempts():
    cursor.execute("SELECT qa.id, qa.user_id, u.username, qa.subject, qa.score, qa.reward, qa.timestamp FROM quiz_attempts qa LEFT JOIN users u ON qa.user_id=u.id ORDER BY qa.timestamp DESC")
    return cursor.fetchall()

def get_all_subjects():
    cursor.execute("SELECT DISTINCT subject FROM questions ORDER BY subject ASC")
    rows = cursor.fetchall()
    return [r[0] for r in rows]

# ---------------- ROUTES ----------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        mobile_number = request.form.get('mobile_number')
        age = request.form.get('age')
        address = request.form.get('address')

        if not username or not email or not password or not mobile_number or not age or not address:
            flash('All fields required','danger')
            return redirect(url_for('register'))
        if get_user_by_email(email):
            flash('Email already registered','danger')
            return redirect(url_for('register'))

        pwd_hash = generate_password_hash(password)
        create_user(username,email,pwd_hash,mobile_number,int(age),address)
        flash('Registration successful. Please login.','success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = get_user_by_email(email)
        if not user:
            flash('Invalid credentials','danger'); return redirect(url_for('login'))
        uid, username, email_db, pwd_hash, wallet = user
        if not check_password_hash(pwd_hash, password):
            flash('Invalid credentials','danger'); return redirect(url_for('login'))
        session['user_id'] = uid
        session['username'] = username
        flash('Logged in successfully','success')
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out','info')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = get_user_by_id(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))
    uid, username, email, pwd, wallet = user
    return render_template('dashboard.html', username=username, wallet=float(wallet))

# ---------------- Quiz Routes ----------------
@app.route('/start_quiz/<subject>')
def start_quiz(subject):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    subject = subject.lower()
    if subject not in ['technology','science','history']:
        flash('Invalid subject','danger')
        return redirect(url_for('dashboard'))
    qs = get_questions_by_subject(subject, limit=5)
    questions = []
    for q in qs:
        qid, question, o1,o2,o3,o4, correct = q
        questions.append({
            'id': qid,
            'question': question,
            'options': [o1,o2,o3,o4]
        })
    return render_template('quiz.html', subject=subject.title(), questions=questions)

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    if 'user_id' not in session:
        return jsonify({'error':'Not logged in'}), 401
    data = request.get_json()
    subject = data.get('subject')
    answers = data.get('answers')

    score = 0
    for qid_str, sel in (answers or {}).items():
        try:
            qid = int(qid_str)
        except:
            continue
        cursor.execute("SELECT correct_option FROM questions WHERE id=%s", (qid,))
        row = cursor.fetchone()
        if not row:
            continue
        correct = row[0]
        if int(sel) + 1 == int(correct):
            score += 1

    reward = score * 100.0
    cursor.execute("UPDATE users SET wallet_balance = wallet_balance + %s WHERE id=%s", (reward, session['user_id']))
    conn.commit()
    save_quiz_attempt(session['user_id'], subject, score, reward)

    user = get_user_by_id(session['user_id'])
    if user:
        uid, username, email, pwd, wallet = user
        send_quiz_email(email, username, subject, score, reward)

    return jsonify({'score':score, 'reward': reward})

@app.route('/result')
def result():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    cursor.execute("SELECT subject,score,reward,timestamp FROM quiz_attempts WHERE user_id=%s ORDER BY timestamp DESC LIMIT 1", (session['user_id'],))
    row = cursor.fetchone()
    if not row:
        flash('No quiz attempts found','info')
        return redirect(url_for('dashboard'))
    subject, score, reward, timestamp = row
    return render_template('result.html', subject=subject, score=score, reward=float(reward), timestamp=timestamp)

# ---------------- Admin Routes ----------------
ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "admin1234"

def require_admin():
    if not session.get('admin'):
        flash('Admin login required','danger')
        return False
    return True

@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if request.method=='POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email==ADMIN_EMAIL and password==ADMIN_PASSWORD:
            session['admin']=True
            flash('Admin logged in','success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials','danger')
            return redirect(url_for('admin_login'))
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    flash('Admin logged out','info')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not require_admin():
        return redirect(url_for('admin_login'))
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM quiz_attempts")
    total_quizzes = cursor.fetchone()[0]
    cursor.execute("SELECT COALESCE(SUM(reward),0) FROM quiz_attempts")
    total_payouts = float(cursor.fetchone()[0] or 0)
    return render_template('admin_dashboard.html', total_users=total_users, total_quizzes=total_quizzes, total_payouts=total_payouts)

@app.route('/admin/subjects')
def admin_subjects():
    if not require_admin():
        return redirect(url_for('admin_login'))
    subjects = get_all_subjects()
    if not subjects:
        subjects = ['technology','science','history']
    return render_template('admin_subjects.html', subjects=subjects)

@app.route('/admin/view_questions/<subject>')
def admin_view_questions(subject):
    if not require_admin():
        return redirect(url_for('admin_login'))
    subject = subject.lower()
    questions = get_all_questions_for_subject(subject)
    return render_template('admin_view_questions.html', subject=subject, questions=questions)

@app.route('/admin/add_question', methods=['GET','POST'])
def admin_add_question():
    if not require_admin():
        return redirect(url_for('admin_login'))
    if request.method=='POST':
        subject = request.form.get('subject')
        question = request.form.get('question')
        o1 = request.form.get('option1')
        o2 = request.form.get('option2')
        o3 = request.form.get('option3')
        o4 = request.form.get('option4')
        correct = int(request.form.get('correct_option'))
        add_question_db(subject,question,o1,o2,o3,o4,correct)
        flash('Question added','success')
        return redirect(url_for('admin_subjects'))
    return render_template('admin_add_question.html')

@app.route('/admin/edit_question/<int:qid>', methods=['GET','POST'])
def admin_edit_question(qid):
    if not require_admin():
        return redirect(url_for('admin_login'))
    q = get_question_by_id(qid)
    if not q:
        flash('Question not found','danger')
        return redirect(url_for('admin_subjects'))
    if request.method == 'POST':
        subject = request.form.get('subject')
        question = request.form.get('question')
        o1 = request.form.get('option1')
        o2 = request.form.get('option2')
        o3 = request.form.get('option3')
        o4 = request.form.get('option4')
        correct = int(request.form.get('correct_option'))
        update_question(qid, subject, question, o1, o2, o3, o4, correct)
        flash('Question updated','success')
        return redirect(url_for('admin_view_questions', subject=subject))
    qid, subject, question, o1, o2, o3, o4, correct = q
    return render_template('admin_edit_question.html', qid=qid, subject=subject, question=question, option1=o1, option2=o2, option3=o3, option4=o4, correct_option=correct)

@app.route('/admin/delete_question/<int:qid>', methods=['POST'])
def admin_delete_question(qid):
    if not require_admin():
        return redirect(url_for('admin_login'))
    q = get_question_by_id(qid)
    subject = q[1] if q else ''
    delete_question(qid)
    flash('Question deleted','info')
    if subject:
        return redirect(url_for('admin_view_questions', subject=subject))
    return redirect(url_for('admin_subjects'))

@app.route('/admin/users')
def admin_view_users():
    if not require_admin():
        return redirect(url_for('admin_login'))
    users = get_all_users()
    return render_template('admin_users.html', users=users)

@app.route('/admin/delete_user/<int:uid>', methods=['POST'])
def admin_delete_user(uid):
    if not require_admin():
        return redirect(url_for('admin_login'))
    delete_user(uid)
    flash('User deleted','info')
    return redirect(url_for('admin_view_users'))

@app.route('/admin/attempts')
def admin_view_attempts():
    if not require_admin():
        return redirect(url_for('admin_login'))
    attempts = get_all_attempts()
    return render_template('admin_attempts.html', attempts=attempts)

@app.route('/admin_data', methods=['POST'])
def admin_data():
    data = request.get_json()
    password = data.get('password')
    if password != ADMIN_PASSWORD:
        return jsonify({'error':'Invalid password'})
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM quiz_attempts")
    total_quizzes = cursor.fetchone()[0]
    cursor.execute("SELECT COALESCE(SUM(reward),0) FROM quiz_attempts")
    total_payouts = float(cursor.fetchone()[0] or 0)
    return jsonify({'total_users': total_users, 'total_quizzes': total_quizzes, 'total_payouts': total_payouts})

if __name__=='__main__':
    app.run(debug=True)
