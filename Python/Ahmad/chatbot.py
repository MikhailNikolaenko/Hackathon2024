import google.generativeai as genai
from talkingFace import talk
from speechAndPresenceDetection import SpeechRecognizer
import threading

genai.configure(api_key="AIzaSyCcMeCIo-xF6X_vkcyxRrVjVaCXpbbziPA")

with open('./Mikhail-5.24.24/lab_info.txt', encoding='utf-8') as file:
    instructions = ("You are a knowledgeable research assistant at the University of Cincinnati's eXtended Reality Laboratory. "
                    "Try to sound natural and be human, don't be too verbose. Keep your replies to five sentences or less. "
                    "Provide replies that would make sense being spoken out loud by a person, not just written down. "
                    "So for example, don't try to format text with asterisks or anything else. " + file.read())

model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=instructions)
chat = model.start_chat(history=[])
recognizer = SpeechRecognizer()

def process_query():
    while True:
        query = recognizer.start_face_detection()
        if query:
            response = chat.send_message(query)
            talk(response.text)

query_thread = threading.Thread(target=process_query)
query_thread.start()