from flask import Flask, render_template, request, redirect, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize Database
def init_db():
    conn = sqlite3.connect('coincave.db')
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        date TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS category_limits (
        category TEXT PRIMARY KEY,
        category_limit REAL NOT NULL
    )
    ''')

    conn.commit()
    conn.close()

init_db()


# Home Route
@app.route('/')
def home():
    return render_template('home.html')


# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('coincave.db')
        cursor = conn.cursor()

        try:
            cursor.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, password))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect('/login')
        except sqlite3.IntegrityError:
            flash('Email already exists!', 'danger')
        finally:
            conn.close()

    return render_template('register.html')


# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('coincave.db')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
        user = cursor.fetchone()

        conn.close()

        if user:
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            return redirect('/dashboard')
        else:
            flash('Invalid email or password!', 'danger')

    return render_template('login.html')


# Dashboard Route
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('coincave.db')
    cursor = conn.cursor()

    cursor.execute('SELECT SUM(amount) FROM expenses WHERE user_id = ?', (session['user_id'],))
    total_expenses = cursor.fetchone()[0] or 0.0

    conn.close()

    return render_template('dashboard.html', user_name=session['user_name'], total_expenses=total_expenses)


# Track Expense Route
@app.route('/track_expense', methods=['GET', 'POST'])
def track_expense():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        amount = float(request.form['amount'])
        category = request.form['category']
        date = request.form['date']

        conn = sqlite3.connect('coincave.db')
        cursor = conn.cursor()

        cursor.execute('INSERT INTO expenses (amount, category, date, user_id) VALUES (?, ?, ?, ?)', 
                       (amount, category, date, session['user_id']))

        conn.commit()
        conn.close()

        flash('Expense added successfully!', 'success')

    conn = sqlite3.connect('coincave.db')
    cursor = conn.cursor()

    cursor.execute('SELECT category, SUM(amount) FROM expenses WHERE user_id = ? GROUP BY category', (session['user_id'],))
    category_totals = dict(cursor.fetchall())

    cursor.execute('SELECT SUM(amount) FROM expenses WHERE user_id = ?', (session['user_id'],))
    total_expenses = cursor.fetchone()[0] or 0.0

    cursor.execute('SELECT * FROM expenses WHERE user_id = ?', (session['user_id'],))
    expenses = cursor.fetchall()

    conn.close()

    return render_template(
        'expense_tracker.html',
        expenses=expenses,
        total_expenses=total_expenses,
        category_totals_keys=list(category_totals.keys()),
        category_totals_values=list(category_totals.values()),
        user_name=session['user_name']
    )


# Logout Route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
