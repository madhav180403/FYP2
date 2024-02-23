from flask import Flask, render_template, request, redirect, url_for, flash,session
from pymongo import MongoClient
from mark_calculation import calc_marks

def total_marks(responses):
    total = 0
    for response in responses:
        total += response['marks']
    return total

with open("key.key","rb") as key_file:
    key = key_file.read()

app = Flask(__name__)
app.secret_key = key

client = MongoClient('mongodb://localhost:27017/')
db = client['automatic_grading']
questions_collection = db['questions']
students_collection = db['student']
teachers_collection = db['teacher']
student_responses_collection = db['student_responses']


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        if role == 'teacher':
            user = teachers_collection.find_one({'username': username, 'password': password})
            if user:
                session['username'] = username  
                return redirect(url_for('teacher_dashboard'))
            else:
                flash('Invalid credentials. Please try again.', 'error')
                return redirect(url_for('login'))
        elif role == 'student':
            user = students_collection.find_one({'username': username, 'password': password})
            if user:
                session['username'] = username  
                return redirect(url_for('student_dashboard'))
            else:
                flash('Invalid credentials. Please try again.', 'error')
                return redirect(url_for('login'))
        else:
            flash('Invalid role. Please select either teacher or student.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        if role == 'teacher':
            teachers_collection.insert_one({'username': username, 'password': password})
        elif role == 'student':
            students_collection.insert_one({'username': username, 'password': password})

        flash('Registration successful. You can now login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/student', methods=['GET', 'POST'])
def student_dashboard():
    if request.method == 'POST':
        username = session.get('username')

        for key in request.form:
            if key.startswith('answer_'):
                question_id = key.replace('answer_', '')
                answer = request.form[key]
                
                marks,similarity,expected_answer = calc_marks(question_id,answer)

                student_responses_collection.insert_one({
                    'username': username,
                    'question_id': question_id,
                    'answer': answer,
                    'marks': marks,
                    'similarity' : similarity,
                    'expected_answer' : expected_answer
                })

        flash('Answers submitted successfully!', 'success')
        return redirect(url_for('student_dashboard'))

    subject = session.get('subject')
    num_questions = session.get('num_questions')

    if subject and num_questions:
        questions = questions_collection.find({'subject': subject}).limit(num_questions)
        return render_template('student.html', questions=questions)

    return render_template('student_init.html')

@app.route('/teacher')
def teacher_dashboard():

    usernames = student_responses_collection.distinct('username')

    student_responses_dict = {}
    for username in usernames:
        responses = list(student_responses_collection.find({'username': username}))  # Convert cursor to list
        student_responses_dict[username] = responses

    questions = questions_collection.find({}, {'_id': 1, 'question': 1})  

    question_text_map = {}
    for question in questions:
        question_text_map[str(question['_id'])] = question['question']

    return render_template('teacher.html', student_responses_dict=student_responses_dict, question_text_map=question_text_map,total_marks=total_marks)

@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    if request.method == 'POST':
        question_text = request.form['question_text']
        questions_collection.insert_one({'question_text': question_text})
        flash('Question added successfully!', 'success')
        return redirect(url_for('add_question'))

    return render_template('add_question.html')

@app.route('/student_init', methods=['POST'])
def student_init():
    subject = request.form['subject']
    num_questions = int(request.form['num_questions'])  

    session['subject'] = subject
    session['num_questions'] = num_questions
    
    return redirect(url_for('student_dashboard'))

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
