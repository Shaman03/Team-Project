from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, abort #Imports from flask Tazneem code
import os
from werkzeug.security import generate_password_hash, check_password_hash #Import for paswword hashing security implementation 
import sqlite3 #Import to use SQLite3 inbuilt vs
import datetime
from werkzeug.utils import secure_filename #Import for secure file storing

app = Flask(__name__)
app.secret_key = os.urandom(24) #App secret key is generated by a random 24byte key

# Database declarationn
DATABASE = 'users.db'

# Initialise the database
def initialize_database():
    init_db() #calls the init function

#Initialise the SQLite database and create necessary tables.
def init_db():
    conn = sqlite3.connect(DATABASE) #Connects the databse 
    cursor = conn.cursor()
    
    # Single table for users and related info
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        department TEXT,
        job_title TEXT,
        phone_number TEXT,
        address TEXT,
        salary REAL,
        cv_filename TEXT,
        upload_time TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()

#Route to hompage once app is running
@app.route('/')
def home():
    if 'username' in session:#checks if the user is logged in  and redirects to UserProfile if not renders the homepage 
        return redirect(url_for('UserProfile'))
    return render_template('homePage.html')

#Route for register page saves the information in the users db
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['user_pwd']
        confirm_password = request.form['user_pwd1']
        
        if password != confirm_password:
            return "Passwords do not match.", 400

        hashed_password = generate_password_hash(password)
        
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, hashed_password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Email already registered.", 400
    
    return render_template('Register.html') #Renders Register page 

#Checks the information in the databse and logs the user in if successful
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:#Checks if the user is in session and redirects 
        return redirect(url_for('UserProfile'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['user_pwd0']
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[3], password):  #user[3] is the hashed password
            session['user_id'] = user[0]  # Store user_id in session
            session['username'] = user[1]  # Store the name in the session
            return redirect(url_for('UserProfile'))
        else:
            return "Invalid email or password.", 401
    
    return render_template('Login.html')#Renders login page 


# File Upload Config where to save uploaded files and what type of docs to accept 
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

#Checks if file is accepted 
def allowed_file(filename):
    """Check if the uploaded file is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#Renders User Profile page 
@app.route('/UserProfile', methods=['GET', 'POST'])
def UserProfile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('UserProfile.html', username=session['username'])


#Function is used to save the users input on the main page 
@app.route('/save_user_profile', methods=['POST'])
def save_user_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Retrieves form data from the frontend page 
    department = request.form.get('department')
    job_title = request.form.get('job_title')
    phone_number = request.form.get('phone_number')
    address = request.form.get('address')
    salary = request.form.get('salary')
    file = request.files.get('file')  # Get file from form

    # Ensure all form data is correctly retrieved
    if not all([department, job_title, phone_number, address, salary]):
        return 'All fields are required.', 400

    # Ensure file upload if a file is provided
    cv_filename = None
    if file and allowed_file(file.filename):
        cv_filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], cv_filename)) #Saves file to uploads folder and name to db
    
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Update users table in the database
        cursor.execute('''
            UPDATE users
            SET department = ?, job_title = ?, phone_number = ?, address = ?, salary = ?, cv_filename = ?, upload_time = ?
            WHERE id = ?
        ''', (department, job_title, phone_number, address, float(salary), cv_filename, datetime.datetime.now(), user_id))
        
        conn.commit()
        conn.close()
        return 'User profile updated successfully.', 200
    except sqlite3.Error as e:
        return f'Error saving user profile: {e}', 500


#Functon to handle uploaded files save to upload folder
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id'] #Saves by user id giving by flask session
    file = request.files.get('file') #Get file name 
    if file and allowed_file(file.filename): #Gets file name 
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        #Sets file name and time uploaded in db 
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users
            SET cv_filename = ?, upload_time = ?
            WHERE id = ?
        ''', (filename, datetime.datetime.now(), user_id)) #Upload time is set by the datetime.datetime.now 
        conn.commit()
        conn.close()
        return 'File uploaded successfully.', 200
    else:
        return 'Invalid file.', 400
    
#Display info function called by the frontend JS UserProfile
@app.route('/display_info', methods=['GET'])
def display_info():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor() #Selects from the field and retrieves the data that displays on the user page 
    cursor.execute('''
        SELECT name, email, department, job_title, phone_number, address, salary, cv_filename
        FROM users WHERE id = ?
    ''', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'error': 'User profile not found'}), 404
    
    return jsonify({  # Returns the retrieved data in JSON
        'name': user[0],
        'email': user[1],
        'department': user[2] or "N/A",
        'job_title': user[3] or "N/A",
        'phone_number': user[4] or "N/A",
        'address': user[5] or "N/A",
        'salary': user[6] or "N/A",
        'cv_filename': user[7] or "N/A"
    })

#Function for retrieving the upload and filename
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    if 'user_id' not in session:
        abort(403)
    
    user_id = session['user_id'] #Uses the user id to retrieve the uplaoded cv file name 
    conn = sqlite3.connect(DATABASE) #Connects the databse 
    cursor = conn.cursor()
    cursor.execute("SELECT cv_filename FROM users WHERE id = ?", (user_id,)) 
    user_cv = cursor.fetchone() #Fetche the cv 
    conn.close()
    

    if user_cv and user_cv[0] == filename: #Ensuring there is a valid user CV record
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)  #Allowed to access the file
    else:
        abort(403)

#function to log out user 
@app.route('/logout', methods=['GET'])
def logout():
    session.pop('username', None)  # Remove the username from session to log out
    return redirect(url_for('home'))#Brings them back to the homepage

if __name__ == '__main__':
    init_db()  # Ensure the database is initialized
    app.run(debug=True)

 