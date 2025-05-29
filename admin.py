from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QTextEdit, QStackedWidget,
    QMessageBox, QDialog, QFormLayout, QComboBox,
    QProgressBar, QSizePolicy, QScrollArea, QTabWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl, QTimer

from pdf_to_text import from_pdf


# Admin Widget for PDF Upload (Improved for feedback and error handling)
class AdminWidget(QWidget):
    pdf_uploaded_signal = pyqtSignal(str)  # Signal to send PDF path

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        self.upload_button = QPushButton("Upload PDF File")
        self.upload_button.clicked.connect(self.upload_pdf)
        self.layout.addWidget(self.upload_button)

        self.pdf_label = QLabel("No PDF file selected")
        self.layout.addWidget(self.pdf_label)

        self.status_label = QLabel("")  # For status messages
        self.layout.addWidget(self.status_label)
        self.status_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        self.progress_bar = QProgressBar(self)  # Progress bar for file operations
        self.progress_bar.setVisible(False)  # Initially hide the progress bar
        self.layout.addWidget(self.progress_bar)

    def upload_pdf(self):
        """
        Opens a file dialog to select a PDF, extracts the text,
        and emits a signal with the PDF path.
        """
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select PDF File", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if file_path:
            self.status_label.setText("Processing PDF...")  # set status
            # Use a QThread or a similar mechanism for long operations
            # to prevent freezing the GUI. For simplicity of this example,
            # we'll do it in the main thread, but this is NOT recommended
            # for large files or complex processing.
            try:
                global PDF_FILE_PATH  # Update the global variable
                PDF_FILE_PATH = file_path
                self.pdf_label.setText(f"Selected PDF: {file_path}")
                pdf_text = from_pdf(file_path)
                self.pdf_uploaded_signal.emit(pdf_text)
                self.status_label.setText("PDF uploaded and processed.")
            except Exception as e:
                error_message = f"Error uploading/processing PDF: {e}"
                self.status_label.setText(error_message)
                self.progress_bar.setVisible(False)
                QMessageBox.critical(self, "Error", error_message)