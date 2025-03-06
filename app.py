from flask import Flask, render_template, request, session
import json
import random
from flask_session import Session

app = Flask(__name__)
app.debug = True

app.secret_key = '4f4594df564a4e64b96e4fe6609c6c9dhere'
app.config['SESSION_TYPE'] = 'filesystem'  # Use filesystem or any other session backend
Session(app)

# Function to extract questions from a JSON file
def extract_questions(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

@app.route('/')
def index():
    # Check if the user selected a language, default to georgian
    language = session.get('language', 'ka')  # Default language is georgian
    file_path = "processed_text.json" if language == 'ka' else "processed_textru.json"
    
    questions = extract_questions(file_path)
    random.shuffle(questions)  # Shuffle questions
    selected_questions = questions[:30]  # Select 30 random questions
    
    session['selected_questions'] = selected_questions  # Store selected questions in session
    return render_template('quiz.html', questions=selected_questions, language=language)

@app.route('/change_language/<language>')
def change_language(language):
    # Store language selection in session
    session['language'] = language
    return index()  # Redirect to index to reload questions in selected language

@app.route('/result', methods=['POST'])
def submit_quiz():
    selected_questions = session.get('selected_questions', [])
    score = 0
    results = []

    for question in selected_questions:
        question_number = question['question_number']
        options = question['options']

        # Get selected answer from form data
        selected_answer = request.form.get(f'question{question_number}', 'None')

        # Find the correct answer
        correct_answer = next((option['text'] for option in options if option['is_correct']), None)

        # Check if the selected answer is correct
        if selected_answer == correct_answer:
            score += 1
            is_correct = True
        else:
            is_correct = False

        results.append((question['question'], selected_answer, correct_answer, is_correct))

    return render_template('result.html', correct_count=score, total=len(selected_questions), results=results)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
