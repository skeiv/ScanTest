import json

from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify
from pdf_generator import generate_pdf
from image_scaner import testRecognize
import sqlite3

app = Flask(__name__)


def create_tables():
    conn = sqlite3.connect('test_data.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Tests (
            id INTEGER PRIMARY KEY,
            test_name TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Questions (
            id INTEGER PRIMARY KEY,
            test_id INTEGER,
            question_text TEXT,
            FOREIGN KEY (test_id) REFERENCES Tests(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Answers (
            id INTEGER PRIMARY KEY,
            question_id INTEGER,
            answer_text TEXT,
            is_correct BOOLEAN,
            FOREIGN KEY (question_id) REFERENCES Questions(id)
        )
    ''')

    conn.commit()
    conn.close()


@app.route('/', methods=['GET', 'POST'])
def index(success=''):
    tests = get_tests()
    if request.method == 'POST':
        num_questions = int(request.form['num_questions'])
        return render_template('matrix.html', num_questions=num_questions, success=success, tests=tests)
    return render_template('index.html', success=success, tests=tests)


@app.route('/generate_pdf', methods=['POST'])
def generate_pdf_route():
    conn = sqlite3.connect('test_data.db')
    cursor = conn.cursor()

    test_id = request.form.get('test_id')
    students_num = int(request.form.get('students_num'))
    query_questions = '''
        SELECT question_text
        FROM Questions
        WHERE test_id = ?
    '''
    cursor.execute(query_questions, test_id)
    questions_data = cursor.fetchall()

    questions = [q[0] for q in questions_data]

    query_answers = '''
        SELECT Questions.id, answer_text
        FROM Answers
        INNER JOIN Questions ON Answers.question_id = Questions.id
        WHERE Questions.test_id = ?
    '''
    cursor.execute(query_answers, test_id)
    answers_data = cursor.fetchall()

    answers = []
    question_ids = {}

    new_question_id = 0  # Начальное значение нового идентификатора вопроса

    for question_id, answer_text in answers_data:
        if question_id not in question_ids:
            question_ids[question_id] = new_question_id
            new_question_id += 1

        new_question_id_mapped = question_ids[question_id]
        answers.append((new_question_id_mapped, answer_text))

    query_test_name = '''
        SELECT test_name
        FROM Tests
        WHERE Tests.id = ?
    '''
    cursor.execute(query_test_name, test_id)
    test_name = cursor.fetchone()
    if test_name:
        test_name = test_name[0]
    else:
        test_name = "Тест"

    conn.commit()
    conn.close()

    if questions_data and answers_data:

        pdf_buffer = generate_pdf(students_num, test_name, questions, answers)

        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=test.pdf'
        return response

    return jsonify({'message': 'Failed to generate PDF or test not found'}), 404


@app.route('/save_test', methods=['POST'])
def save_test():
    conn = sqlite3.connect('test_data.db')
    cursor = conn.cursor()

    test_name = request.form['test_name']
    num_questions = int(request.form['num_questions'])

    cursor.execute('INSERT INTO Tests (test_name) VALUES (?)', (test_name.encode('utf-8').decode('utf-8'),))
    test_id = cursor.lastrowid

    for i in range(num_questions):
        question = request.form[f'question{i+1}']
        correct_answer = int(request.form[f'correct_answer{i+1}'])

        cursor.execute('INSERT INTO Questions (test_id, question_text) VALUES (?, ?)',
                       (test_id, question.encode('utf-8').decode('utf-8')))
        question_id = cursor.lastrowid

        answers = request.form.getlist(f'answers{i+1}[]')
        for j, answer in enumerate(answers):
            is_correct = j + 1 == correct_answer
            cursor.execute('INSERT INTO Answers (question_id, answer_text, is_correct) VALUES (?, ?, ?)',
                           (question_id, answer.encode('utf-8').decode('utf-8'), is_correct))

    conn.commit()
    conn.close()
    return redirect(url_for('index', success='Данные успешно обновлены'))


@app.route('/delete_test', methods=['GET'])
def delete_test():
    test_id = request.args.get('test_id')
    conn = sqlite3.connect('test_data.db')
    cursor = conn.cursor()

    cursor.execute('DELETE FROM Answers WHERE question_id IN (SELECT id FROM Questions WHERE test_id = ?);', test_id);
    cursor.execute('DELETE FROM Questions WHERE test_id = ?;', test_id)
    cursor.execute('DELETE FROM Tests WHERE id = ?;', test_id)

    conn.commit()
    conn.close()
    return redirect(url_for('index'))


@app.route('/get_tests', methods=['GET'])
def get_tests():
    conn = sqlite3.connect('test_data.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM Tests')
    tests = cursor.fetchall()

    return tests


@app.route('/recognize', methods=['POST'])
def recognizeImages():
    conn = sqlite3.connect('test_data.db')
    cursor = conn.cursor()

    test_id = request.form.get('test_id')

    # SQL-запрос для получения правильных ответов для определенного теста
    sql_query = f'''
        SELECT Q.id, A.id, A.is_correct
        FROM Answers AS A
        JOIN Questions AS Q ON Q.id = A.question_id
        JOIN Tests AS T ON T.id = Q.test_id
        WHERE T.id = {test_id}
    '''

    cursor.execute(sql_query)
    results = cursor.fetchall()

    correct_answers = []
    start_question_id = 1
    answer_id = 1

    for row in results:
        question_id = row[0]
        answer_is_correct = row[2]
        if question_id <= start_question_id:
            if answer_is_correct == 0:
                answer_id += 1
            else:
                correct_answers.append(answer_id)
                answer_id += 1
        else:
            start_question_id += 1
            answer_id = 1
            if answer_is_correct == 0:
                answer_id += 1
            else:
                correct_answers.append(answer_id)
                answer_id += 1

    uploaded_files = request.files.getlist("images")
    files = []
    for file in uploaded_files:
        # Чтение изображения с использованием OpenCV
        img_stream = file.read()
        files.append(img_stream)

    if files.count == 0:
        pass

    student_points, student_incorrect_answers = testRecognize(files, correct_answers)
    return report(student_points=student_points, student_incorrect_answers=student_incorrect_answers)


@app.route('/report', methods=['POST'])
def report(student_points, student_incorrect_answers):
    return render_template('report.html', points=student_points, incorrect_answers=student_incorrect_answers)


if __name__ == '__main__':
    create_tables()
    app.run(debug=False)
