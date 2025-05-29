import io
import wave
import sounddevice as sd

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import ( QWidget, QVBoxLayout, QLabel,
    QPushButton, QTextEdit, QMessageBox, QSizePolicy, QScrollArea
)
from gemini import GeminiThread

class UserWidget(QWidget):
    """Main user interface for recording and chatting with Gemini."""
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle("Restaurant Chatbot")

        # Layout and widgets
        layout = QVBoxLayout(self)
        # Reset button to restart conversation
        self.reset_button = QPushButton("Reset Conversation")
        self.reset_button.clicked.connect(self.handle_reset)
        layout.addWidget(self.reset_button)

        self.record_button = QPushButton("Push to Talk")
        self.record_button.setCheckable(True)
        self.record_button.toggled.connect(self.on_record_toggled)
        layout.addWidget(self.record_button)

        self.status_label = QLabel("")
        self.status_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        layout.addWidget(self.status_label)

        self.response_display = QTextEdit()
        self.response_display.setReadOnly(True)
        scroll = QScrollArea()
        scroll.setWidget(self.response_display)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        self.response_display.append("Welcome to our restaurant. How may we help you?\n")

        # Internal state
        self.pdf_text = ""
        self.audio_frames = []
        self.sample_rate = None
        self.stream = None
        self.audio_timer = QTimer()
        self.audio_timer.timeout.connect(self.update_recording_time)
        self.recording_time = 0.0

        # Build static system+menu prompt
        self.base_prompt = (
            "You are a restaurant chatbot. You take orders from customers and add your response to the end of the conversation. "
            "Only give responses in plain text. No JSON. Do not include 'Restaurant chatbot'. "
            'If the customer needs to talk to a person or has a weird request, say, "Hmm, OK, I will transfer you to an agent. Bye!"'
            "When the customer is finished, tell them the price, when their order will be ready, and say, 'Have a great day!'.\n"
        )
        self.menu_text = None
        self.reset_conversation()

    def handle_reset(self):
        """Resets conversation to initial state."""
        self.reset_conversation()
        # Show greeting again
        self.response_display.append("Welcome to our restaurant. How may we help you?\n")

    def reset_conversation(self):
        # Initialize conversation history
        self.prompt_history = self.base_prompt
        if self.menu_text:
            self.prompt_history += f"Menu:\n{self.menu_text}\n"
        else:
            # fallback menu
            fallback = {"pizza":12.99, "burger":8.99, "salad":7.99, "pasta":10.99, "fries":3.99, "coke":1.99, "sprite":1.99}
            self.prompt_history += f"Menu:\n{fallback}\n"
        # Clear display when starting over
        self.response_display.clear()

    def set_pdf_text(self, text: str):
        """Loads menu text from admin and resets."""
        self.menu_text = text
        self.reset_conversation()
        self.response_display.append("📖 Menu loaded! You can now place your order.")

    def on_record_toggled(self, checked: bool):
        if checked: self.start_recording()
        else: self.stop_recording()

    def start_recording(self):
        # Reset and start
        self.audio_frames = []
        self.recording_time = 0.0
        self.audio_timer.start(100)
        self.status_label.setText("Recording... 0.0s")
        self.record_button.setText("Release to Stop")

        try:
            self.sample_rate = sd.query_devices(kind='input')['default_samplerate']
            self.stream = sd.InputStream(
                samplerate=int(self.sample_rate), channels=1, dtype='int16', callback=self.audio_callback
            )
            self.stream.start()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Recording error: {e}")
            self.cleanup_after_error()

    def stop_recording(self):
        # Stop recording
        self.audio_timer.stop()
        self.status_label.setText("Processing audio...")
        self.record_button.setText("Push to Talk")
        if self.stream:
            self.stream.stop()
            self.stream.close()

        # Convert frames to WAV and send
        try:
            buffer = io.BytesIO()
            with wave.open(buffer, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(int(self.sample_rate))
                wf.writeframes(b''.join(self.audio_frames))
            audio_bytes = buffer.getvalue()
            self.send_to_gemini(audio_bytes)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error processing audio: {e}")
            self.status_label.setText("Error processing audio.")

    def update_recording_time(self):
        self.recording_time += 0.1
        self.status_label.setText(f"Recording... {self.recording_time:.1f}s")

    def audio_callback(self, indata, frames, time, status):
        if status: print(f"Audio status: {status}")
        self.audio_frames.append(indata.tobytes())

    def send_to_gemini(self, audio_bytes: bytes):
        self.record_button.setEnabled(False)
        self.status_label.setText("Waiting for response...")
        # Pass full history to GeminiThread
        thread = GeminiThread(self.prompt_history, audio_bytes)
        thread.transcription_signal.connect(self.display_transcription)
        thread.response_signal.connect(lambda resp, th=thread: self.display_response(resp, th))
        thread.error_signal.connect(self.display_error)
        thread.start()

    def display_transcription(self, transcription: str):
        self.response_display.append(f"You said: {transcription}")

    def display_response(self, text: str, thread: GeminiThread):
        self.response_display.append(f"\n{text}")
        self.prompt_history = thread.prompt
        self.status_label.setText("Ready.")
        self.record_button.setEnabled(True)
        self.record_button.setChecked(False)

    def display_error(self, error_msg: str):
        QMessageBox.critical(self, "Error", error_msg)
        self.status_label.setText("Error.")
        self.record_button.setEnabled(True)
        self.record_button.setChecked(False)

    def cleanup_after_error(self):
        self.audio_timer.stop()
        self.record_button.setChecked(False)