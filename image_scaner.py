import io

import cv2
import numpy as np
import re
import pytesseract


def testRecognize(images, answers):
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Укажите свой путь
    student_points = {}
    student_incorrect_answers = {}
    pattern = r'\d+\n'

    for img in images:
        image = cv2.imdecode(np.frombuffer(img, np.uint8), cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        improved_contrast = clahe.apply(gray)

        sobel_x = cv2.Sobel(improved_contrast, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(improved_contrast, cv2.CV_64F, 0, 1, ksize=3)
        sobel_combined = cv2.magnitude(sobel_x, sobel_y)
        _, thresh = cv2.threshold(sobel_combined, 255, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        height = image.shape[0]
        width = image.shape[1]

        lines = []
        page = 0
        student = 0

        circles = []
        empty_circles = []

        incorrect_answers = []
        points = 0

        min_contour_area = 50

        filtered_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_contour_area:
                filtered_contours.append(contour)

        for contour in filtered_contours:
            x, y, w, h = cv2.boundingRect(contour)

            roi = image[y:y + h + 5, x:x + w + 5]
            gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789O'
            detected_text = pytesseract.image_to_string(gray_roi, config=custom_config)
            if detected_text == 'O\n':
                empty_circles.append((x, y))
            if re.search(pattern, detected_text):
                if (y < height / 3 * 2) and (x > width / 3 * 2):
                    student = int(detected_text)
                elif (y > height / 2) and (x > width / 2):
                    page = int(detected_text)

            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                perimeter = 10000000
            circularity = 4 * np.pi * (area / (perimeter * perimeter))
            if circularity > 0.6:
                x, y, w, h = cv2.boundingRect(contour)
                if w > 5:
                    circles.append((x, y))

        circles.sort(key=lambda p: p[1])
        current_line = []

        for circle in circles:
            if not current_line:
                current_line.append(circle)
            elif circle[1] - current_line[-1][1] < 20:
                current_line.append(circle)
            else:
                current_line.sort(key=lambda p: p[0])
                lines.append(current_line)
                current_line = [circle]

        if current_line:
            current_line.sort(key=lambda p: p[0])
            lines.append(current_line)

        for i, line in enumerate(lines):
            for j, element in enumerate(line):
                if not empty_circles.__contains__(element):
                    if answers[i] != j + 1:
                        #incorrect_answers.append(i + 1 + ((page - 1) * 20))# 20 - количество вопросов на странице
                        #TODO: Найти причину
                        incorrect_answers.append(i + 1)
                    else:
                        points += 1

        if student in student_points:
            student_points[student] += points
            student_incorrect_answers[student].append(incorrect_answers)
        else:
            student_points[student] = points
            student_incorrect_answers[student] = incorrect_answers

    return student_points, student_incorrect_answers






