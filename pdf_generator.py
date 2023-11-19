from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO


def generate_pdf(students_num, test_name, questions, answers):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

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

    for student in range(students_num):
        pdf.setTitle("Тест")

        arial_path = 'fonts/arial.ttf'

        pdfmetrics.registerFont(TTFont('Arial', arial_path))
        pdf.setFont('Arial', 16)
        pdf.drawString(100, 720, test_name)

        y_position = 700
        max_y = 90  # Предел для координаты y, когда нужно переходить на новую страницу

        for i, question in enumerate(questions):
            if y_position < max_y:
                pdf.showPage()
                y_position = 730
            else:
                y_position -= 15

            pdf.setFont("Arial", 10)
            pdf.drawString(100, y_position, f"Вопрос {i + 1}:")
            y_position -= 15

            lines = split_text(question, 400)  # 400 - предполагаемая ширина блока для текста вопроса

            for line in lines:
                if y_position < max_y:
                    pdf.showPage()
                    pdf.setFont('Arial', 10)
                    y_position = 700

                pdf.drawString(120, y_position, line)
                y_position -= 15

            if y_position < max_y:
                pdf.showPage()
                y_position = 730

            pdf.setFont("Arial", 10)
            pdf.drawString(100, y_position, "Ответы:")

            answers_for_question = [answer for number, answer in answers if number == i]
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
        pdf.drawString(100, 720, "Бланк ответов")
        page = 0

        y_position = 700
        for i, question in enumerate(questions):
            y_position -= 30
            if y_position < max_y:
                page += 1
                pdf.setFont("Arial", 15)
                pdf.drawString(500, 700, f"{student + 1}")
                pdf.setFont("Arial", 15)
                pdf.drawString(500, 100, f"{page}")
                pdf.showPage()
                y_position = 720
                pdf.setFont("Arial", 12)
                pdf.drawString(100, 720, "Бланк ответов")
                y_position -= 30
            pdf.setFont("Arial", 10)
            pdf.drawString(100, y_position, f"{i + 1}:")
            answers_for_question = [answer for number, answer in answers if number == i]
            for j, answer in enumerate(answers_for_question):
                pdf.circle(130 + j * 25, y_position + 5, 5)

        pdf.setFont("Arial", 15)
        pdf.drawString(500, 700, f"{student + 1}")
        pdf.setFont("Arial", 15)
        pdf.drawString(500, 100, f"{page + 1}")

        pdf.showPage()

    pdf.save()
    buffer.seek(0)
    return buffer

