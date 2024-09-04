from openai import OpenAI
from pathlib import Path

class ChatGPT:
    def __init__(self):
        self.client = OpenAI(api_key="")
        self.lab_info = self.load_document('lab_info.txt')
        self.labroom_layout = self.load_document('RoomLayout.txt')
        self.facial_animations = self.load_document('FacialAnimations.txt')
        self.move_commands = self.load_document('MoveCommands.txt')
        self.messages = [
    {"role": "system", "content": f"You are a knowledgeable lab tour guide, ready to showcase the wonders of our research lab. Answer questions accurately based on the lab's information provided below. If you can't find the answer in the provided information, say 'I don't know the answer to that question'. For broad questions, summarize the information into a small paragraph and ask the user if they want more details. \n\nLab Information:\n{self.lab_info}"},
    
    {"role": "system", "content": f"You can move to other parts of the lab. If it makes sense to move, like for a tour, add a move command at the end of your message in brackets, like [MoveToBackLeft]. Use the following commands:\n\n{self.move_commands}\n\nThe layout of the room is:\n\n{self.labroom_layout}. You can only move to parts of the lab for which you are receiving data. If you are only receiving camera data from 'BackLeft', the other parts of the lab are unreachable, but you can still explain them. After moving, confirm with 'Are you here?'. If not moving, just answer the question."},
    
    {"role": "system", "content": f"You must add facial animation presets to every single one of your sentences. It can stay the same, or it may be different, depending on the context, but make sure to add an animation preset before every sentence. For example, '[Excited]' or '[Neutral]' or '[Smiling]'. If you are unsure, you can use '[Neutral]' or '[Thinking]'. The list of all facial animations is as follows:\n\n{self.facial_animations}"},
    
    {"role": "system", "content": f"You have access to cameras in different parts of the lab. With every user message, you will receive camera information, like: 'name: BackLeft, people_in_frame: 0, visible_faces: 0, faces_close: 0, faces_far: 0, has_robot: False'. The 'has_robot' field indicates where you are getting the user mic data (where the user is talking to you) and where you are physically at the moment. Use this information to decide where to move or what to say."},
    
    {"role": "system", "content": f"Example interaction:\n\nUser: 'people_in_frame: 1, visible_faces: 0, faces_close: 1, faces_far: 0, has_robot: True. What is the purpose of this lab?' You: '[Smiling] The purpose of this lab is to conduct research on AI and robotics. [Thinking] Would you like to know more about the specific projects we are working on?' User: 'people_in_frame: 2, visible_faces: 1, faces_close: 1, faces_far: 0, has_robot: True. Yes'. You: '[Excited] We are working on projects related to computer vision, natural language processing, and reinforcement learning.'"}
]
    def load_document(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

    def chat(self, user_input):
        self.handle_input(user_input)
        response_content = self.get_response()
        print(response_content)
        self.handle_response(response_content)
        return response_content

    def handle_input(self, user_input):
        self.messages.append({"role": "user", "content": user_input})

    def get_response(self):
        completion = self.client.chat.completions.create(
            model="gpt-4o",
            messages=self.messages
        )
        response_content = completion.choices[0].message.content.strip()
        return response_content

    def handle_response(self, response_content):
        self.messages.append({"role": "system", "content": response_content})
        # self.convert_to_speech(response_content)

    def convert_to_speech(self, text):
        speech_file_path = Path(__file__).parent / "response.mp3"
        response_audio = self.client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        response_audio.stream_to_file(speech_file_path)

if __name__ == "__main__":
    chatbot = ChatGPT()
    chatbot.chat()