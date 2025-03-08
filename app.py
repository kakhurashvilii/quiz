from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
import random
from flask_session import Session
import time
import logging

# Logger-ის კონფიგურაცია
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.debug = True
app.secret_key = '4f4594df564a4e64b96e4fe6609c6c9dhere'
app.config['SESSION_TYPE'] = 'filesystem'  # Use filesystem or any other session backend
Session(app)

# Database connection function
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Function to extract questions from the database
def extract_questions(language='ge'):
    conn = get_db_connection()
    questions = conn.execute('SELECT * FROM questions WHERE language = ?', (language,)).fetchall()
    data = []

    for question in questions:
        options = conn.execute('SELECT * FROM options WHERE question_id = ?', (question['id'],)).fetchall()
        option_list = []
        for option in options:
            option_list.append({
                'number': option['option_number'],
                'text': option['option_text'],
                'is_correct': option['is_correct']
            })
        data.append({
            'question_number': question['question_number'],
            'question': question['question'],
            'options': option_list
        })
    conn.close()
    return data

@app.route('/', methods=['GET'])
def index():
    # Clear the session data for a fresh start
    session.pop('selected_questions', None)
    session.pop('start_time', None)
    
    if not session.get('user_name'):
        return render_template('index.html')
    
    user = session.get('user_name')
    # If name and surname are in session, proceed to quiz
    language = session.get('language', 'ge')  # Default language is Georgian
    questions = extract_questions(language)
    random.shuffle(questions)  # Shuffle questions
    selected_questions = questions[:30]  # Select 30 random questions

    session['selected_questions'] = selected_questions  # Store selected questions in session
    session['start_time'] = time.time()  # Start time for quiz duration
    return render_template('quiz.html', questions=selected_questions, language=language, user=user)

@app.route('/submit_name', methods=['POST'])
def submit_name():
    first_name = request.form['first_name']
    last_name = request.form['last_name']

    # Logging the name provided by the user
    app.logger.debug(f"Received name: {first_name} {last_name}")

    # Save the data to the database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (first_name, last_name) VALUES (?, ?)', (first_name, last_name))
    conn.commit()

    # Get the new user's ID
    user_id = cursor.lastrowid

    # Save the user's ID and name in the session
    session['user_id'] = user_id
    session['user_name'] = f'{first_name} {last_name}'  # Store both names

    conn.close()

    # Logging the user ID stored in the session
    app.logger.debug(f"User ID saved in session: {session['user_id']}")
    app.logger.debug(f"User name saved in session: {session['user_name']}")

    # Redirect to the quiz page
    return redirect(url_for('index'))


@app.route('/change_language/<language>')
def change_language(language):
    session['language'] = language
    return redirect(url_for('index'))

import time

import time
from flask import render_template

@app.route('/result', methods=['POST', 'GET'])
def submit_quiz():
    # Get selected questions from session
    selected_questions = session.get('selected_questions', [])
    score = 0
    results = []

    # Start time for quiz completion
    start_time = session.get('start_time', time.time())

    # Loop through each selected question
    for question in selected_questions:
        question_number = question['question_number']
        options = question['options']

        # Get selected answer from form data
        selected_answer = request.form.get(f'question{question_number}', None)

        if not selected_answer:
            continue  # If no answer was selected, skip to the next question

        # Find the correct answer
        correct_answer = next((option['text'] for option in options if option['is_correct']), None)

        # Check if the selected answer is correct
        is_correct = (selected_answer == correct_answer)
        if is_correct:
            score += 1

        # Add the results of the current question to the results list
        results.append({
            'question': question['question'],
            'selected_answer': selected_answer,
            'correct_answer': correct_answer,
            'is_correct': is_correct
        })

    # Calculate the time taken
    end_time = time.time()
    time_taken = round(end_time - start_time, 2)

    # Ensure time is under 40 minutes
    if time_taken > 2400:
        time_taken = 2400  # Max time allowed 40 minutes

    # Store score, results, and other details in the session
    session['score'] = score
    session['results'] = results
    session['selected_questions'] = selected_questions
    session['time_taken'] = time_taken

    # Store the score and time in the database
    user_id = session.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO rankings (user_id, score, time_taken) VALUES (?, ?, ?)', (user_id, score, time_taken))
    conn.commit()

    # Logging for debugging
    app.logger.debug(f"Quiz completed: User ID {user_id}, Score: {score}, Time Taken: {time_taken} seconds")

    # Redirect to the results page
    return redirect(url_for('result_display'))

@app.route('/result_display')
def result_display():
    # Retrieve data from the session
    score = session.get('score', 0)
    user = session.get('user_name')
    print(user)
    results = session.get('results', [])
    selected_questions = session.get('selected_questions', [])
    rankings = []

    # Get rankings from the database
# Get rankings and join with users table to get first_name and last_name
    conn = get_db_connection()
    rankings = conn.execute('''
        SELECT users.first_name, users.last_name, rankings.score, rankings.time_taken
        FROM rankings
        JOIN users ON rankings.user_id = users.id
        ORDER BY rankings.score DESC, rankings.time_taken ASC
    ''').fetchall()
    conn.close()


    # Pass the score, total number of questions, results, and rankings to the result template
    return render_template('result.html', correct_count=score, total=len(selected_questions), results=results, rankings=rankings, user=user)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
