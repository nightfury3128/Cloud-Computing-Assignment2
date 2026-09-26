# Generative AI was used for sqlite database creation and fixing errors
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import sqlite3
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'users.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            firstname TEXT NOT NULL,
            lastname TEXT NOT NULL,
            email TEXT NOT NULL,
            address TEXT NOT NULL,
            filename TEXT,
            wordcount INTEGER
        )
    ''')
    conn.commit()
    conn.close()


def count_words(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    return len(text.split())


init_db()


@app.route('/')
def index():
    return render_template('register.html')


@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    firstname = request.form['firstname']
    lastname = request.form['lastname']
    email = request.form['email']
    address = request.form['address']

    filename = None
    wordcount = None

    file = request.files.get('file')
    if file and file.filename:
        filename = username + '_' + os.path.basename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        wordcount = count_words(filepath)

    conn = get_db()
    conn.execute(
        '''INSERT OR REPLACE INTO users
           (username, password, firstname, lastname, email, address, filename, wordcount)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (username, password, firstname, lastname, email, address, filename, wordcount)
    )
    conn.commit()
    conn.close()

    return redirect(url_for('profile', username=username))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form['username']
    password = request.form['password']

    conn = get_db()
    user = conn.execute(
        'SELECT * FROM users WHERE username=? AND password=?',
        (username, password)
    ).fetchone()
    conn.close()

    if user:
        return redirect(url_for('profile', username=username))

    return render_template('login.html', error='Invalid username or password')


@app.route('/profile/<username>')
def profile(username):
    conn = get_db()
    user = conn.execute(
        'SELECT * FROM users WHERE username=?',
        (username,)
    ).fetchone()
    conn.close()

    if not user:
        return redirect(url_for('index'))

    return render_template('profile.html', user=user)


@app.route('/download/<username>')
def download(username):
    conn = get_db()
    user = conn.execute(
        'SELECT filename FROM users WHERE username=?',
        (username,)
    ).fetchone()
    conn.close()

    if not user or not user['filename']:
        return 'File not found', 404

    return send_from_directory(UPLOAD_FOLDER, user['filename'], as_attachment=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
