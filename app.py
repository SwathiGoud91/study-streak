from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import random
from datetime import datetime

app = Flask(__name__)

app.secret_key = 'study_streak_secret'

# =========================
# DATABASE CONFIGURATION
# =========================
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///study_streak.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =========================
# MOTIVATIONAL QUOTES
# =========================
quotes = [

    "Success comes from consistency.",

    "Small progress is still progress.",

    "Study now, shine later.",

    "Discipline beats motivation.",

    "Your future is created today.",

    "Every study session counts.",

    "Dream big and work daily.",

    "Push yourself a little more today."

]

# =========================
# USER MODEL
# =========================
class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(100), unique=True, nullable=False)

    password = db.Column(db.String(300), nullable=False)

    streak = db.Column(db.Integer, default=0)

    badge = db.Column(db.String(100), default="Beginner")

    daily_goal = db.Column(db.Integer, default=60)

    xp = db.Column(db.Integer, default=0)

    level = db.Column(db.Integer, default=1)

    last_quiz_day = db.Column(db.Integer, default=0)

    today_quote_index = db.Column(db.Integer, default=-1)

    today_quote_day = db.Column(db.Integer, default=0)

    today_quiz_index = db.Column(db.Integer, default=-1)

    today_quiz_day = db.Column(db.Integer, default=0)

# =========================
# STUDY SESSION MODEL
# =========================
class StudySession(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    subject = db.Column(db.String(100), nullable=False)

    duration = db.Column(db.Integer, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# =========================
# USED QUOTES MODEL
# =========================
class UsedQuote(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer)

    quote_index = db.Column(db.Integer)

# =========================
# USED QUIZ MODEL
# =========================
class UsedQuiz(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer)

    quiz_index = db.Column(db.Integer)

# =========================
# HOME ROUTE
# =========================
@app.route('/')
def home():

    return render_template('index.html')

# =========================
# REGISTER ROUTE
# =========================
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']

        email = request.form['email']

        password = request.form['password']

        hashed_password = generate_password_hash(password)

        new_user = User(
            name=name,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)

        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

# =========================
# LOGIN ROUTE
# =========================
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']

        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):

            session['user_id'] = user.id

            return redirect(url_for('dashboard'))

        else:

            return "Invalid Email or Password"

    return render_template('login.html')

# =========================
# DASHBOARD ROUTE
# =========================
@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    sessions = StudySession.query.filter_by(
        user_id=session['user_id']
    ).all()

    total_time = 0

    for session_data in sessions:

        total_time += session_data.duration

    # =========================
    # CHART DATA
    # =========================
    subjects = []

    durations = []

    for session_data in sessions:

        subjects.append(session_data.subject)

        durations.append(session_data.duration)

    # =========================
    # DAILY UNIQUE QUOTE LOGIC
    # =========================
    today = datetime.now().day

    if user.today_quote_day != today:

        used_quotes = UsedQuote.query.filter_by(
            user_id=user.id
        ).all()

        used_indexes = []

        for item in used_quotes:

            used_indexes.append(item.quote_index)

        available_indexes = []

        for i in range(len(quotes)):

            if i not in used_indexes:

                available_indexes.append(i)

        # Reset after all quotes used
        if len(available_indexes) == 0:

            UsedQuote.query.filter_by(
                user_id=user.id
            ).delete()

            db.session.commit()

            available_indexes = list(range(len(quotes)))

        selected_index = random.choice(available_indexes)

        # Save Today's Quote
        user.today_quote_index = selected_index

        user.today_quote_day = today

        db.session.add(
            UsedQuote(
                user_id=user.id,
                quote_index=selected_index
            )
        )

        db.session.commit()

    # Same Quote Whole Day
    quote = quotes[user.today_quote_index]

    return render_template(
        'dashboard.html',
        sessions=sessions,
        user=user,
        total_time=total_time,
        subjects=subjects,
        durations=durations,
        quote=quote
    )

# =========================
# LEADERBOARD ROUTE
# =========================
@app.route('/leaderboard')
def leaderboard():

    users = User.query.order_by(User.xp.desc()).all()

    return render_template(
        'leaderboard.html',
        users=users
    )

# =========================
# TIMER ROUTE
# =========================
@app.route('/timer')
def timer():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('timer.html')

# =========================
# LOGOUT ROUTE
# =========================
@app.route('/logout')
def logout():

    session.pop('user_id', None)

    return redirect(url_for('login'))

# =========================
# GOAL SETTING ROUTE
# =========================
@app.route('/set-goal', methods=['GET', 'POST'])
def set_goal():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':

        goal = request.form['goal']

        user.daily_goal = int(goal)

        db.session.commit()

        return redirect(url_for('dashboard'))

    return render_template('goal.html')

# =========================
# STUDY SESSION ROUTE
# =========================
@app.route('/study', methods=['GET', 'POST'])
def study():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':

        subject = request.form['subject']

        duration = int(request.form['duration'])

        session_data = StudySession(
            subject=subject,
            duration=duration,
            user_id=session['user_id']
        )

        db.session.add(session_data)

        user = User.query.get(session['user_id'])

        if user:

            # Increase Streak
            user.streak += 1

            # Add XP
            user.xp += 10

            # Level System
            user.level = (user.xp // 50) + 1

            # Badge Logic
            if user.streak >= 20:

                user.badge = "Master Learner"

            elif user.streak >= 10:

                user.badge = "Pro Learner"

            elif user.streak >= 5:

                user.badge = "Consistent Learner"

            else:

                user.badge = "Beginner"

        db.session.commit()

        return redirect(url_for('dashboard'))

    return render_template('study.html')

# =========================
# DAILY QUIZ ROUTE
# =========================
@app.route('/daily-quiz', methods=['GET', 'POST'])
def daily_quiz():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    quiz_questions = [

        {
            "question": "Which language is used for Flask?",
            "options": ["Java", "Python", "C++", "PHP"],
            "answer": "Python"
        },

        {
            "question": "Which database are we using in this project?",
            "options": ["MongoDB", "SQLite", "Oracle", "Firebase"],
            "answer": "SQLite"
        },

        {
            "question": "Which HTML tag creates a hyperlink?",
            "options": ["<p>", "<img>", "<a>", "<div>"],
            "answer": "<a>"
        },

        {
            "question": "Which language is used for styling web pages?",
            "options": ["Python", "CSS", "Java", "C++"],
            "answer": "CSS"
        }

    ]

    # =========================
    # DAILY UNIQUE QUIZ LOGIC
    # =========================
    today = datetime.now().day

    if user.today_quiz_day != today:

        used_quizzes = UsedQuiz.query.filter_by(
            user_id=user.id
        ).all()

        used_indexes = []

        for item in used_quizzes:

            used_indexes.append(item.quiz_index)

        available_indexes = []

        for i in range(len(quiz_questions)):

            if i not in used_indexes:

                available_indexes.append(i)

        # Reset after all quizzes used
        if len(available_indexes) == 0:

            UsedQuiz.query.filter_by(
                user_id=user.id
            ).delete()

            db.session.commit()

            available_indexes = list(range(len(quiz_questions)))

        selected_index = random.choice(available_indexes)

        # Save Today's Quiz
        user.today_quiz_index = selected_index

        user.today_quiz_day = today

        db.session.add(
            UsedQuiz(
                user_id=user.id,
                quiz_index=selected_index
            )
        )

        db.session.commit()

    # Same Quiz Whole Day
    question = quiz_questions[user.today_quiz_index]

    message = ""

    if request.method == 'POST':

        selected = request.form['answer']

        correct_answer = request.form['correct_answer']

        if user.last_quiz_day == today:

            message = "⚠️ You already attempted today's quiz."

        elif selected == correct_answer:

            user.xp += 20

            user.last_quiz_day = today

            db.session.commit()

            message = "✅ Correct! You earned 20 XP."

        else:

            user.last_quiz_day = today

            db.session.commit()

            message = "❌ Wrong Answer."

    return render_template(
        'quiz.html',
        question=question,
        message=message
    )

# =========================
# MAIN
# =========================
if __name__ == '__main__':

    with app.app_context():

        db.create_all()

    app.run(debug=True)