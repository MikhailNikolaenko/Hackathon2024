import speech_recognition as sr
import numpy as np

# Lower the threshold for testing
THRESHOLD = 10  # Volume threshold for detecting speech

# Initialize the recognizer
recognizer = sr.Recognizer()

# Function to determine if someone is talking
def is_talking(audio_data, threshold):
    # Convert audio_data to numpy array
    audio_array = np.frombuffer(audio_data.get_raw_data(), dtype=np.int16)
    # Calculate the root mean square (RMS) volume
    volume = np.sqrt(np.mean(audio_array**2))
    #print(f"Volume: {volume}")  # Print the volume level for debugging
    return volume > threshold

# Use the default microphone as the audio source
with sr.Microphone() as source:
    print("Adjusting for ambient noise, please wait...")
    recognizer.adjust_for_ambient_noise(source, duration=5)
    print("Listening for speech...")

    try:
        while True:
            print("Say something...")

            # Capture audio data from the microphone
            audio_data = recognizer.listen(source)
            #print("Audio data captured")  # Debugging statement

            # Check if someone is talking
            if is_talking(audio_data, THRESHOLD):
                #print("Someone is talking...")

                try:
                    # Recognize speech using Google Web Speech API
                    transcription = recognizer.recognize_google(audio_data)
                    print("Transcription:", transcription)
                except sr.UnknownValueError:
                    print("Could not understand audio")
                except sr.RequestError as e:
                    print(f"Could not request results; {e}")
                except Exception as e:
                    print(f"An error occurred during transcription: {e}")
            else:
                print("Silence...")

    except KeyboardInterrupt:
        print("Stopping...")
