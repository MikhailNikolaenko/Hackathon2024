import asyncio
import websockets
import json
from chatHandler import ChatGPT

clients = {}
node_details = {}
chat = ChatGPT()

## Server
async def register(websocket):
    try:
        message = await websocket.recv()
        data = json.loads(message)
        name = data["name"]
        clients[websocket] = name
        node_details[name] = {"people_in_frame": 0, "visible_faces": 0, "faces_close": 0, "faces_far": 0, "has_robot": False}
        print(f"Node {name} connected")

        # Send animation request to the first client
        if len(clients) == 1:
            node_details[name]["has_robot"] = True
            await send_animation_request(websocket, name, "[MoveInFrame]")

        await handle_messages(websocket, name)
    except websockets.ConnectionClosed:
        print(f"Connection with {name} closed")
    finally:
        if websocket in clients:
            del clients[websocket]
            del node_details[name]

async def handle_messages(websocket, name):
    async for message in websocket:
        data = json.loads(message)
        print(f"Received from {data['name']}")

        if data.get("type") == "cameraData":
            # Update node details based on incoming messages
            if 'people_in_frame' in data:
                node_details[name]['people_in_frame'] = data['people_in_frame']
                # print(f"Updated people_in_frame for {name}: {node_details[name]['people_in_frame']}")
            if 'visible_faces' in data:
                node_details[name]['visible_faces'] = data['visible_faces']
                # print(f"Updated visible_faces for {name}: {node_details[name]['visible_faces']}")
            if 'faces_closer_than_2m' in data:
                node_details[name]['faces_close'] = data['faces_closer_than_2m']
                # print(f"Updated faces_close for {name}: {node_details[name]['faces_close']}")
            if 'faces_beyond_2m' in data:
                node_details[name]['faces_far'] = data['faces_beyond_2m']
                # print(f"Updated faces_far for {name}: {node_details[name]['faces_far']}")

        if data.get("type") == "MicrophoneData":
            print(f"Received audio data from {name} node.")
            if node_details[name]["has_robot"]:
                await handle_microphone_data(websocket, data)
            else:
                print("Node does not have a robot.")

        if data.get("type") == "text":
            print(f"Received text data from {name} node.")
            await handle_text_data(websocket, data)
        # # Broadcast to all other clients
        # for client in clients:
        #     if client != websocket:
        #         await client.send(json.dumps(data))


# Collect node details
def collect_node_data():
    return node_details


# Handle microphone data
async def handle_microphone_data(websocket, data):
    # Add your implementation here
    mic_data = str(collect_node_data()) + "User: " + data['data']
    response = chat.chat(mic_data)
    message = {"type": "ChatResponse", "data": response}
    await websocket.send(json.dumps(message))
    pass

async def handle_text_data(websocket, data):
    # Add your implementation here
    print(data.get("data"))
    nodewBot, nameOfNode = checkRobot()
    movement_map = {
        "[MoveToFrontLeft]": "FrontLeft",
        "[MoveToFrontRight]": "FrontRight",
        "[MoveToBackLeft]": "BackLeft"
    }
    movement = movement_map.get(data.get("data"))
    if movement and checkAvailability(movement):
        if not node_details[movement]["has_robot"]:
            nodeToGoto = getNodewithName(movement)
            await send_animation_request(nodewBot, nameOfNode, "[LeaveFrame]")
            await asyncio.sleep(5)
            await send_animation_request(nodeToGoto, movement, "[MoveInFrame]")
            node_details[nameOfNode]["has_robot"] = False
            node_details[movement]["has_robot"] = True
    else:
        print("Invalid movement or node not available")
    pass

def checkAvailability(name):
    if name in clients:
        return True
    else:
        return False

def checkRobot():
    for client, name in clients.items():
        if node_details[name]["has_robot"]:
            return client, name
    return None

def getNodewithName(name):
    for client, nodeName in clients.items():
        if nodeName == name:
            return client
    return None

## Periodic data requests
async def send_periodic_requests():
    while True:
        await asyncio.sleep(10)  # Adjust the interval as needed
        await request_node_data()

async def request_node_data():
    for client, name in clients.items():
        message = {"name": name, "type": "request", "data": "CameraData"}
        await client.send(json.dumps(message))
        print(f"Requested camera data from {name} node.")

## Animation requests
async def send_animation_request(websocket, name, animationType):
    message = {"type": "text", "data": animationType}
    await websocket.send(json.dumps(message))
    print(f"Sent animation request to {name} node.")

## Main function
async def main():
    server = await websockets.serve(register, "0.0.0.0", 6790)
    print("Server started")

    # Run the periodic data request in the background
    data_request_task = asyncio.create_task(send_periodic_requests())

    await server.wait_closed()
    await data_request_task

if __name__ == "__main__":
    asyncio.run(main())