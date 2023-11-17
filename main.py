from flask import Flask, render_template, request, make_response
from pdf_generator import generate_pdf

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        num_questions = int(request.form['num_questions'])
        return render_template('matrix.html', num_questions=num_questions)
    return render_template('index.html')


@app.route('/generate_pdf', methods=['POST'])
def generate_pdf_route():
    questions = [request.form[f'question{i+1}'] for i in range(int(request.form['num_questions']))]
    answers = [request.form.getlist(f'answers{i+1}[]') for i in range(int(request.form['num_questions']))]

    pdf_buffer = generate_pdf(questions, answers)

    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=questions_and_answers.pdf'
    return response


if __name__ == '__main__':
    app.run(debug=False)
