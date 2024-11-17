from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from models import db, User, Event, Participated
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()
username = os.getenv('MYSQLUSERNAME')
password = os.getenv('MYSQLPASS')


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://{username}:{password}@localhost/event_db'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_email_password'

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
mail = Mail(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return redirect(url_for('login'))

# Login, Signup, and Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials!')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone_number = request.form['phone']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        user = User(name=name, email=email, phone_number=phone_number, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please log in.')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/dashboard')
@login_required
def dashboard():
    upcoming_events = Event.query.filter(Event.date >= datetime.now(), Event.id != current_user.id).all()
    organized_events = Event.query.filter_by(organizer_id=current_user.id).all()
    return render_template('dashboard.html', upcoming_events=upcoming_events, organized_events=organized_events)

@app.route('/create_event', methods=['GET', 'POST'])
@login_required
def create_event():
    if request.method == 'POST':
        name = request.form['name']
        place = request.form['place']
        date = datetime.strptime(request.form['date'], '%Y-%m-%d')
        time = datetime.strptime(request.form['time'], '%H:%M').time()
        event = Event(name=name, place=place, date=date, time=time, organizer_id=current_user.id)
        db.session.add(event)
        db.session.commit()
        flash('Event created successfully!')
        return redirect(url_for('dashboard'))
    return render_template('create_event.html')

@app.route('/manage_event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def manage_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.organizer_id != current_user.id:
        flash('Unauthorized access!')
        return redirect(url_for('dashboard'))
    participants = Participated.query.filter_by(event_id=event.id).all()
    return render_template('manage_event.html', event=event, participants=participants)

@app.route('/participate/<int:event_id>')
@login_required
def participate(event_id):
    existing_participation = Participated.query.filter_by(user_id=current_user.id, event_id=event_id).first()
    if existing_participation:
        flash('You are already enrolled in this event!')
        return redirect(url_for('dashboard'))
    participation = Participated(user_id=current_user.id, event_id=event_id)
    db.session.add(participation)
    db.session.commit()
    flash('You have successfully enrolled in the event!')
    return redirect(url_for('dashboard'))

@app.before_request
def send_reminders():
    events = Event.query.all()
    for event in events:
        if (event.date - timedelta(days=1)) == datetime.now().date():
            participants = Participated.query.filter_by(event_id=event.id).all()
            for participant in participants:
                user = User.query.get(participant.user_id)
                msg = Message('Event Reminder', sender='your_email@gmail.com', recipients=[user.email])
                msg.body = f"Reminder for your event: {event.name} at {event.place} on {event.date} {event.time}."
                mail.send(msg)



if __name__ == '__main__':
    app.run(debug=True)
