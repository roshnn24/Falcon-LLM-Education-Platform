import joblib
from flask import Flask, render_template, request, jsonify,session
from werkzeug.utils import secure_filename
import os
from student_functions import extract_text_from_pdf_s,generate_ai_response,generate_project_idea,generate_project_idea_questions,generate_quiz,generate_response_from_pdf,generate_step_by_step_explanation,perform_ocr,study_plan,ConversationBufferMemory,get_first_youtube_video_link,content_translate,summarise_text,content_translate
from teacher_function import evaluate,extract_text_from_image,extract_text_from_pdf,generate_questions_from_text,generate_student_report,generate_timetable_module,cluster_topics,generate_timetable_weak
import shutil
from ai71 import AI71
import re
from flask import Flask, render_template, request, jsonify,session,current_app,send_from_directory

AI71_API_KEY = "api71-api-652e5c6c-8edf-41d0-9c34-28522b07bef9"
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS =  {'pdf', 'jpg', 'jpeg' , 'png'}

app = Flask(__name__)
app.secret_key = 'your_unique_secret_key'  # Add this line

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
memory = ConversationBufferMemory()
database=joblib.load('database.pkl')
teacher_data=database[0]
student_data=database[1]
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/student')
def student():
    student = {
        'name': session.get('student_name'),
        'id': session.get('student_id'),
        'school': session.get('student_school'),
        'dob': session.get('student_dob'),
        'email': session.get('student_email'),
        'subjects_interested': session.get('student_subjects_interested', []),
        'subjects_needing_improvement': session.get('student_subjects_needing_improvement', [])
    }
    return render_template('student.html', student=student)

@app.route('/student_login', methods=['POST'])
def student_login():
    data = request.json
    name = data.get('name')
    password = data.get('password')

    # Verify credentials
    for student in student_data:
        if student['name'] == name and student['password'] == password:
            # Set session data
            session['student_name'] = student['name']
            session['student_id'] = student.get('id', 'N/A')  # If ID is not in data, default to 'N/A'
            session['student_school'] = student['school']
            session['student_dob'] = student['dob']
            session['student_email'] = student['email']
            session['student_subjects_interested'] = student['interests']
            session['student_subjects_needing_improvement'] = [student['areas_to_improve']]
            return jsonify({'success': True})

    return jsonify({'success': False})


@app.route('/teacher_login', methods=['POST'])
def teacher_login():
    data = request.json
    name = data.get('name')
    password = data.get('password')

    # Verify credentials
    for teacher in teacher_data:
        if teacher['name'] == name and teacher['password'] == password:
            # Set session data
            session['teacher_name'] = teacher['name']
            session['teacher_id'] = teacher['teacher_id']
            session['teacher_school'] = teacher['school']
            session['teacher_dob'] = teacher['date_of_birth']
            session['teacher_email'] = teacher['email']
            session['teacher_subjects_taught'] = teacher['subjects_taught']
            session['teacher_classes'] = teacher['classes']
            session['teacher_performance'] = teacher['teaching_performance']
            session['teacher_qualifications'] = teacher['qualifications']
            session['teacher_years_of_experience'] = teacher['years_of_experience']
            session['weekly_class_performance']= teacher['weekly_class_performance']
            return jsonify({'success': True})

    return jsonify({'success': False})

@app.route('/teacher')
def teacher():
    teacher = {
        'name': session.get('teacher_name'),
        'id': session.get('teacher_id'),
        'school': session.get('teacher_school'),
        'dob': session.get('teacher_dob'),
        'email': session.get('teacher_email'),
        'subjects_taught': session.get('teacher_subjects_taught', []),
        'classes': session.get('teacher_classes', []),
        'performance': session.get('teacher_performance', {}),
        'qualifications': session.get('teacher_qualifications', []),
        'years_of_experience': session.get('teacher_years_of_experience', 0),
        'weekly_class_performance': session.get('teacher_weekly_class_performance', {})
    }
    return render_template('teacher.html', teacher=teacher)

@app.route('/student_pdfqa', methods=['GET', 'POST'])
def student_pdfqa():
    if request.method == 'POST':
        file = request.files.get('pdf-file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            pdf_text = extract_text_from_pdf_s(file_path)
            return jsonify({'message': f'PDF uploaded and processed. You can now ask questions.', 'pdf_text': pdf_text})
        else:
            return jsonify({'message': 'Invalid file type. Please upload a PDF.'}), 400

    return render_template('student_pdfqa.html')

@app.route('/ask_pdf_question', methods=['POST'])
def ask_pdf_question():
    data = request.json
    query = data['query']
    pdf_text = data['pdf_text']

    response = generate_response_from_pdf(query, pdf_text)[:-6]
    return jsonify({'response': response})

@app.route('/student_aitutor')
def student_aitutor():
    return render_template('student_aitutor.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    query = data['message']
    response = generate_ai_response(query)
    return jsonify({'response': response})

@app.route('/upload_image_for_ocr', methods=['POST'])
def upload_image_for_ocr():
    if 'image-file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['image-file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        extracted_text = perform_ocr(file_path)
        ai_response = generate_ai_response(extracted_text)

        return jsonify({'ai_response': ai_response})
    return jsonify({'error': 'Invalid file type'}), 400


@app.route('/student_projectideas')
def student_projectideas():
    return render_template('student_projectideas.html')

@app.route('/student_quiz')
def student_quiz():
    return render_template('student_quiz.html')

@app.route('/update_student_areas', methods=['POST'])
def update_student_areas():
    data = request.json
    student_id = data.get('student_id')
    areas_to_improve = data.get('areas_to_improve')

    # Find the student in the database
    student = next((s for s in student_data if s['email'] == student_id), None)

    if student:
        # Update the student's areas to improve
        student['areas_to_improve'] = areas_to_improve
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Student not found'}), 404
@app.route('/get_student_profile', methods=['GET'])
def get_student_profile():
    # For demonstration, assume `student_id` is passed in query parameters
    student_id = request.args.get('student_id')
    student = next((s for s in student_data if s['email'] == student_id), None)

    if student:
        return jsonify({
            'status': 'success',
            'areas_to_improve': student.get('areas_to_improve', [])
        })
    else:
        return jsonify({'status': 'error', 'message': 'Student not found'}), 404


def calculate_score_and_grade(llm_response):
    total_score=llm_response.split('\n')[1].split(' ')[-1]
    max_possible_score=llm_response.split('\n')[0].split(' ')[-1]

    total_score = int(total_score)
    max_possible_score = int(max_possible_score)

    percentage = (max_possible_score/total_score) * 100 if max_possible_score > 0 else 0

    if percentage > 90:
        grade = 'O-grade'
    elif 80 <= percentage <= 90:
        grade = 'A-grade'
    elif 70 <= percentage < 80:
        grade = 'B-grade'
    elif 60 <= percentage < 70:
        grade = 'C-grade'
    elif 50 <= percentage < 60:
        grade = 'D-grade'
    else:
        grade = 'Fail'

    return total_score, max_possible_score, percentage, grade

@app.route('/student_reward_points')
def student_reward_points():
    return render_template('student_reward_points.html')

@app.route('/generate_quiz', methods=['POST'])
def generate_quiz_route():
    data = request.json
    subject = data['subject']
    topic = data['topic']
    count = int(data['num-questions'])
    difficulty = data['difficulty']

    quiz = generate_quiz(subject, topic, count, difficulty)
    return jsonify({'quiz': quiz})

@app.route('/generate_project_idea', methods=['POST'])
def generate_project_idea_route():
    data = request.json
    subject = data['subject']
    topic = data['topic']
    plan = data['plan']

    project_idea = generate_project_idea(subject, topic, plan)
    return jsonify({'project_idea': project_idea})

@app.route('/homework')
def homework():
    return render_template('homework.html')

@app.route('/student_courses')
def student_courses():
    return render_template('student_courses.html')

@app.route('/search_youtube', methods=['POST'])
def search_youtube():
    data = request.json
    query = data['query']

    try:
        video_link, video_title = get_first_youtube_video_link(query)
        video_id = video_link.split('v=')[1]
        return jsonify({
            'videoId': video_id,
            'videoTitle': video_title
        })
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/ask_followup', methods=['POST'])
def ask_followup_route():
    data = request.json
    project_idea = data['project_idea']
    query = data['query']

    response = generate_project_idea_questions(project_idea, query)
    return jsonify({'response': response})

@app.route('/student_studyplans')
def student_studyplans():
    return render_template('student_studyplans.html')

@app.route('/generate_study_plan', methods=['POST'])
def generate_study_plan_route():
    data = request.json
    subjects = data['subjects']
    hours = data['hours']
    area_lag = data['areaLag']  # Ensure the key matches
    goal = data['goal']
    learning_style = data['learningStyle']

    study_plan_text = study_plan(subjects, hours, area_lag, goal)
    return jsonify({'study_plan': study_plan_text})


@app.route('/student_stepexplanation')
def student_stepexplanation():
    return render_template('student_stepexplanation.html')


@app.route('/evaluate-answers', methods=['POST'])
def evaluate_answers():
    data = request.json
    questions = data['questions']
    answers = data['answers']
    max_marks = 5  # As per your requirement

    evaluations = []
    for question, answer in zip(questions, answers):
        if answer.strip() == "":
            evaluation = "Description: No answer provided.\nAssigned marks: 0\nTotal marks: 5"
        else:
            evaluation = evaluate(question, answer, max_marks)
        evaluations.append(evaluation)

    return jsonify({"evaluations": evaluations})

@app.route('/translate', methods=['POST'])
def translate():
    data = request.json
    text = data.get('text', '')
    # Mock translation function
    translated_text = content_translate(text)
    return jsonify({"translated_text": translated_text})

@app.route('/generate_step_by_step_explanation', methods=['POST'])
def generate_step_by_step_explanation_route():
    data = request.get_json()
    question = data['question']
    answer = generate_step_by_step_explanation(question)
    return jsonify({'answer': answer})

@app.route('/speak')
def speak():
    return render_template('student_speakai.html')

@app.route('/generate_ai_timetable', methods=['POST'])
def generate_ai_timetable():
    academic_topics = request.form['academic_topics'].split(',')
    hours_per_day = request.form['hours_per_day']

    clustered_topics = cluster_topics(academic_topics)
    special_timetable = generate_timetable_weak(clustered_topics, hours_per_day)

    return jsonify({
        'clustered_topics': clustered_topics,
        'special_timetable': special_timetable
    })


@app.route('/ai_timetable')
def ai_timetable():
    return render_template('ai_timetable.html')

@app.route('/summarise_video')
def summarise_video():
    return render_template('student_summarise_video.html')

@app.route('/summarize_video', methods=['POST'])
def summarize_video_route():
    data = request.json
    url = data.get('url')
    if url:
        try:
            summary = summarise_text(url)
            return jsonify({'summary': summary})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'No URL provided'}), 400


@app.route('/generate-questions-hw', methods=['GET'])
def generate_questions():
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": (
            "Generate 5 questions for a Math Assignment on 'trigonometry Basics'. "
            "Include a mix of both theoretical and numerical questions."
        )}
    ]

    questions = []
    for chunk in AI71(AI71_API_KEY).chat.completions.create(
            model="tiiuae/falcon-180b-chat",
            messages=messages,
            stream=True,
    ):
        if chunk.choices[0].delta.content:
            questions.append(chunk.choices[0].delta.content)

    # Join all chunks to create the complete list of questions
    complete_questions = ''.join(questions).split('\n')

    return jsonify({'questions': complete_questions})

@app.route('/assign_grade', methods=['POST'])
def assign_grade():
    data = request.json
    result = data['result']
    total_score, max_possible_score, percentage, grade = calculate_score_and_grade(result)
    return jsonify({
        'total_score': total_score,
        'max_possible_score': max_possible_score,
        'percentage': percentage,
        'grade': grade
    })

@app.route('/generate_timetable', methods=['POST'])
def generate_timetable():
    data = request.json
    hours_per_day = data.get('hours_per_day')
    days_per_week = data.get('days_per_week')
    semester_end_date = data.get('semester_end_date')
    subjects = data.get('subjects', [])

    # Input validation
    if not hours_per_day or not days_per_week or not semester_end_date or not subjects:
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        # Assuming generate_timetable_module is a function you've defined elsewhere
        timetable = generate_timetable_module(data, hours_per_day, days_per_week, semester_end_date, subjects)
        return jsonify({"timetable": timetable})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/generate-paper', methods=['GET', 'POST'])
def generate_paper():
    if request.method == 'POST':
        no_of_questions = int(request.form['no_of_questions'])
        total_marks = int(request.form['total_marks'])
        no_of_parts = int(request.form['no_of_parts'])
        marks_per_part = int(request.form['marks_per_part'])
        test_duration = request.form['test_duration']
        pdf_file = request.files['pdf_file']

        if pdf_file:
            # Secure the file name and save the file to the upload folder
            filename = secure_filename(pdf_file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            pdf_file.save(file_path)

            # Extract text from the curriculum PDF
            curriculum_text = extract_text_from_pdf(file_path)

            # Generate questions
            questions = generate_questions_from_text(curriculum_text, no_of_questions, marks_per_part, no_of_parts)

            # Optionally, remove the saved file after use

            return render_template('teacher_paper_gen.html', questions=questions)

    return render_template('teacher_paper_gen.html')


@app.route('/eval', methods=['GET', 'POST'])
def eval():
    if request.method == 'POST':
        input_type = request.form['input_type']
        question_text = ""
        answer_text = ""
        max_marks = request.form['max_marks']

        if input_type == 'file':
            question_file = request.files['question_file']
            answer_file = request.files['answer_file']

            if question_file and answer_file:
                question_path = os.path.join(app.config['UPLOAD_FOLDER'], question_file.filename)
                answer_path = os.path.join(app.config['UPLOAD_FOLDER'], answer_file.filename)

                question_file.save(question_path)
                answer_file.save(answer_path)

                if question_path.endswith('.pdf'):
                    question_text = extract_text_from_pdf(question_path)
                else:
                    question_text = extract_text_from_image(question_path)

                if answer_path.endswith('.pdf'):
                    answer_text = extract_text_from_pdf(answer_path)
                else:
                    answer_text = extract_text_from_image(answer_path)

        elif input_type == 'text':
            question_text = request.form['question_text']
            answer_text = request.form['answer_text']

        evaluation_result = evaluate(question_text, answer_text, max_marks)
        print(f"Question Text: {question_text}")  # Debugging line
        print(f"Answer Text: {answer_text}")  # Debugging line
        print(f"Evaluation Result: {evaluation_result}")  # Debugging line

        return render_template('teacher_result.html', result=evaluation_result)

    return render_template('teacher_eval.html')

@app.route('/get_students')
def get_students():

    return jsonify(student_data)


@app.route('/get_audio_files', methods=['GET'])
def get_audio_files():
    audio_folder = os.path.join(app.root_path, 'speech')
    audio_files = [{'name': file, 'url': f'/speech/{file}'} for file in os.listdir(audio_folder) if
                   file.endswith('.mp3')]

    current_app.logger.info(f"Found audio files: {audio_files}")

    return jsonify({'audio_files': audio_files})


@app.route('/speech/<path:filename>')
def serve_audio(filename):
    return send_from_directory(os.path.join(app.root_path, 'speech'), filename)



@app.route('/generate_report', methods=['POST'])
def generate_report():
    student_data = request.json
    report = generate_student_report(
        student_data['name'],
        student_data['age'],
        student_data['cgpa'],
        student_data['course_pursuing'],
        student_data['assigned_test_score'],
        student_data['ai_test_score'],
        student_data['interests'],
        student_data['areas_to_improve'],
        student_data['courses_taken']
    )
    return jsonify({'report': report})




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860, debug=True)

