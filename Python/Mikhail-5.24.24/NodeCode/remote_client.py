import asyncio
import websockets
import json
import base64
from pydub import AudioSegment
from host_Nodeserver import handle_event, getDuration, setDuration, getReceivedAudio, setReceivedAudio, setReceivedEnd, getReceivedEnd, node_info
import threading
from IOHandler import SpeechRecognizer


connected_websockets = {}

ready = False

globalname = ''

# remote_client.py

# Import the event handler from host_server

async def send_camera_data(websocket, name, speech_recognizer):
    """
    Sends camera data to the remote server, including statistics on people and face detection.
    """
    stats = speech_recognizer.stats
    camera_data = {
        "name": name,  # The name of the client
        "type": "cameraData",
        "people_in_frame": stats["people_in_frame"],
        "visible_faces": stats["visible_faces"],
        "faces_closer_than_2m": stats["faces_closer_than_2m"],
        "faces_beyond_2m": stats["faces_beyond_2m"]
    }
    await websocket.send(json.dumps(camera_data))
    pass


async def poll_microphone_and_send(websocket, speech_recognizer, name):
    while True:
        if not node_info["has_robot"]:
            await asyncio.sleep(0.1)
            continue
        if speech_recognizer.mic_on:
            await send_mic(websocket, speech_recognizer, name, 0.1)
        elif getDuration() == 0:
            await asyncio.sleep(0.1)
        elif getDuration() != 0 and getReceivedEnd():
            await asyncio.sleep(getDuration())
            speech_recognizer.mic_on = True
            print("Microphone on...")
            speech_recognizer.transcriptionData = ""
            setReceivedEnd(False)
            setDuration(0)
        else:
            await asyncio.sleep(0.1)  # Always yield control back to the event loop

async def send_mic(websocket, speech_recognizer, name, time):
    await asyncio.sleep(time)  # Polling interval
    if speech_recognizer.transcriptionData:
        audio_data = {
        "name": name,
        "type": "MicrophoneData",
        "data": speech_recognizer.transcriptionData  # Synchronously get data
    }
        speech_recognizer.transcriptionData = ""  # Clear the data
        await websocket.send(json.dumps(audio_data))
        speech_recognizer.mic_on = False
        print("Microphone off...")
        

async def send_text(data):
    """
    Sends text data to the remote server.

    Args:
        websocket: The WebSocket connection.
        name: The name of the client.
    """
    websocket = connected_websockets["Remote"]

    await websocket.send(json.dumps({"name": globalname, "type": "text", "data": data}))
    pass

async def send_audio(websocket, name):
    """
    Sends audio data to the remote server.

    Args:
        websocket: The WebSocket connection.
        name: The name of the client.
    """
    audio = AudioSegment.from_mp3("speech.mp3")
    audio.export("speech.wav", format="wav")

    with open("speech.wav", "rb") as audio_file:
        audio_data = audio_file.read()

    audio_base64 = base64.b64encode(audio_data).decode('utf-8')

    chunk_size = 4096
    for i in range(0, len(audio_base64), chunk_size):
        chunk = audio_base64[i:i + chunk_size]
        message = {"name": name, "type": "audio", "data": chunk}
        await websocket.send(json.dumps(message))

    end_message = {"name": name, "type": "audio_end"}
    await websocket.send(json.dumps(end_message))

async def receive_message(websocket, speech_recognizer):
    """
    Receives messages from the remote server.

    Args:
        websocket: The WebSocket connection.
    """
    async for message in websocket:
        print(f"Received: {message}")

        try:
            data = json.loads(message)  # Parse the JSON string into a Python dictionary
        except json.JSONDecodeError:
            print("Failed to decode JSON from the message.")
            continue  # Skip to the next message if decoding fails

        # Check if the message contains the animation request and trigger the event
        if data.get("data") == "[MoveInFrame]":
            await handle_event(data)  # Pass the dictionary to handle_event

        if data.get("type") == "request":
            if data.get("data") == "CameraData":
                await handle_request(websocket, data, speech_recognizer)  # Pass the dictionary to handle_request

        if data.get("type") == "ChatResponse":
            print(f"Received chat response: {data['data']}")
            await handle_event(data)  # Pass the dictionary to handle_event

        if data.get("data") == "[LeaveFrame]":
            await handle_event(data)  # Pass the dictionary to handle_event

async def handle_request(websocket, request_data, speech_recognizer):
    """
    Handles requests from the remote server.

    Args:
        websocket: The WebSocket connection.
        request_data: The request data received from the server.
    """
    # Example of handling a request
    if request_data["data"] == "CameraData":
        print("Received a request for CameraData.")
        # Send the camera data to the requesting node
        await send_camera_data(websocket, request_data["name"], speech_recognizer)
        pass

async def connect_to_remote(name):
    """
    Connects to the remote server.

    Args:
        name: The name of the client.
    """
    remote_uri = "ws://localhost:6790"  # The URI of the remote server
    # remote_uri = "ws://10.168.3.106:6790"  # The URI of the remote server

    global globalname
    globalname = name

    async with websockets.connect(remote_uri) as websocket:
        
        speech_recognizer = SpeechRecognizer(websocket=websocket)
        recognizer_thread = threading.Thread(target=speech_recognizer.run)

        connected_websockets["Remote"] = websocket
        
        try:
            # Start the speech recognizer thread
            recognizer_thread.start()

            text_task = asyncio.create_task(send_text("Hello from the client!"))
            receive_task = asyncio.create_task(receive_message(websocket, speech_recognizer))
            mic_task = asyncio.create_task(poll_microphone_and_send(websocket, speech_recognizer, name))
            await asyncio.gather(text_task, receive_task, mic_task)
        finally:
            # Stop the speech recognizer when done or on error
            speech_recognizer.stop_threads.set()
            recognizer_thread.join()  # Ensure the thread has finished