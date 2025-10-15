from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Load teacher data from JSON file
def load_teachers():
    try:
        with open('teacherdata.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []

# Get teacher details by staff ID
def get_teacher_details(staff_id):
    teachers = load_teachers()
    for teacher in teachers:
        if str(teacher['staffId']) == str(staff_id):
            return teacher
    return None

# Database initialization
def init_db():
    conn = sqlite3.connect('leave_system.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database
init_db()

@app.route('/')
def index():
    teachers = load_teachers()
    return render_template('index.html', teachers=teachers)

@app.route('/check_status')
def check_status():
    return render_template('check_status.html')

@app.route('/search_status', methods=['POST'])
def search_status():
    staff_id = request.form['staff_id']
    
    if not staff_id:
        flash('Please enter a Staff ID!')
        return redirect(url_for('check_status'))
    
    # Get teacher details
    teacher_details = get_teacher_details(staff_id)
    if not teacher_details:
        flash('Invalid Staff ID! Teacher not found.')
        return redirect(url_for('check_status'))
    
    # Get leave requests for this teacher
    conn = sqlite3.connect('leave_system.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM leave_requests WHERE teacher_id = ? ORDER BY created_at DESC', (staff_id,))
    requests = cursor.fetchall()
    conn.close()
    
    return render_template('check_status.html', 
                         teacher_details=teacher_details, 
                         requests=requests, 
                         searched=True)

@app.route('/admin')
def admin():
    conn = sqlite3.connect('leave_system.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM leave_requests ORDER BY created_at DESC')
    requests = cursor.fetchall()
    conn.close()
    
    # Add teacher details to each request
    requests_with_details = []
    for request in requests:
        teacher_details = get_teacher_details(request[1])
        requests_with_details.append({
            'id': request[0],
            'teacher_id': request[1],
            'description': request[2],
            'status': request[3],
            'created_at': request[4],
            'teacher_details': teacher_details
        })
    
    return render_template('admin.html', requests=requests_with_details)

@app.route('/submit_leave', methods=['POST'])
def submit_leave():
    teacher_id = request.form['teacher_id']
    description = request.form['description']
    
    if not teacher_id or not description:
        flash('Please fill all fields!')
        return redirect(url_for('index'))
    
    # Check if teacher exists
    teacher_details = get_teacher_details(teacher_id)
    if not teacher_details:
        flash('Invalid Teacher ID! Please enter a valid Staff ID from the list.')
        return redirect(url_for('index'))
    
    conn = sqlite3.connect('leave_system.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO leave_requests (teacher_id, description) VALUES (?, ?)', 
                  (teacher_id, description))
    conn.commit()
    conn.close()
    
    flash(f'Leave request submitted successfully for {teacher_details["name"]}!')
    return redirect(url_for('index'))

@app.route('/approve/<int:request_id>')
def approve_leave(request_id):
    conn = sqlite3.connect('leave_system.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE leave_requests SET status = ? WHERE id = ?', ('approved', request_id))
    conn.commit()
    conn.close()
    flash('Leave request approved!')
    return redirect(url_for('admin'))

@app.route('/reject/<int:request_id>')
def reject_leave(request_id):
    conn = sqlite3.connect('leave_system.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE leave_requests SET status = ? WHERE id = ?', ('rejected', request_id))
    conn.commit()
    conn.close()
    flash('Leave request rejected!')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
