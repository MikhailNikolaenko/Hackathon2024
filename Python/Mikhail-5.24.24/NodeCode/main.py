# main.py
import asyncio
import os
from host_Nodeserver import websocket_server, change_working_directory, server_ready
from remote_client import connect_to_remote

async def websocket_server_with_signal():
    await websocket_server()  # Start the server and wait for a connection

async def connect_to_remote_when_ready(name):
    await server_ready.wait()  # Wait until the server is ready
    await connect_to_remote(name)

async def main():
    name = input("Enter the name of the node: ")
    # name = "BackLeft"

    server_task = asyncio.create_task(websocket_server_with_signal())
    client_task = asyncio.create_task(connect_to_remote_when_ready(name))

    await asyncio.gather(server_task, client_task)

if __name__ == "__main__":
    new_directory = r"Z:\GitHub\speechDetection\Mikhail-5.24.24\NodeCode"
    change_working_directory(new_directory)

    print(f"Current working directory: {os.getcwd()}")

    asyncio.run(main())