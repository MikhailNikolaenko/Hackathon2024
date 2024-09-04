import speech_recognition as sr
import numpy as np
import cv2
import threading
import time
import asyncio
import json

class SpeechRecognizer:
    def __init__(self, websocket=None, threshold=10):
        self.websocket = websocket  # Store the WebSocket connection object
        self.mic_on = True
        self.threshold = threshold
        self.recognizer = sr.Recognizer()
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.stop_threads = threading.Event()
        self.KNOWN_WIDTH = 14.0  # in cm
        self.FOCAL_LENGTH = 615  # adjust this based on your camera
        self.stats = {"people_in_frame": 0, "visible_faces": 0, "faces_closer_than_2m": 0, "faces_beyond_2m": 0}
        self.transcriptionData = ""
        self.update_lock = threading.Lock()

         # Load MobileNet SSD for person detection
        self.person_prototxt = "MobileNetSSD_deploy.prototxt"
        self.person_model = "MobileNetSSD_deploy.caffemodel"
        self.net_person = cv2.dnn.readNetFromCaffe(self.person_prototxt, self.person_model)


    def is_talking(self, audio_data):
        audio_array = np.frombuffer(audio_data.get_raw_data(), dtype=np.int16)
        volume = np.sqrt(np.mean(audio_array**2))
        return volume > self.threshold

    def estimate_distance(self, face_width):
        return (self.KNOWN_WIDTH * self.FOCAL_LENGTH) / face_width
    
    def recognize_speech(self):
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("Listening for speech...")

            while not self.stop_threads.is_set():
                try:
                    audio_data = self.recognizer.listen(source)
                    if self.is_talking(audio_data):
                        transcription = self.recognizer.recognize_google(audio_data)
                        print(f"Transcription: {transcription}")
                        self.transcriptionData = transcription
                except sr.UnknownValueError:
                    print("Could not understand audio")
                except sr.RequestError as e:
                    print(f"Could not request results; {e}")
                except Exception as e:
                    print(f"An error occurred during transcription: {e}")

    def update_statistics(self):
        while not self.stop_threads.is_set():
            # with self.update_lock:
                # print(self.stats)
            time.sleep(1)  # Update every second

    def start_face_and_person_detection(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open camera.")
            return

        while not self.stop_threads.is_set():
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not capture frame.")
                continue

            # Person detection
            h, w = frame.shape[:2]
            blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)
            self.net_person.setInput(blob)
            detections = self.net_person.forward()
            people_count = sum(1 for i in range(detections.shape[2]) if detections[0, 0, i, 2] > 0.2 and int(detections[0, 0, i, 1]) == 15)

            # Face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
            face_distances = [self.estimate_distance(w) for (x, y, w, h) in faces]

            with self.update_lock:
                self.stats["people_in_frame"] = people_count
                self.stats["visible_faces"] = len(faces)
                self.stats["faces_closer_than_2m"] = sum(1 for distance in face_distances if distance < 200)
                self.stats["faces_beyond_2m"] = sum(1 for distance in face_distances if distance >= 200)

            cv2.imshow('Frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.stop_threads.set()

        cap.release()
        cv2.destroyAllWindows()

    def run(self):
        # Start threads for face and person detection and speech recognition
        thread_detection = threading.Thread(target=self.start_face_and_person_detection)
        thread_speech = threading.Thread(target=self.recognize_speech)
        thread_stats = threading.Thread(target=self.update_statistics)

        thread_detection.start()
        thread_speech.start()
        thread_stats.start()

        thread_detection.join()
        thread_speech.join()
        thread_stats.join()

if __name__ == '__main__':
    recognizer = SpeechRecognizer()
    recognizer.run()






## okay, so i have this remote_client.py code, that communicates with a remote client websocket server. this server periodically sends cameradata requests to this code, which requires stores camera data to be sent back. How can I adjust this code to utilize the speechrecognizer class to determine how many people are in frame, how many are beyond 2 m, how many or closer than 2 meters, how many faces are visible / etc.