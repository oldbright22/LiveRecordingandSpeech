import threading
import cv2
from PIL import Image
import io
from dotenv import load_dotenv
import os
import tkinter as tk
from gtts import gTTS
import google.generativeai as genai
import google.ai.generativelanguage as glm
from queue import Queue, Empty
from pydub import AudioSegment
import pygame

load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-pro') 
#gemini-pro-vision

class ContentDescriber:
    def __init__(self, root, user_input, video_handler):
        self.root = root
        self.user_input = user_input
        self.video_handler = video_handler
        self.message_var = tk.StringVar()
        self.queue = Queue()
        self.root.after(100, self.process_queue)

        # Initialize pygame mixer
        pygame.mixer.init()

        # Ensure the output directory exists
        self.output_dir = "C:\\Users\\btina\\Documents\\AUDIO"
        os.makedirs(self.output_dir, exist_ok=True)

        # Set the output directory to a subdirectory within the user's home directory
        # self.output_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Temp", "sounds")
        # self.ensure_directory_permissions(self.output_dir)

    def ensure_directory_permissions(self, directory):
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except OSError as e:
                print(f"Error creating directory {directory}: {e}")
                raise
        elif not os.access(directory, os.W_OK):
            try:
                os.chmod(directory, 0o755)
            except OSError as e:
                print(f"Error changing permissions for directory {directory}: {e}")
                raise

    def describe_content(self):
        current_frame = self.video_handler.get_current_frame()
        if current_frame is not None:
            pil_image = Image.fromarray(cv2.cvtColor(current_frame, cv2.COLOR_BGR2RGB))
            img_byte_arr = io.BytesIO()
            pil_image.save(img_byte_arr, format='JPEG')
            blob = glm.Blob(
                mime_type='image/jpeg',
                data=img_byte_arr.getvalue()
            )
            user_request = self.user_input.get()
            response = model.generate_content([user_request, blob], stream=True)
            for chunk in response:
                self.queue.put(chunk.text)
                self.text_to_speech(chunk.text)
        else:
            self.queue.put("No frame available")

    def threaded_describe_content(self):
        describe_thread = threading.Thread(target=self.describe_content)
        describe_thread.start()

    def process_queue(self):
        try:
            while True:
                new_text = self.queue.get_nowait()
                current_text = self.message_var.get()
                updated_text = current_text + new_text + "\n"
                self.message_var.set(updated_text)
        except Empty:
            pass
        self.root.after(100, self.process_queue)

    def text_to_speech(self, text):
        tts = gTTS(text=text, lang='en')
        mp3_path = os.path.join(self.output_dir, 'output.mp3')
        wav_path = os.path.join(self.output_dir, 'output.wav')

        tts.save(mp3_path)
        audio = AudioSegment.from_mp3(mp3_path)
        audio.export(wav_path, format="wav")
        pygame.mixer.music.load(wav_path)
        pygame.mixer.music.play()

# Ensure to install necessary libraries:
# pip install gtts pydub pygame
