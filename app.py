from flask import Flask, render_template, request
import json
import random
from flask import session
import os
from flask_session import Session


app = Flask(__name__)
app.debug = True

app.secret_key = '4f4594df564a4e64b96e4fe6609c6c9dhere'
app.config['SESSION_TYPE'] = 'filesystem'  # ან გამოიყენეთ Redis, MongoDB და სხვ.
Session(app)
def extract_questions(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


@app.route('/')
def index():
    questions = extract_questions("processed_text.json")
    random.shuffle(questions)  # შემთხვევითი კითხვის შერჩევა
    selected_questions = questions[:30]  # 30 შემთხვევითი კითხვა
    session['selected_questions'] = selected_questions  # შეინახეთ კითხვები session-ში
    return render_template('quiz.html', questions=selected_questions)

@app.route('/result', methods=['POST'])
def submit_quiz():
    # selected_questions უნდა იყოს ის 30 კითხვა, რომელიც მომხმარებელს მიაწვდეთ
    selected_questions = session.get('selected_questions', [])

    score = 0
    results = []

    for question in selected_questions:
        question_number = question['question_number']
        options = question['options']

        # მომხმარებლის მიერ არჩეული პასუხი
        selected_answer = request.form.get(f'question{question_number}', 'None')

        # სწორი პასუხის მოძიება
        correct_answer = next((option['text'] for option in options if option['is_correct']), None)

        # შეფასება
        if selected_answer == correct_answer:
            score += 1
            is_correct = True
        else:
            is_correct = False

        results.append((question['question'], selected_answer, correct_answer, is_correct))

    return render_template('result.html', correct_count=score, total=len(selected_questions), results=results)

if __name__ == '__main__':
    app.run(debug=True)
