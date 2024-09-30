from flask import Flask, render_template, request, redirect, session, flash
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
import sqlite3

app = Flask(__name__)
app.secret_key = "secret_key"  # Set a secret key for session management

# Load dataset
dataset = pd.read_csv("D:/final/policy.csv")

# Separate features and target
X = dataset.iloc[:, [0, 1]].values
y = dataset.iloc[:, 2].values

# Fit the model
model = DecisionTreeClassifier()
model.fit(X, y)

# Function to save user data to the database
def save_to_database(name, email, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (name TEXT, email TEXT, password TEXT)')
    c.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, password))
    conn.commit()
    conn.close()

# Function to save feedback data to the database
def save_feedback(name, email, feedback, rating):
    conn = sqlite3.connect('feedback.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS feedback (name TEXT, email TEXT, feedback TEXT, rating INTEGER)')
    c.execute('INSERT INTO feedback (name, email, feedback, rating) VALUES (?, ?, ?, ?)', (name, email, feedback, rating))
    conn.commit()
    conn.close()

# Function to fetch data from the users table
def get_users_data():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users')
    users_data = c.fetchall()
    conn.close()
    return users_data

# Function to fetch data from the feedback table
def get_feedback_data():
    conn = sqlite3.connect('feedback.db')
    c = conn.cursor()
    c.execute('SELECT * FROM feedback')
    feedback_data = c.fetchall()
    conn.close()
    return feedback_data

# Function to check user credentials against the database
def check_user(email, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email=? AND password=?', (email, password))
    user = c.fetchone()
    conn.close()
    return user is not None

# Define route for home page
@app.route('/')
def home():
    return render_template('front.html')

# Define route for registration form
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        # Save user data to the database
        save_to_database(name, email, password)
        
        # Redirect to login page after registration
        return redirect('/login')
    else:
        return render_template('register.html')
    
    # Define route for about
@app.route('/about', methods=['GET', 'POST'])
def about():
     return render_template('about.html')

# Define route for login form
@app.route('/login', methods=['GET', 'POST'])
def login():
    error_message = None
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Check if the user exists in the database
        if check_user(email, password):
            # Set session for logged-in user
            session['logged_in'] = True
            session['email'] = email
            
            # Redirect to prediction page after successful login
            return redirect('/predict')
        else:
            # Display error message for invalid credentials
            error_message = "Invalid email or password. Please try again."
    
    # Render login template with error message
    return render_template('login.html', error=error_message)

# Define route for admin page
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    error_message = None
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Check if the provided email and password match the admin credentials
        if email == 'admin@gmail.com' and password == 'admin':
            # Set session for admin
            session['admin_logged_in'] = True
            return redirect('/data')  # Redirect to home page after admin login
        else:
            error_message = "Invalid admin credentials. Please try again."

    return render_template('admin.html', error=error_message)

# Define route for feedback form
@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        feedback = request.form['feedback']
        rating = int(request.form['rating'])
        
        # Save feedback data to the database
        save_feedback(name, email, feedback, rating)
        
        # Redirect to prediction page
        return redirect('/predict')
    else:
        return render_template('feedback.html')

# Define route to display all data and provide options to add/delete
@app.route('/data')
def view_data():
    users_data = get_users_data()
    feedback_data = get_feedback_data()
    return render_template('view_data.html', users_data=users_data, feedback_data=feedback_data)

# Define route to add new user data
@app.route('/add_user', methods=['POST'])
def add_user():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, password))
    conn.commit()
    conn.close()
    
    flash('User added successfully!', 'success')
    return redirect('/data')

# Define route to delete user
@app.route('/delete_user', methods=['POST'])
def delete_user():
    email = request.form['email']
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE email=?', (email,))
    conn.commit()
    conn.close()
    flash('User deleted successfully!', 'success')
    return redirect('/data')

# Define route for prediction page
@app.route('/predict', methods=['GET', 'POST'])
def predict():
    error_message = request.args.get('error_message')
    if request.method == 'POST':
        age = int(request.form['age'])
        income = int(request.form['income'])
        prediction = model.predict([[age, income]])
        return render_template('predict.html', prediction_text='Recommended policy: {}'.format(prediction[0]), error_message=error_message)
    else:
        return render_template('predict.html', error_message=error_message)

if __name__ == "__main__":
    app.run(debug=True)
