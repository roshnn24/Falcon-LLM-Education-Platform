from gtts import gTTS
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import easyocr
import json
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import JSONFormatter
from urllib.parse import urlparse, parse_qs
from pypdf import PdfReader
from ai71 import AI71
import os

AI71_API_KEY = "api71-api-df260d58-62e0-46c9-b549-62daa9c409be"


def extract_text_from_pdf_s(pdf_path):
    text = ""
    reader = PdfReader(pdf_path)
    for page in reader.pages:
        text += page.extract_text() + "\n"
    generate_speech_from_pdf(text[:len(text) // 2])
    return text


def generate_response_from_pdf(query, pdf_text):
    response = ''
    for chunk in AI71(AI71_API_KEY).chat.completions.create(
            model="tiiuae/falcon-180b-chat",
            messages=[
                {"role": "system", "content": "You are a pdf questioning assistant."},
                {"role": "user",
                 "content": f'''Answer the querry based on the given content.Content:{pdf_text},query:{query}'''},
            ],
            stream=True,
    ):
        if chunk.choices[0].delta.content:
            response += chunk.choices[0].delta.content
    return response[:-6].replace("###", '')


def generate_quiz(subject, topic, count, difficult):
    quiz_output = ""

    for chunk in AI71(AI71_API_KEY).chat.completions.create(
            model="tiiuae/falcon-180b-chat",
            messages=[
                {"role": "system", "content": "You are a teaching assistant."},
                {"role": "user",
                 "content": f'''Generate {count} multiple-choice questions in the subject of {subject} for the topic {topic} for students at a {difficult} level. Ensure the questions are well-diversified and cover various aspects of the topic. Format the questions as follows:
Question: [Question text] [specific concept in a question] 
<<o>> [Option1] 
<<o>> [Option2] 
<<o>> [Option3] 
<<o>> [Option4], 
Answer: [Option number]'''},
            ],
            stream=True,
    ):
        if chunk.choices[0].delta.content:
            quiz_output += chunk.choices[0].delta.content
    print("Quiz generated")
    return quiz_output


def perform_ocr(image_path):
    reader = easyocr.Reader(['en'])
    try:
        result = reader.readtext(image_path)
        extracted_text = ''
        for (bbox, text, prob) in result:
            extracted_text += text + ' '
        return extracted_text.strip()
    except Exception as e:
        print(f"Error during OCR: {e}")
        return ''


def generate_ai_response(query):
    ai_response = ''
    for chunk in AI71(AI71_API_KEY).chat.completions.create(
            model="tiiuae/falcon-180b-chat",
            messages=[
                {"role": "system", "content": "You are a teaching assistant."},
                {"role": "user", "content": f'Assist the user clearly for his questions: {query}.'},
            ],
            stream=True,
    ):
        if chunk.choices[0].delta.content:
            ai_response += chunk.choices[0].delta.content
    return ai_response.replace('###', '')[:-6]


def generate_project_idea(subject, topic, overview):
    string = ''
    for chunk in AI71(AI71_API_KEY).chat.completions.create(
            model="tiiuae/falcon-180b-chat",
            messages=[
                {"role": "system", "content": "You are a project building assistant."},
                {"role": "user",
                 "content": f'''Give the different project ideas to build project in {subject} specifically in {topic} for school students. {overview}.'''},
            ],
            stream=True,
    ):
        if chunk.choices[0].delta.content:
            string += chunk.choices[0].delta.content
    return string


def generate_project_idea_questions(project_idea, query):
    project_idea_answer = ''
    for chunk in AI71(AI71_API_KEY).chat.completions.create(
            model="tiiuae/falcon-180b-chat",
            messages=[
                {"role": "system", "content": "You are a project building assistant."},
                {"role": "user",
                 "content": f'''Assist me clearly for the following question for the given idea. Idea: {project_idea}. Question: {query}'''},
            ],
            stream=True,
    ):
        if chunk.choices[0].delta.content:
            project_idea_answer += chunk.choices[0].delta.content
    return project_idea_answer


def generate_step_by_step_explanation(query):
    explanation = ''
    for chunk in AI71(AI71_API_KEY).chat.completions.create(
            model="tiiuae/falcon-180b-chat",
            messages=[
                {"role": "system", "content": "You are the best teaching assistant."},
                {"role": "user",
                 "content": f'''Provide me the clear step by step explanation answer for the following question. Question: {query}'''},
            ],
            stream=True,
    ):
        if chunk.choices[0].delta.content:
            explanation += chunk.choices[0].delta.content
    return explanation.replace('###', '')


def study_plan(subjects, hours, arealag, goal):
    plan = ''
    for chunk in AI71(AI71_API_KEY).chat.completions.create(
            model="tiiuae/falcon-180b-chat",
            messages=[
                {"role": "system", "content": "You are the best teaching assistant."},
                {"role": "user",
                 "content": f'''Provide me the clear personalised study plan for the subjects {subjects} i lag in areas like {arealag}, im available for {hours} hours per day and my study goal is to {goal}.Provide me like a timetable like day1,day2 for 5 days with concepts,also suggest some books'''},
            ],
            stream=True,
    ):
        if chunk.choices[0].delta.content:
            plan += chunk.choices[0].delta.content
    return plan.replace('\n', '<br>')


class ConversationBufferMemory:
    def __init__(self, memory_key="chat_history"):
        self.memory_key = memory_key
        self.buffer = []

    def add_to_memory(self, interaction):
        self.buffer.append(interaction)

    def get_memory(self):
        return "\n".join([f"Human: {entry['user']}\nAssistant: {entry['assistant']}" for entry in self.buffer])


def spk_msg(user_input, memory):
    chat_history = memory.get_memory()
    msg = ''

    # Construct the message for the API request
    messages = [
        {"role": "system",
         "content": "You are a nice speaker having a conversation with a human.You ask the question the user choose the topic and let user answer.Provide the response only within 2 sentence"},
        {"role": "user",
         "content": f"Previous conversation:\n{chat_history}\n\nNew human question: {user_input}\nResponse:"}
    ]

    try:
        for chunk in AI71(AI71_API_KEY).chat.completions.create(
                model="tiiuae/falcon-180b-chat",
                messages=messages,
                stream=True,
        ):
            if chunk.choices[0].delta.content:
                msg += chunk.choices[0].delta.content
    except Exception as e:
        print(f"An error occurred: {e}")

    return msg


def get_first_youtube_video_link(query):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get('https://www.youtube.com')
        search_box = driver.find_element(By.NAME, 'search_query')
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a#video-title')))
        first_video = driver.find_element(By.CSS_SELECTOR, 'a#video-title')
        first_video_link = first_video.get_attribute('href')
        video_title = first_video.get_attribute('title')
        return first_video_link, video_title
    finally:
        driver.quit()
    return


def content_translate(text):
    translated_content = ''
    for chunk in AI71(AI71_API_KEY).chat.completions.create(
            model="tiiuae/falcon-180b-chat",
            messages=[
                {"role": "system", "content": "You are the best teaching assistant."},
                {"role": "user", "content": f'''Translate the text to hindi. Text: {text}'''},
            ],
            stream=True,
    ):
        if chunk.choices[0].delta.content:
            translated_content += chunk.choices[0].delta.content
    return translated_content


def get_video_id(url):
    """
    Extract the video ID from a YouTube URL.
    """
    parsed_url = urlparse(url)
    if parsed_url.hostname == 'www.youtube.com' or parsed_url.hostname == 'youtube.com':
        video_id = parse_qs(parsed_url.query).get('v')
        if video_id:
            return video_id[0]
    elif parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
    return None


def extract_captions(video_url):
    """
    Extract captions from a YouTube video URL.
    """
    video_id = get_video_id(video_url)
    if not video_id:
        print("Invalid YouTube URL.")
        return

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        formatter = JSONFormatter()
        formatted_transcript = formatter.format_transcript(transcript)

        # Save captions to a file
        with open(f'youtube_captions.json', 'w') as file:
            file.write(formatted_transcript)

        print("Captions have been extracted and saved as JSON.")

    except Exception as e:
        print(f"An error occurred: {e}")


def extract_text_from_json(filename):
    # Open and read the JSON file
    with open(filename, 'r') as file:
        data = json.load(file)

    # Extract and print the text fields
    texts = [entry['text'] for entry in data]
    return texts


def get_simplified_explanation(text):
    prompt = (
        f"The following is a transcript of a video: \n\n{text}\n\n"
        "Please provide a simplified explanation of the video for easy understanding."
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


def summarise_text(url):
    extract_captions(url)
    texts = extract_text_from_json(r'youtube_captions.json')
    os.remove('youtube_captions.json')

    first_half = (get_simplified_explanation(texts[:len(texts) // 2]))[:-6]
    second_half = (get_simplified_explanation(texts[len(texts) // 2:]))[:-6]
    return (first_half + second_half)


def generate_speech_from_pdf(content):
    if os.path.exists('speech'):
        shutil.rmtree('speech')
        os.makedirs('speech', exist_ok=True)
    else:
        os.makedirs('speech', exist_ok=True)

    speech = ''
    for chunk in AI71(AI71_API_KEY).chat.completions.create(
            model="tiiuae/falcon-180b-chat",
            messages=[
                {"role": "system", "content": "You are a summarising assistant."},
                {"role": "user",
                 "content": f'''Summarise the given content for each chapter for 1 sentence.Content={content}'''},
            ],
            stream=True,
    ):
        if chunk.choices[0].delta.content:
            speech += chunk.choices[0].delta.content
    speech = speech[:-6].replace("###", '')
    chapters = speech.split('\n\n')
    pdf_audio(chapters[:4])
    return


def pdf_audio(chapters):
    for i in range(len(chapters)):
        tts = gTTS(text=chapters[i], lang='en', slow=False)
        tts.save(f'speech/chapter {i + 1}.mp3')
    return

def content_translate(text):


    translated_content = ''
    for chunk in AI71(AI71_API_KEY).chat.completions.create(
        model="tiiuae/falcon-180b-chat",
        messages=[
            {"role": "system", "content": "You are the best teaching assistant."},
            {"role": "user", "content": f'''Translate the text to hindi. Text: {text}'''},
        ],
        stream=True,
    ):
        if chunk.choices[0].delta.content:
            translated_content += chunk.choices[0].delta.content
    return translated_content