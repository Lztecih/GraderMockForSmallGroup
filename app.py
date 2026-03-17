import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, send_from_directory, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from grader import run_grader

app = Flask(__name__)
app.secret_key = "super_secret_grader_key"

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS submissions 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT, problem_id TEXT, status TEXT, score INTEGER, timestamp DATETIME, code TEXT)''')
    try:
        c.execute("ALTER TABLE submissions ADD COLUMN code TEXT")
    except sqlite3.OperationalError:
        pass 
    conn.commit()
    conn.close()

init_db()

def get_active_problems():
    problems_dict = {}
    problems_dir = "problems"
    if not os.path.exists(problems_dir): return problems_dict
    for folder_name in os.listdir(problems_dir):
        folder_path = os.path.join(problems_dir, folder_name)
        if os.path.isdir(folder_path):
            title_path = os.path.join(folder_path, "title.txt")
            if os.path.exists(title_path):
                with open(title_path, "r") as f: title = f.read().strip()
            else:
                title = folder_name.replace("_", " ").title()
            problems_dict[folder_name] = title
    return problems_dict

def get_user_total_score(username, active_problems):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''SELECT problem_id, MAX(score) FROM submissions 
                 WHERE username=? GROUP BY problem_id''', (username,))
    rows = c.fetchall()
    conn.close()
    
    total = 0
    for pid, score in rows:
        if pid in active_problems:
            total += score
    return total

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, generate_password_hash(password)))
            conn.commit()
            flash("Registration successful! Please login.")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username already exists!")
        finally:
            conn.close()
    return render_template('login.html', action="Register")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[0], password):
            session['username'] = username
            return redirect(url_for('home'))
        else:
            flash("Invalid username or password.")
    return render_template('login.html', action="Login")

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/', methods=['GET'])
def home():
    active_problems = get_active_problems() 
    user_score = get_user_total_score(session.get('username'), active_problems) if 'username' in session else 0
    return render_template('index.html', problems=active_problems, score=user_score)

@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    active_problems = get_active_problems()
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''SELECT username, problem_id, MAX(score) FROM submissions GROUP BY username, problem_id''')
    rows = c.fetchall()
    conn.close()
    
    user_scores = {}
    for username, pid, score in rows:
        if pid in active_problems:
            user_scores[username] = user_scores.get(username, 0) + score
            
    rankings = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)
    return render_template('leaderboard.html', rankings=rankings)

@app.route('/pdf/<problem_id>')
def serve_pdf(problem_id):
    active_problems = get_active_problems()
    if problem_id not in active_problems: return "PDF not found!", 404
    return send_from_directory(f'problems/{problem_id}', 'problem.pdf')

@app.route('/problem/<problem_id>', methods=['GET'])
def problem_page(problem_id):
    active_problems = get_active_problems()
    if problem_id not in active_problems: 
        return "Problem not found or has been deleted!", 404
        
    history = []
    if 'username' in session:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT status, score, timestamp, code FROM submissions WHERE username=? AND problem_id=? ORDER BY timestamp DESC", 
                  (session['username'], problem_id))
        history = c.fetchall()
        conn.close()
    return render_template('problem.html', problem_id=problem_id, title=active_problems[problem_id], history=history)

@app.route('/submit/<problem_id>', methods=['POST'])
def submit_code(problem_id):
    if 'username' not in session: return redirect(url_for('login'))
    
    active_problems = get_active_problems()
    if problem_id not in active_problems:
        return "You cannot submit. Problem has been removed!", 404

    user_code = request.form['code']
    language = request.form['language'] 
    
    ext = ".cpp" if language == "cpp" else ".c"
    submission_filename = f"solution{ext}"
    
    with open(f"submissions/{submission_filename}", "w") as f:
        f.write(user_code)
        
    status, score, summary, test_results = run_grader(submission_filename, problem_id, language)
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO submissions (username, problem_id, status, score, timestamp, code) VALUES (?, ?, ?, ?, ?, ?)",
              (session['username'], problem_id, status, score, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_code))
    conn.commit()
    
    c.execute("SELECT status, score, timestamp, code FROM submissions WHERE username=? AND problem_id=? ORDER BY timestamp DESC", 
              (session['username'], problem_id))
    history = c.fetchall()
    conn.close()
        
    return render_template('problem.html', problem_id=problem_id, title=active_problems[problem_id], 
                           result=status, score=score, summary=summary, test_results=test_results, user_code=user_code, 
                           history=history, submitted_lang=language, active_tab="editor")

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=6767)