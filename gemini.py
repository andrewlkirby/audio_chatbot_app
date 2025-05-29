import os
import io
from dotenv import load_dotenv
import speech_recognition as sr
from google import genai
from google.genai import types
from PyQt5.QtCore import QThread, pyqtSignal
from model import tts_pipeline
import soundfile as sf
import platform
import subprocess

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv('gemini_api_key')

# Gemini model configuration
genai_client = genai.Client(api_key=GEMINI_API_KEY)
configs = types.GenerateContentConfig(max_output_tokens=200, temperature=0.5)
MODEL_NAME = 'gemini-2.0-flash'

class GeminiThread(QThread):
    """Thread for communicating with Google Gemini model and maintaining conversation history."""
    transcription_signal = pyqtSignal(str)
    response_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, prompt: str, audio_bytes=None):
        super().__init__()
        self.prompt = prompt  # full conversation so far, incl. system + menu + history
        self.audio_bytes = audio_bytes

    @staticmethod
    def speech_to_text(audio_bytes):
        recognizer = sr.Recognizer()
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            audio_data = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio_data).strip()
        except (sr.UnknownValueError, sr.RequestError):
            return None

    def get_response(self, prompt_text: str) -> str:
        try:
            stream = genai_client.models.generate_content_stream(
                model=MODEL_NAME,
                contents=[prompt_text],
                config=configs
            )
            return ''.join(chunk.text for chunk in stream)
        except Exception as e:
            return f"Error generating response: {e}"
        
    @staticmethod
    def play_wav_file(filename):
        """
        Plays a WAV audio file using system-specific commands.

        Args:
            filename (str): The path to the WAV file.
        """
        if not os.path.exists(filename):
            print(f"Error: File '{filename}' not found.")
            return

        try:
            if platform.system() == 'Windows':
                subprocess.run(['powershell', '-c', f'Add-Type -AssemblyName System.Media; (New-Object System.Media.SoundPlayer("{filename}")).PlaySync();'], check=True)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['afplay', filename], check=True)
            elif platform.system() == 'Linux':
                try:
                    subprocess.run(['aplay', filename], check=True)
                except FileNotFoundError:
                    try:
                        subprocess.run(['xdg-open', filename], check=True) #try opening with default media player
                    except FileNotFoundError:
                        print ("Error: aplay or xdg-open not found. Please install a sound player.")
                        return
            else:
                print("Error: Unsupported operating system.")
                return
        except subprocess.CalledProcessError as e:
            print(f"Error playing file: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def text_to_speech(self, text: str):
        """Converts text to speech."""
        generator = tts_pipeline(text = text, 
                            voice='af_heart', # <= change voice here
                            speed=1
                            )
        for i, (gs, ps, audio) in enumerate(generator):
            output_path = 'output.wav'
            sf.write(output_path, audio, 24000)
            self.play_wav_file(output_path)
            return output_path

    def run(self):
        try:
            if self.audio_bytes:
                transcription = self.speech_to_text(self.audio_bytes)
                if not transcription:
                    self.response_signal.emit("Sorry, I could not understand the audio.")
                    return
                # Emit transcription and append user turn
                self.transcription_signal.emit(transcription)
                self.prompt += f"Customer: {transcription}\nChatbot: "

            # Generate chatbot reply with full history
            response = self.get_response(self.prompt)
            
            # Append chatbot response to prompt history
            self.prompt += f"{response}\n"
            self.response_signal.emit(response)
            self.text_to_speech(response)

        except Exception as e:
            self.error_signal.emit(f"Error communicating with Gemini: {e}")