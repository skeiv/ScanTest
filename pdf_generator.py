from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO


def generate_pdf(questions, answers):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle("Тест")

    arial_path = 'fonts/arial.ttf'

    pdfmetrics.registerFont(TTFont('Arial', arial_path))
    pdf.setFont('Arial', 16)
    pdf.drawString(100, 750, "Тест")

    def split_text(text, max_width):
        words = text.split()
        lines = []
        current_line = words[0]

        for word in words[1:]:
            if pdf.stringWidth(current_line + ' ' + word, "Arial", 10) < max_width:
                current_line += ' ' + word
            else:
                lines.append(current_line)
                current_line = word

        lines.append(current_line)
        return lines

    y_position = 730
    max_y = 100  # Предел для координаты y, когда нужно переходить на новую страницу

    for i, question in enumerate(questions):
        y_position -= 15
        pdf.setFont("Arial", 10)
        pdf.drawString(100, y_position, f"Вопрос {i + 1}:")
        y_position -= 15

        lines = split_text(question, 400)  # 400 - предполагаемая ширина блока для текста вопроса

        for line in lines:
            if y_position < max_y:
                pdf.showPage()
                pdf.setFont('Arial', 10)
                y_position = 730

            pdf.drawString(120, y_position, line)
            y_position -= 15

        pdf.setFont("Arial", 10)
        pdf.drawString(100, y_position, "Ответы:")

        answers_for_question = answers[i]
        for j, answer in enumerate(answers_for_question):
            lines = split_text(f"{j + 1}: {answer}", 400)  # 400 - предполагаемая ширина блока для текста ответа

            for line in lines:
                y_position -= 15
                if y_position < max_y:
                    pdf.showPage()
                    pdf.setFont("Arial", 10)
                    y_position = 730

                pdf.drawString(140, y_position, line)

    pdf.showPage()

    pdf.setFont("Arial", 12)
    pdf.drawString(100, 750, "Бланк ответов")

    y_position = 700
    for i, question in enumerate(questions):
        y_position -= 30
        pdf.setFont("Arial", 10)
        pdf.drawString(100, y_position, f"{i + 1}:")
        for j, answer in enumerate(answers[i]):
            pdf.circle(130 + j * 20, y_position + 5, 5)

    pdf.save()
    buffer.seek(0)
    return buffer

