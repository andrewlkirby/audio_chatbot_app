import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QDialog, QTabWidget, QPushButton
)
from login import LoginDialog
from user import UserWidget
from admin import AdminWidget

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Restaurant Chatbot")
        self.setGeometry(100, 100, 800, 600)

        self.tab_widget = QTabWidget(self)
        self.login_dialog = LoginDialog(self)
        self.user_widget = UserWidget(self)
        self.admin_widget = None

        self.return_button = QPushButton("Return to Login")
        self.return_button.clicked.connect(self.show_tabs_based_on_login)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.tab_widget)
        self.main_layout.addWidget(self.return_button)  # Add button to layout
        self.setLayout(self.main_layout)

        self.show_tabs_based_on_login()
        self.show()

    def show_tabs_based_on_login(self):
        """Shows the appropriate tabs based on the login result."""
        self.tab_widget.clear()
        self.admin_widget = None  # Clear any existing admin widget

        result = self.login_dialog.exec_()

        if result == QDialog.Accepted:
            self.admin_widget = AdminWidget(self)
            self.admin_widget.pdf_uploaded_signal.connect(self.user_widget.set_pdf_text)

            self.tab_widget.addTab(self.user_widget, "Chat")
            self.tab_widget.addTab(self.admin_widget, "Admin")
            self.tab_widget.setCurrentIndex(1)

        elif result == LoginDialog.BYPASS:
            self.tab_widget.addTab(self.user_widget, "Chat")
            self.tab_widget.setCurrentIndex(0)

        else:
            self.tab_widget.addTab(self.user_widget, "Chat")
            self.tab_widget.setCurrentIndex(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app.exec_())
