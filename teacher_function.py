from ai71 import AI71
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import cv2
import numpy as np
import pytesseract
AI71_API_KEY = "api71-api-20725a9d-46d6-4baf-9e26-abfca35ab242"

def extract_text_from_pdf(pdf_file):
    text = ""
    reader = PdfReader(pdf_file)
    for page in reader.pages:
        text += page.extract_text()
    return text

def generate_questions_from_text(text, no_of_questions, marks_per_part, no_parts):
    ai71 = AI71(AI71_API_KEY)
    messages = [
        {"role": "system", "content": "You are a teaching assistant"},
        {"role": "user",
         "content": f"Give your own {no_of_questions} questions under each part for {no_parts} parts with {marks_per_part} marks for each part. Note that all questions must be from the topics of {text}"}
    ]

    questions = []
    for chunk in ai71.chat.completions.create(
            model="tiiuae/falcon-180b-chat",
            messages=messages,
            stream=True,
    ):
        if chunk.choices[0].delta.content:
            questions.append(chunk.choices[0].delta.content)

    return "".join(questions)

def extract_text_from_image(image_path):
    img = cv2.imread(image_path)
    text = pytesseract.image_to_string(img)
    return text


def extract_text_from_pdf(pdf_path):
    images = convert_from_path(pdf_path)
    final_text = ""
    for image in images:
        image_cv = np.array(image)
        image_cv = cv2.cvtColor(image_cv, cv2.COLOR_RGB2BGR)
        text = pytesseract.image_to_string(image_cv)
        final_text += text
    return final_text


def evaluate(question, answer, max_marks):
    prompt = f"""Questions: {question}
    Answer: {answer}.


    Evaluate above questions one by one(if there are multiple) by provided answers and assign marks out of {max_marks}. No need overall score. Note that as maximum mark increases, the size of the answer must be large enough to get good marks. Give ouput in format below:
description: 
assigned marks: 
total marks: 
Note that you should not display total marks"""

    messages = [
        {"role": "system", "content": "You are an answer evaluator"},
        {"role": "user", "content": prompt}
    ]

    response_content = ""
    for chunk in  AI71(AI71_API_KEY).chat.completions.create(
            model="tiiuae/falcon-180b-chat",
            messages=messages,
            stream=True
    ):
        if chunk.choices[0].delta.content:
            response_content += chunk.choices[0].delta.content

    return response_content

def generate_student_report(name, age, cgpa, course, assigned_test, ai_test, interests, difficulty, courses_taken):
    prompt = f"""
    Name: {name}
    Age: {age}
    CGPA: {cgpa}
    Course: {course}
    Assigned Test Score: {assigned_test}
    AI generated Test Score: {ai_test}
    Interests: {interests}
    Difficulty in: {difficulty}
    Courses Taken: {courses_taken}
    Use the above student data to generate a neat personalized report and suggested teaching methods."""

    client = AI71(AI71_API_KEY)

    response = client.chat.completions.create(
        model="tiiuae/falcon-180B-chat",
        messages=[
            {"role": "system", "content": "You are a student report generator."},
            {"role": "user", "content": prompt}
        ]
    )

    report = response.choices[0].message.content if response.choices and response.choices[
        0].message else "No report generated."
    print(report)

    return report.replace('\n','<br>')
def generate_timetable_module(data,hours_per_day,days_per_week,semester_end_date,subjects):
    response = AI71(AI71_API_KEY).chat.completions.create(
            model="tiiuae/falcon-180B-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Create a timetable starting from Monday based on the following inputs:\n"
                                            f"- Number of hours per day: {hours_per_day}\n"
                                            f"- Number of days per week: {days_per_week}\n"
                                            f"- Semester end date: {semester_end_date}\n"
                                            f"- Subjects: {', '.join(subjects)}\n"}
            ]
        )

        # Access the response content correctly
    return( response.choices[0].message.content if response.choices and response.choices[0].message else "No timetable generated.")

def cluster_topics(academic_topics):
    prompt = (
            "Please cluster the following academic topics into their respective subjects such as Mathematics, Physics, etc.: "
            + ", ".join(academic_topics))
    response = ""
    for chunk in AI71(AI71_API_KEY).chat.completions.create(
            model="tiiuae/falcon-180b-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            stream=True,
    ):
        if chunk.choices[0].delta.content:
            response += chunk.choices[0].delta.content
    return response

def generate_timetable_weak(clustered_subjects, hours_per_day):
    prompt = (
        f"Using the following subjects and topics:\n{clustered_subjects}\n"
        f"Generate a special class timetable for {hours_per_day} hours per day.\n"
        f"Also provide reference books and methods to teach the slow learners for each subject"
    )
    response = ""
    for chunk in AI71(AI71_API_KEY).chat.completions.create(
            model="tiiuae/falcon-180b-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            stream=True,
    ):
        if chunk.choices[0].delta.content:
            response += chunk.choices[0].delta.content
    return response

