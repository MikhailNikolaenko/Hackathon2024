import pyaudio
import numpy as np

# Initialize PyAudio
p = pyaudio.PyAudio()

# List all available audio input devices
print("Available audio input devices:")
for i in range(p.get_device_count()):
    device_info = p.get_device_info_by_index(i)
    if device_info['maxInputChannels'] > 0:
        print(f"Device {i}: {device_info['name']}")

# Set the device index for the desired microphone
device_index = int(input("Enter the device index for the desired microphone: "))

# PyAudio parameters
FORMAT = pyaudio.paInt16  # Audio format
CHANNELS = 1              # Mono
RATE = 44100              # Sampling rate
CHUNK = 1024              # Buffer size

# Open the stream with the selected device
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=CHUNK)

# Define a threshold level for detecting speech
THRESHOLD = 500  # Adjust this value based on your requirements

print("Listening...")

try:
    while True:
        # Read raw microphone data
        data = stream.read(CHUNK)
        
        # Convert data to numpy array
        audio_data = np.frombuffer(data, dtype=np.int16)
        
        # Compute the RMS (root mean square) amplitude
        rms = np.sqrt(np.mean(audio_data**2))
        
        # Check if the RMS amplitude exceeds the threshold
        if rms > THRESHOLD:
            print("Speaking detected!")
        else:
            print("Silence")

except KeyboardInterrupt:
    print("Stopping...")
finally:
    # Close the stream and PyAudio
    stream.stop_stream()
    stream.close()
    p.terminate()