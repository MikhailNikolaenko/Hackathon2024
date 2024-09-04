import cv2
import numpy as np
import time

# Paths to the model files
prototxt_path = 'deploy.prototxt.txt'  # Update the path if needed
model_path = 'res10_300x300_ssd_iter_140000.caffemodel'  # Update the path if needed

# Load the pre-trained MobileNet SSD model for face detection
net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)

# Load the pre-trained MobileNet SSD model for person detection
person_prototxt = "MobileNetSSD_deploy.prototxt"
person_model = "MobileNetSSD_deploy.caffemodel"
net_person = cv2.dnn.readNetFromCaffe(person_prototxt, person_model)

# Load the pre-trained Haar Cascade Classifier for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Function to detect faces using Haar Cascade
def detect_faces(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    return faces

# Initialize the webcam feed
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

# Variables to track time for updating detection every second
start_time = time.time()
detection_interval = 1.0  # in seconds

# Variables to store detected faces and persons
detected_faces = []
detected_persons = []

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture image.")
        break

    # Get the current time
    current_time = time.time()
    
    # Check if the detection interval has passed
    if current_time - start_time >= detection_interval:
        # Detect faces
        detected_faces = detect_faces(frame)

        # Prepare the frame for person detection
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)
        net_person.setInput(blob)
        detections = net_person.forward()

        # Process the person detections
        detected_persons = []
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > 0.2:  # Confidence threshold
                idx = int(detections[0, 0, i, 1])
                if idx == 15:  # Class ID for 'person' in COCO dataset
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (startX, startY, endX, endY) = box.astype("int")
                    detected_persons.append((startX, startY, endX, endY))

        # Reset the start time
        start_time = current_time

    # Draw rectangles around detected faces
    for (x, y, w, h) in detected_faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        cv2.putText(frame, 'Face', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

    # Draw rectangles around detected persons
    for (startX, startY, endX, endY) in detected_persons:
        cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
        cv2.putText(frame, 'Person', (startX, startY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    # Display the frame with detected faces and bodies
    cv2.imshow('Face and Body Detection', frame)

    # Exit the loop when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and close the window
cap.release()
cv2.destroyAllWindows()