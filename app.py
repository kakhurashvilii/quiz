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

@app.route('/result', methods=['POST', 'GET'])
def submit_quiz():
    # Get selected questions from session
    selected_questions = session.get('selected_questions', [])
    score = 0
    results = []

    # Debugging: Print request form to check if data is sent correctly
    print(request.form)

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

    # Pass the score, total number of questions, and results to the result template
    return render_template('result.html', correct_count=score, total=len(selected_questions), results=results)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
