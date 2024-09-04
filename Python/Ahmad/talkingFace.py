import pygame
import time
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
import os

face_pattern_closed = [
    "  *********  ",
    " *         * ",
    "*  **   **  *",
    "*  **   **  *",
    "*           *",
    "*           *",
    "*  *******  *",
    "*           *",
    "*           *",
    " *         * ",
    "  *********  ",
]

face_pattern_open = [
    "  *********  ",
    " *         * ",
    "*  **   **  *",
    "*  **   **  *",
    "*           *",
    "*           *",
    "*   *****   *",
    "*   *   *   *",
    "*   *****   *",
    " *         * ",
    "  *********  ",
]

def create_face_image(face_pattern, text):
    image_size = (400, 400)
    pixel_size = 40
    image = Image.new('RGB', image_size, 'white')
    draw = ImageDraw.Draw(image)
    offset_x = (image_size[0] - pixel_size * len(face_pattern[0])) // 2
    offset_y = (image_size[1] - pixel_size * len(face_pattern)) // 2

    for y, row in enumerate(face_pattern):
        for x, char in enumerate(row):
            if char == '*':
                draw.rectangle([offset_x + x * pixel_size, offset_y + y * pixel_size, offset_x + (x + 1) * pixel_size - 1, offset_y + (y + 1) * pixel_size - 1], fill='black')

    bubble_x, bubble_y, bubble_width, bubble_height = 40, offset_y + pixel_size * len(face_pattern), image_size[0] - 80, 80
    draw.rectangle([bubble_x, bubble_y, bubble_x + bubble_width, bubble_y + bubble_height], fill='white', outline='black')

    try:
        font = ImageFont.truetype("arial.ttf", 25)
    except IOError:
        font = ImageFont.load_default()
    draw.text((bubble_x + 10, bubble_y + 10), text, fill='black', font=font)

    return image

def save_face_images(text):
    face_image_closed = create_face_image(face_pattern_closed, text)
    face_image_closed.save("face_closed.png")
    face_image_open = create_face_image(face_pattern_open, text)
    face_image_open.save("face_open.png")

def generate_audio(text):
    tts = gTTS(text)
    tts.save("audio.mp3")

def animate_face(text):
    pygame.init()
    screen = pygame.display.set_mode((400, 500))
    pygame.display.set_caption("Talking Face")
    face_closed = pygame.image.load("face_closed.png")
    face_open = pygame.image.load("face_open.png")
    pygame.mixer.init()
    pygame.mixer.music.load("audio.mp3")
    pygame.mixer.music.play()
    face_x, face_y = (400 - face_closed.get_width()) // 2, (500 - face_closed.get_height()) // 2
    bubble_y = face_y + face_closed.get_height() + 20

    running, start_time, frame_duration = True, time.time(), 0.2
    while running:
        elapsed_time = time.time() - start_time
        screen.blit(face_open if int(elapsed_time / frame_duration) % 2 else face_closed, (face_x, face_y))
        pygame.display.flip()
        if not pygame.mixer.music.get_busy():
            running = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

    pygame.quit()

def talk(text):
    save_face_images(text)
    generate_audio(text)
    animate_face(text)
    os.remove("face_closed.png")
    os.remove("face_open.png")
    os.remove("audio.mp3")