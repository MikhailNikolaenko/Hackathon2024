import google.generativeai as genai
from talkingFace import talk
from speechAndPresenceDetection import SpeechRecognizer
import threading

def formatResponse(text):
    lines = text.split('\n')
    formattedLines = []
    for l in lines:
        l = l.replace('[', '').replace(']', '').replace('*', '')
        splitLine = l.split(' ', 1)
        if (splitLine != ['']): 
            formattedLines += [splitLine]
    return formattedLines

genai.configure(api_key="AIzaSyCcMeCIo-xF6X_vkcyxRrVjVaCXpbbziPA")

with open('./Mikhail-5.24.24/lab_info.txt', encoding='utf-8') as file:
    instructions = ("You are a knowledgeable research assistant at the University of Cincinnati's eXtended Reality Laboratory. "
                    "Try to sound natural and be human, don't be too verbose. "
                    "Provide replies that would make sense being spoken out loud by a person, not just written down. "
                    "So for example, DO NOT try to format text with asterisks or anything else. "
                    "Throughout your response add emotion tags in brackets([Happy], [Sad], [NeutralFace], [Angry], [Thinking], [Suprised]) before the text they relate to, "
                    "to make the conversation more natural and engaging, be enthusiastic and friendly. "
                    "Before each emotion ALWAYS add a newline, so each line is a different emotion." + file.read())

model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=instructions)
chat = model.start_chat(history=[])

query = input('Query: ')
while (query != 'DONE'):
    response = chat.send_message(query).text
    formattedResponse = formatResponse(response)
    print(response)
    print(formattedResponse)
    query = input('Query: ')
