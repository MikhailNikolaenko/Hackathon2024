# host_Nodeserver.py
import asyncio
import websockets
import json
import base64
import os
from pydub import AudioSegment
from openai import OpenAI
from pathlib import Path
import re
 
clients = {}
server_ready = asyncio.Event()  # Event to signal the server is ready to accept connections
node_info = {
    "has_robot": False,
    "name": "Node Server",
    # Add more information about the node server here
}
duration_together = 0
received_audio = False
received_animation = False
received_end = False
finished_animation = False
 
## Event handler function
async def handle_event(event_data):
    # Example of handling an event
    if event_data["type"] == "ChatResponse":
        await decode_response_text(event_data["data"])
        # await send_chat_response_to_clients(event_data["data"])
 
    if event_data["data"] == "[MoveInFrame]":
        node_info["has_robot"] = True
        await send_animation_request_to_clients("[MoveInFrame]", facial_expression=False)
   
    if event_data["data"] == "[LeaveFrame]":
        node_info["has_robot"] = False
        await send_animation_request_to_clients("[LeaveFrame]", facial_expression=False)
   
 
async def send_chat_response_to_clients(chat_data):
    convert_to_speech(chat_data)
    for client, name in clients.items():
        await send_audio(client, "response.mp3")
 
async def decode_response_text(response_text):
    tags = ['[MoveToFrontLeft]', '[MoveToFrontRight]', '[MovetoBackLeft]']
    pattern = '|'.join(re.escape(tag) for tag in tags)
    matches = re.findall(pattern, response_text, flags=re.IGNORECASE)  # Case-insensitive match
    includes_move_tag = False
   
    if matches:
        # Remove the move tags from the response text
        includes_move_tag = True
        for tag in matches:
            response_text = re.sub(re.escape(tag), "", response_text, flags=re.IGNORECASE)
       
        print("Found move tags:", matches)
   
    else:
        print("No move tags found")
   
    await handle_chat_with_emotion(response_text, includes_move_tag, matches)
    return response_text
 
 
async def handle_chat_with_emotion(response_text, includes_move_tag, move_tags):
   
    # Define the animation tags
    animation_tags = ['[Exited]', '[Neutral]', '[Smiling]', '[Thinking]', '[Surprised]', '[Laughing]', '[Excited]']
    default_tag = '[Neutral]'  # Define a default tag for text without explicit tags
   
    # Split the response text at animation tags, keeping the tags with the sentences
    parts = re.split(r'(\[.*?\])', response_text)
   
    # Clean up empty strings and strip spaces
    parts = [part.strip() for part in parts if part.strip()]
 
    # Organize data into a list of (tag, sentence) tuples
    animation_data = []
    tag = default_tag  # Start with a default tag
    for part in parts:
        if part in animation_tags:
            tag = part  # Update the current tag
        else:
            animation_data.append((tag, part))  # Append the current tag and sentence
 
    # Convert sentences to speech and get durations
    speech_files = []
    full_duration = 0
    for index, (tag, sentence) in enumerate(animation_data):
        print(f"Here is the tag: {tag}, and here is the sentence: {sentence}")
        duration = convert_to_speech(sentence, index + 1)  # Pass index + 1 as rowNumber
        full_duration += duration
        file_path = Path(__file__).parent / f"response_{index + 1}.mp3"
        file_name = f"response_{index + 1}.mp3"
        speech_files.append((tag, file_path, file_name, duration))
 
    global duration_together
    duration_together = full_duration
    # Default for first run
    setReceivedAudio(True)
 
    for client, name in clients.items():
        for tag, sentence, file_name, duration in speech_files:
            while True:
                if getReceivedAudio() == True:
                    setReceivedAudio(False)
                    break
                else:
                    await asyncio.sleep(0.1)
            await send_animation_request_to_clients(tag, facial_expression=True)
            print(f"Going to send audio to node.")
            await send_audio(client, file_name, duration)
 
        await send_full_response_message(client, name)
    if includes_move_tag:
        await handle_move_tags(move_tags)
 
async def handle_move_tags(move_tags):
    data = str(move_tags)
    from remote_client import send_text
    await send_text(data)
    # for move_tag in move_tags:
    #     await send_animation_request_to_clients(move_tag, facial_expression=False)
 
async def send_text_to_clients(type, text):
    for client, name in clients.items():
        await client.send(json.dumps({"name": name, "type": type, "data": text}))
 
async def send_full_response_message(websocket, name):
    end_message = {"name": name, "type": "response_end"}
    await websocket.send(json.dumps(end_message))
 
def get_full_duration(speech_files):
    full_duration = 0
    for speech_file in speech_files:
        audio = AudioSegment.from_mp3(speech_file)
        full_duration += audio.duration_seconds
    global duration
    duration = full_duration
 
def get_partial_duration(path):
    audio = AudioSegment.from_mp3(path)
    return audio.duration_seconds
 
def convert_to_speech(text, rowNumber):
    client = OpenAI(api_key="sk-proj-1azr5CQzijqGLS2vCtruT3BlbkFJ1w7ZKNnDE6mBGuXyRfug")
    speech_file_path = Path(__file__).parent / f"response_{rowNumber}.mp3"
    response_audio = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text
    )
    response_audio.stream_to_file(speech_file_path)
    return get_partial_duration(speech_file_path)
 
async def send_animation_request_to_clients(type, facial_expression=False):
    message = {}
    waitforresponse = False
    if facial_expression:
        message = {"type": "animation", "data": type, "facial_expression": "True"}
    else:
        message = {"type": "animation", "data": type, "facial_expression": "False"}
        waitforresponse = True
    for client, name in clients.items():
        await client.send(json.dumps(message))
        print(f"Sent animation request to {name} node.")
        while True:
            if getReceivedAnimation() == True:
                print("Received animation acknowledgment")
                setReceivedAnimation(False)
                break
            await asyncio.sleep(0.1)
        if waitforresponse:
            while True:
                if getFinishedAnimation() == True:
                    print("Received animation finished acknowledgment")
                    setFinishedAnimation(False)
                    break
                await asyncio.sleep(0.1)
 
## Server
def change_working_directory(new_directory):
    try:
        os.chdir(new_directory)
        print(f"Changed working directory to: {new_directory}")
    except Exception as e:
        print(f"Error: {e}")
 
def read_text_file():
    try:
        with open("response.txt", "r") as text_file:
            text_data = text_file.read()
        return text_data
    except FileNotFoundError:
        print("The file 'response.txt' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
 
import hashlib
 
def compute_checksum(data):
    return hashlib.md5(data).hexdigest()
 
async def send_audio(websocket, name, duration=None):
    audio = AudioSegment.from_mp3(name)
    audio.export("response.wav", format="wav")
 
    with open("response.wav", "rb") as audio_file:
        audio_data = audio_file.read()
 
    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
    checksum = compute_checksum(audio_data)
    print(f"Checksum before sending: {checksum}")
 
    chunk_size = 4096
    for i in range(0, len(audio_base64), chunk_size):
        chunk = audio_base64[i:i + chunk_size]
        message = {"name": name, "type": "audio", "data": chunk}
        await websocket.send(json.dumps(message))
        print(f"Sent audio chunk data to node.")
 
    end_message = {"name": name, "type": "audio_end", "duration": duration, "checksum": checksum}
    await websocket.send(json.dumps(end_message))
    print(f"Sent audio end message to node.")
 
    # Clean up resources
    os.remove("response.wav")
 
def getDuration():
    global duration_together
    return duration_together
 
def setDuration(time):
    global duration_together
    duration_together = time
 
def getReceivedAudio():
    global received_audio
    return received_audio
 
def setReceivedAudio(value):
    global received_audio
    received_audio = value
 
def getReceivedAnimation():
    global received_animation
    return received_animation
 
def setReceivedAnimation(value):
    global received_animation
    received_animation = value
 
def getReceivedEnd():
    global received_end
    return received_end
 
def setReceivedEnd(value):
    global received_end
    received_end = value
 
def getFinishedAnimation():
    global finished_animation
    return finished_animation
 
def setFinishedAnimation(value):
    global finished_animation
    finished_animation = value
 
async def register(websocket, path):
    print(f"New connection attempt at path: {path}")
    global server_ready
    try:
        message = await websocket.recv()
        print(f"Initial message received: {message}")
 
        data = json.loads(message)
        name = data["name"]
        clients[websocket] = name
        print(f"Node {name} connected")
 
        server_ready.set()  # Signal that the first client has connected
        print("server_ready event set!")
 
        # text_data = read_text_file()
        # await websocket.send(json.dumps({"type": "text", "data": text_data}))
 
        # await send_audio(websocket, "speech.wav")
 
        await handle_messages(websocket, name)
    except websockets.ConnectionClosed:
        print(f"Connection with {name} closed")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if websocket in clients:
            del clients[websocket]
 
async def handle_messages(websocket, name):
    async for message in websocket:
        try:
            data = json.loads(message)
            print(f"Received from {name}: {data['data']}")
 
            if data.get("type") == "audio_end_ack":
                setReceivedAudio(True)
                pass
                # print("Received audio end acknowledgment")
                # setFirstRun(True)
                # setDuration(0)
 
            if data.get("type") == "animation_ack":
                setReceivedAnimation(True)
                pass
                # print("Received animation acknowledgment")
 
            if data.get("type") == "response_end_ack":
                print("Received response end acknowledgment")
                setReceivedEnd(True)
                # Handle the request message
                pass
 
            if data.get("type") == "animation_end_ack":
                print("Received animation end acknowledgment")
                setFinishedAnimation(True)
                # Handle the request message
                pass
 
        except Exception as e:
            print(f"Error while handling message: {e}")
 
async def websocket_server():
    server = await websockets.serve(register, "localhost", 6789)
    print("Waiting for Unreal Engine client to connect...")
    await server_ready.wait()  # Wait until the first client is connected
    print("WebSocket server started on ws://localhost:6789")
    await server.wait_closed()