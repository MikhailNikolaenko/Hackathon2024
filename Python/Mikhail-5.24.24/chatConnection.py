from openai import OpenAI
from pathlib import Path

client = OpenAI()

# Load the document content
def load_document(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

lab_info = load_document('lab_info.txt')

completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": f"You are a knowledgeable lab tour guide, ready to showcase the wonders of our research lab. Answer questions accurately based on the lab's information provided below. Answer to questions that you know the answer to; If you can't find it in the provided information, say 'I don't know the answer to that question'. If it is a long answer to a question, such as when the question is broad, please summarize the information into no longer than a small paragraph and ask the user if they want to go into more detail into anything specific. \n\nLab Information:\n{lab_info}"},
        {"role": "user", "content": "Tell me about the most recent project done by the XR lab."}
    ]
)

answer = str(completion.choices[0].message.content)
answer = answer.strip()

print(completion.choices[0].message.content)


# SPEECH SYNTHESIS
# Save the synthesized speech to a file
speech_file_path = Path(__file__).parent / "speech.mp3"
response = client.audio.speech.create(
  model="tts-1",
  voice="alloy",
  input=answer
)

response.stream_to_file(speech_file_path)