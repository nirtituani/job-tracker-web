#!/usr/bin/env python3
"""
Job Application Tracker - Web Version
Mobile-optimized Flask application for tracking job applications from anywhere
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import csv
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///job_applications.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Fix for Render.com PostgreSQL URL
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(200), nullable=False)
    job_title = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200))
    date_applied = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default='Applied')
    salary_range = db.Column(db.String(100))
    job_link = db.Column(db.String(500))
    contact_person = db.Column(db.String(200))
    contact_email = db.Column(db.String(200))
    job_match = db.Column(db.Integer)
    notes = db.Column(db.Text)
    last_updated = db.Column(db.String(50), nullable=False)

# Initialize database
with app.app_context():
    db.create_all()
    # Create default user if not exists (username: admin, password: admin)
    if not User.query.filter_by(username='admin').first():
        default_user = User(username='admin')
        default_user.set_password('admin')
        db.session.add(default_user)
        db.session.commit()

# Login required decorator
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    search = request.args.get('search', '')
    status_filter = request.args.get('status', 'All')
    
    query = Application.query
    
    # Apply search filter
    if search:
        query = query.filter(
            (Application.company_name.ilike(f'%{search}%')) |
            (Application.job_title.ilike(f'%{search}%')) |
            (Application.location.ilike(f'%{search}%'))
        )
    
    # Apply status filter
    if status_filter != 'All':
        query = query.filter_by(status=status_filter)
    
    # Sort by ID descending (newest first)
    applications = query.order_by(Application.id.desc()).all()
    
    # Calculate statistics
    total = Application.query.count()
    status_counts = {}
    for status in ['Applied', 'Phone Screen', 'First Interview', 'Second Interview', 
                   'Third Interview', 'Final Interview', 'Offer Received', 'Rejected', 'Ghosted', 'Withdrawn']:
        count = Application.query.filter_by(status=status).count()
        if count > 0:
            status_counts[status] = count
    
    return render_template('index.html', 
                         applications=applications, 
                         total=total,
                         status_counts=status_counts,
                         search=search,
                         status_filter=status_filter)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_application():
    if request.method == 'POST':
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        job_match = request.form.get('job_match')
        job_match_value = int(job_match) if job_match and job_match.isdigit() else None
        
        app_data = Application(
            company_name=request.form.get('company_name'),
            job_title=request.form.get('job_title'),
            location=request.form.get('location'),
            date_applied=request.form.get('date_applied', datetime.now().strftime("%d/%m/%Y")),
            status=request.form.get('status', 'Applied'),
            salary_range=request.form.get('salary_range'),
            job_link=request.form.get('job_link'),
            contact_person=request.form.get('contact_person'),
            contact_email=request.form.get('contact_email'),
            job_match=job_match_value,
            notes=request.form.get('notes'),
            last_updated=now
        )
        
        db.session.add(app_data)
        db.session.commit()
        
        flash('Application added successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('add.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_application(id):
    application = Application.query.get_or_404(id)
    
    if request.method == 'POST':
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        job_match = request.form.get('job_match')
        job_match_value = int(job_match) if job_match and job_match.isdigit() else None
        
        application.company_name = request.form.get('company_name')
        application.job_title = request.form.get('job_title')
        application.location = request.form.get('location')
        application.date_applied = request.form.get('date_applied')
        application.status = request.form.get('status')
        application.salary_range = request.form.get('salary_range')
        application.job_link = request.form.get('job_link')
        application.contact_person = request.form.get('contact_person')
        application.contact_email = request.form.get('contact_email')
        application.job_match = job_match_value
        application.notes = request.form.get('notes')
        application.last_updated = now
        
        db.session.commit()
        
        flash('Application updated successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('edit.html', application=application)

@app.route('/delete/<int:id>')
@login_required
def delete_application(id):
    application = Application.query.get_or_404(id)
    db.session.delete(application)
    db.session.commit()
    
    flash('Application deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/view/<int:id>')
@login_required
def view_application(id):
    application = Application.query.get_or_404(id)
    return render_template('view.html', application=application)

@app.route('/export')
@login_required
def export_csv():
    applications = Application.query.order_by(Application.id.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Company Name', 'Job Title', 'Location', 'Date Applied', 'Status',
                    'Salary Range', 'Job Link', 'Contact Person', 'Contact Email', 
                    'Job Match', 'Notes', 'Last Updated'])
    
    # Write data
    for app in applications:
        writer.writerow([
            app.company_name,
            app.job_title,
            app.location or '',
            app.date_applied,
            app.status,
            app.salary_range or '',
            app.job_link or '',
            app.contact_person or '',
            app.contact_email or '',
            app.job_match or '',
            app.notes or '',
            app.last_updated
        ])
    
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'job_applications_{datetime.now().strftime("%d%m%Y")}.csv'
    )

@app.route('/stats')
@login_required
def stats():
    total = Application.query.count()
    
    status_counts = {}
    for status in ['Applied', 'Phone Screen', 'First Interview', 'Second Interview', 
                   'Third Interview', 'Final Interview', 'Offer Received', 'Rejected', 'Ghosted', 'Withdrawn']:
        count = Application.query.filter_by(status=status).count()
        if count > 0:
            status_counts[status] = count
    
    # Recent applications
    recent = Application.query.order_by(Application.id.desc()).limit(5).all()
    
    # Match rating distribution
    match_counts = {}
    for i in range(1, 6):
        count = Application.query.filter_by(job_match=i).count()
        if count > 0:
            match_counts[i] = count
    
    return render_template('stats.html', 
                         total=total,
                         status_counts=status_counts,
                         recent=recent,
                         match_counts=match_counts)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
