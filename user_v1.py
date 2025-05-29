from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, 
    QPushButton, QTextEdit,
    QMessageBox, QSizePolicy, QScrollArea
)
from PyQt5.QtCore import QTimer

import sounddevice as sd
from gemini import GeminiThread
import wave
import io

# User Widget for Gemini Interaction (Improved for clarity, feedback, and error handling)
class UserWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        self.record_button = QPushButton("Push to Talk")  # Push-to-talk button
        self.record_button.setCheckable(True)  # Make it checkable
        self.record_button.toggled.connect(self.handle_record_button)  # Connect to handler
        self.layout.addWidget(self.record_button)

        self.response_label = QLabel("Response:")

        self.scroll_area = QScrollArea()
        self.response_display = QTextEdit()
        self.response_display.setReadOnly(True)
        self.scroll_area.setWidget(self.response_display)
        self.scroll_area.setWidgetResizable(True)

        self.layout.addWidget(self.response_label)
        self.layout.addWidget(self.scroll_area)

        self.gemini_thread = None  # Initialize thread
        self.status_label = QLabel("")  # Add a status label
        self.layout.addWidget(self.status_label)
        self.status_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.pdf_text = ""
        self.audio_data = None  # To store recorded audio data
        self.recording = False
        self.audio_timer = QTimer()
        self.audio_timer.timeout.connect(self.update_audio_status)
        self.audio_duration = 0

    def set_pdf_text(self, pdf_text):
        """Sets the PDF text that will be used as context for Gemini."""
        self.pdf_text = pdf_text

    def send_prompt(self):
        # Create and start the Gemini thread
        self.gemini_thread = GeminiThread(self.pdf_text, self.audio_data)  # Pass pdf_text and audio
        self.gemini_thread.response_signal.connect(self.handle_response)
        self.gemini_thread.error_signal.connect(self.handle_error)  # Connect error signal
        self.gemini_thread.start()
        self.audio_data = None # reset

    def handle_response(self, response):
        self.response_display.setText(response)
        self.send_button.setEnabled(True)  # Re-enable the send button
        self.status_label.setText("Ready.")

    def handle_error(self, error_message):
        """Handles errors from the Gemini thread."""
        QMessageBox.critical(self, "Error", error_message)
        self.response_display.setText(f"Error: {error_message}")
        self.send_button.setEnabled(True)
        self.status_label.setText("Error.")

    def handle_record_button(self, checked):
        """Handles the push-to-talk button state changes."""
        if checked: self.start_recording()
        else: self.stop_recording()

    def start_recording(self):
        """Starts audio recording."""
        self.recording = True
        self.audio_data = []
        self.audio_duration = 0
        self.audio_timer.start(100)  # Update every 100 milliseconds
        self.status_label.setText("Recording...")
        self.record_button.setText("Release to Stop")

        # Get the default recording device's sample rate.
        try: self.sample_rate = sd.query_devices(kind='input')['default_samplerate']
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error querying default sample rate: {e}")
            self.status_label.setText("Error.")
            self.record_button.setChecked(False)  # Ensure button is unchecked.
            self.record_button.setText("Push to Talk")
            return

        self.stream = sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='int16', callback=self.audio_callback)

        try: self.stream.start()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error starting recording: {e}")
            self.status_label.setText("Error.")
            self.record_button.setChecked(False)  # Ensure button is unchecked.
            self.record_button.setText("Push to Talk")
            return

    def stop_recording(self):
        """Stops audio recording."""
        self.recording = False
        self.audio_timer.stop()
        self.status_label.setText("Recording stopped.")
        self.record_button.setText("Push to Talk")
        if hasattr(self, 'stream') and self.stream: # check if stream exists
           self.stream.stop()
           self.stream.close()

        if self.audio_data: self.process_audio_data()  # Process the recorded data
        else: self.status_label.setText("No audio recorded.")

    def audio_callback(self, indata, frames, time, status):
        """Callback function for audio data."""
        if status:
            print(f"Error in audio stream: {status}")
            self.error_signal.emit(f"Error in audio stream: {status}")

        if self.recording: self.audio_data.extend(indata.copy())

    def update_audio_status(self):
        """Updates the audio recording timer display."""
        self.audio_duration += 0.1  # Update every 100ms
        self.status_label.setText(f"Recording: {self.audio_duration:.1f} seconds")

    def process_audio_data(self):
        """Processes the recorded audio data."""
        # Convert the recorded audio data to a format suitable for Gemini.
        # In this case, convert it to a WAV file in memory.
        try:
            # Create an in-memory byte stream.
            
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'w') as wf:
                wf.setnchannels(1)  # Mono audio
                wf.setsampwidth(2)  # 2 bytes per sample (int16)
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(self.audio_data))  # Write the audio data

            self.audio_data = wav_buffer.getvalue() # get the entire WAV data
            self.send_prompt()
            if len(self.audio_data) > 0:
                self.status_label.setText(f"Audio data processed. Length: {len(self.audio_data)} bytes")
            else:
                self.status_label.setText("No audio recorded.")
                self.audio_data = None

        except Exception as e:
            error_message = f"Error processing audio data: {e}"
            QMessageBox.critical(self, "Error", error_message)
            self.status_label.setText(error_message)
            self.audio_data = None