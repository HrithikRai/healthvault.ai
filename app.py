from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from backend.agentic_flow import process_files_in_directory
from backend.rag import update_rag_chain

app = Flask(__name__)

# Mock user database 
users = {
    "user@example.com": "password123",
    "test@healthvault.ai": "testpass",
    "test@gmail.com": "test"
}

# Setting the folder to save uploaded files
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if email == 'test@gmail.com' and password == 'test':
            session['user'] = email
            return redirect(url_for('dashboard'))  
        # Only redirect to home if credentials are wrong
        flash("Invalid credentials, try again.", "danger")
        return redirect(url_for('home'))  

    return render_template('login.html') 

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], "patient1","temp_upload", file.filename)
            file.save(filepath)
            flash('File successfully uploaded, Eva is now analysing your upload...')
            process_files_in_directory(filepath)
            flash('File successfully Analysed, Eva is now updating herself with the data analysed...')
            update_rag_chain()
            flash('Eva is Ready...')
            return redirect(url_for('dashboard'))
    
    return render_template('upload_file.html')
    
@app.route('/virtual_assistant')
def virtual_assistant():
    return render_template('virtual_assistant.html')

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out successfully.", "info")
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.secret_key = 'supersecretkey'
    app.run(debug=True)




