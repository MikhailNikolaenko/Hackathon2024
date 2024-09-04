import speech_recognition as sr
import numpy as np
import cv2

class SpeechRecognizer:
    def __init__(self, threshold=10):
        self.threshold = threshold
        self.recognizer = sr.Recognizer()
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def is_talking(self, audio_data):
        audio_array = np.frombuffer(audio_data.get_raw_data(), dtype=np.int16)
        volume = np.sqrt(np.mean(audio_array**2))
        return volume > self.threshold

    def detect_faces(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        small_frame = cv2.resize(gray, (0, 0), fx=0.5, fy=0.5)
        faces = self.face_cascade.detectMultiScale(small_frame, 1.3, 5)
        return faces

    def recognize_speech(self):
        with sr.Microphone() as source:
            print("Adjusting for ambient noise, please wait...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("Listening for speech...")

            while True:
                audio_data = self.recognizer.listen(source)
                if self.is_talking(audio_data):
                    try:
                        transcription = self.recognizer.recognize_google(audio_data)
                        return transcription
                    except sr.UnknownValueError:
                        print("Could not understand audio")
                    except sr.RequestError as e:
                        print(f"Could not request results; {e}")
                    except Exception as e:
                        print(f"An error occurred during transcription: {e}")
                else:
                    return None

    def start_face_detection(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open camera.")
            return

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not capture frame.")
                break

            faces = self.detect_faces(frame)
            if len(faces) > 0:
                print("Face detected...")
                print("Say something...")

                transcription = self.recognize_speech()
                if transcription:
                    cap.release()
                    cv2.destroyAllWindows()
                    return transcription
            else:
                print("No face detected...")

            cv2.imshow('Frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()