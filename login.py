from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QTextEdit, QStackedWidget,
    QMessageBox, QDialog, QFormLayout, QComboBox,
    QProgressBar, QSizePolicy, QScrollArea, QTabWidget
)
from PyQt5.QtGui import QFont, QPixmap, QImage
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl, QTimer

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"

# Login Dialog (Improved for clarity and error handling)
class LoginDialog(QDialog):
    BYPASS = 1000

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        self.layout = QFormLayout(self)

        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        self.layout.addRow(self.username_label, self.username_input)

        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.layout.addRow(self.password_label, self.password_input)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.check_login)
        self.layout.addRow(self.login_button)

        self.bypass_button = QPushButton("Bypass Login")  # Add Bypass Button
        self.bypass_button.clicked.connect(self.bypass_login)
        self.layout.addRow(self.bypass_button)

        self.error_label = QLabel("")  # Add a label for error messages
        self.error_label.setStyleSheet("color: red;")
        self.layout.addRow(self.error_label)

    def check_login(self):
        print("Login button clicked.")
        username = self.username_input.text()
        password = self.password_input.text()

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            print("Login successful.")
            self.accept()
        else:
            print("Login failed.")
            self.error_label.setText("Incorrect username or password.")


    def bypass_login(self):
        print("Bypass login button clicked.")
        self.done(LoginDialog.BYPASS)
