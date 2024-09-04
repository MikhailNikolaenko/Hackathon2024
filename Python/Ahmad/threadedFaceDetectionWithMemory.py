import cv2
import face_recognition
import numpy as np
import os
from collections import defaultdict
import threading

# Initialize some variables
known_face_encodings = []
known_face_names = []
process_this_frame = True
face_data = defaultdict(lambda: {'last_seen': 0, 'name': ''})
face_id = 0
lock = threading.Lock()
frame = None  # Define frame variable

# Create 'known' directory if it doesn't exist
known_folder = './Ahmad/known'
if not os.path.exists(known_folder):
    os.makedirs(known_folder)

# Load known faces from the 'known' directory
def load_known_faces(known_folder='./Ahmad/known'):
    global known_face_encodings, known_face_names, face_id
    for filename in os.listdir(known_folder):
        if filename.endswith(".jpg") or filename.endswith(".png"):
            img = face_recognition.load_image_file(os.path.join(known_folder, filename))
            encodings = face_recognition.face_encodings(img)
            if encodings:
                img_encoding = encodings[0]
                known_face_encodings.append(img_encoding)
                name = filename.split('.')[0]
                known_face_names.append(name)
                face_data[name]['last_seen'] = 0
                face_data[name]['name'] = name
                # Ensure face_id is greater than the highest known face ID
                if name.startswith("Person"):
                    person_id = int(name.split()[1])
                    face_id = max(face_id, person_id + 1)

# Save the new face to the known folder
def save_new_face(face_encoding, face_image):
    global face_id, known_face_encodings, known_face_names
    name = f"Face{len(known_face_names) + 1}"  # Generate sequential name
    known_face_encodings.append(face_encoding)
    known_face_names.append(name)
    face_data[name]['name'] = name
    face_data[name]['last_seen'] = 0
    # Save the image to the known folder
    filename = f'{known_folder}/{name}.jpg'
    cv2.imwrite(filename, face_image)
    print(f"New face saved as {filename}")

# Load known faces
load_known_faces()

# Function to capture frames from video
def capture_frames():
    global frame
    video_capture = cv2.VideoCapture(0)
    while True:
        ret, frame = video_capture.read()

# Function to process frames for face recognition
# Function to process frames for face recognition
def process_frames():
    global frame
    while True:
        if frame is not None and frame.shape[0] > 0 and frame.shape[1] > 0:  # Check if frame dimensions are valid
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            face_names = []
            for face_encoding, face_location in zip(face_encodings, face_locations):
                # Check if the face is a match for the known face(s)
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                name = "Unknown"

                # If it's an unknown face, assign a new ID and save the image
                if True in matches:
                    first_match_index = matches.index(True)
                    name = known_face_names[first_match_index]

                # If it's an unknown face, assign a new ID and save the image
                else:
                    name = f"Face{len(known_face_names) + 1}"  # Generate sequential name
                    top, right, bottom, left = face_location  # Define face bounding box
                    with lock:
                        save_new_face(face_encoding, frame[top*4:bottom*4, left*4:right*4])  # Pass the face image

                face_names.append(name)

                # Update last seen for the face
                face_data[name]['last_seen'] = 0

            # Update last seen times and remove old data
            for name in list(face_data.keys()):
                face_data[name]['last_seen'] += 1
                if face_data[name]['last_seen'] > 100:  # Adjust timeout as necessary
                    del face_data[name]

            # Display the results
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                # Draw a box around the face
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

                # Draw a label with a name below the face
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

            # Display the resulting image
            cv2.imshow('Video', frame)

            # Hit 'q' on the keyboard to quit!
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

# Start the threads
threading.Thread(target=capture_frames).start()
threading.Thread(target=process_frames).start()