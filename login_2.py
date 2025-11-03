from PyQt6.QtWidgets import (
    QDialog, QMessageBox, QLineEdit, QLabel,
    QVBoxLayout, QWidget, QFormLayout, QPushButton, QHBoxLayout, QFrame
)
from PyQt6.QtCore import Qt
import sqlite3
import hashlib # хеширование паролей
import re # регулярные выражение

# Импортируем главное окно приложения
from main_window_2 import MainWindow

EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$") # сырая строка r - чтобы не экранировалось
                                                  # (\. - просто точка, иначе был бы \. - любой символ)

class Line(QWidget):
    def __init__(self):
        super().__init__() # super().__init__() - вызов конструктора родительского класса QWidget
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine) # Задаем форму рамки как горизонтальную линию
        line.setFrameShadow(QFrame.Shadow.Sunken) # линия утоплённая (не такая яркая)
        line.setStyleSheet("background-color: #FF69B4; border: 1px solid #FF69B9;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 8, 0, 8) # 8px над и под линией
        lay.addWidget(line)


class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.login_edit = None
        self.pass_edit = None
        self.main_window = None
        self.setWindowTitle("Авторизация")
        self.resize(400, 300)
        self.conn = sqlite3.connect('library.db')
        self.conn.row_factory = sqlite3.Row
        self.setup_ui()


    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Вход в систему")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:18px; font-weight:600;") # размер и насыщенность (полужирный) шрифта
        layout.addWidget(title)
        layout.addWidget(Line())

        form_layout = QFormLayout()

        self.login_edit = QLineEdit() # однострочное поле ввода текста
        self.login_edit.setPlaceholderText("Логин или email") # текст - подсказка
        self.pass_edit = QLineEdit()
        self.pass_edit.setPlaceholderText("Пароль")
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)

        form_layout.addRow("Логин / Email:", self.login_edit)
        form_layout.addRow("Пароль:", self.pass_edit)

        layout.addLayout(form_layout)
        layout.addSpacing(16) # просто + 16px вниз (между полями ввода и кнопками)

        buttons_layout = QHBoxLayout()

        btn_login = QPushButton("Войти")
        btn_login.clicked.connect(self.handle_login)
        btn_register = QPushButton("Зарегистрироваться")
        btn_register.clicked.connect(self.show_register)

        buttons_layout.addWidget(btn_login)
        buttons_layout.addWidget(btn_register)

        layout.addLayout(buttons_layout)
        layout.addStretch() # добавляет растягивающийся элемент, который занимает всё доступное пространство

    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()


    def verify_password(self, password: str, hash_hex: str) -> bool:
        computed = self.hash_password(password) # вызывает метод хеша для пароля
        return computed == hash_hex


    def find_user_by_login_or_email(self, login: str):
        cur = self.conn.execute(
            "SELECT * FROM Users WHERE username = ? OR email = ?",
            (login.strip(), login.strip())
        )
        return cur.fetchone() # получает одну строку результата (первую найденную)


    def create_user(self, username: str, email: str, password: str) -> None:
        if len(username.strip()) < 3:
            raise ValueError("Логин должен быть не короче 3 символов.")
        if len(password) < 6:
            raise ValueError("Пароль должен быть не короче 6 символов.")
        if not EMAIL_REGEX.match(email.strip()):
            raise ValueError("Введите корректный email-адрес.")

        existing_user = self.conn.execute(
            "SELECT * FROM Users WHERE username = ? OR email = ?",
            (username.strip(), email.strip())
        ).fetchone()

        if existing_user:
            if existing_user['username'] == username.strip():
                raise ValueError("Пользователь с таким логином уже существует.")
            else:
                raise ValueError("Пользователь с таким email уже существует.")

        h = self.hash_password(password)
        self.conn.execute(
            "INSERT INTO Users (username, email, password_hash) VALUES (?, ?, ?)",
            (username.strip(), email.strip(), h)
        )
        self.conn.commit()


    def handle_login(self):
        login = self.login_edit.text().strip()
        password = self.pass_edit.text()

        if not login or not password:
            QMessageBox.warning(self, "Внимание", "Введите логин/email и пароль.")
            return

        user = self.find_user_by_login_or_email(login)
        if not user:
            QMessageBox.critical(self, "Ошибка входа", "Пользователь не найден.")
            return

        if not self.verify_password(password, user["password_hash"]):
            QMessageBox.critical(self, "Ошибка входа", "Неверный пароль.")
            return

        QMessageBox.information(self, 'Успех!', 'Добро пожаловать')

        if hasattr(self, 'conn'): # чисто перестраховка
            self.conn.close()

        self.close()
        self.open_main_window(user["user_id"], user["username"])


    def show_register(self):
        dialog = RegisterDialog(self)
        result = dialog.exec() # сохраняет результат: Accepted (OK) или Rejected (Отмена)
        if result == QDialog.DialogCode.Accepted:
            # После успешной регистрации очищаем поля и предлагаем войти
            self.login_edit.clear()
            self.pass_edit.clear()
            QMessageBox.information(self, "Успех", "Аккаунт создан. Теперь войдите.")

    def open_main_window(self, user_id, username):
        self.main_window = MainWindow(username=username, user_id=user_id)
        self.main_window.show()

    def closeEvent(self, event): # Автоматически вызывается при закрытии окна (крестик), закрываем соединение с бд
        if hasattr(self, 'conn'):
            self.conn.close()
        super().closeEvent(event) # Вызывает родительский метод closeEvent, без этого окно может закрываться некорректно


class RegisterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent) # в нашем случае LoginWindow
        self.username_edit = None
        self.email_edit = None
        self.pass1_edit = None
        self.pass2_edit = None
        self.parent = parent
        self.setWindowTitle("Регистрация")
        self.resize(400, 350)
        self.setup_ui()


    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Регистрация")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:18px; font-weight:600;")
        layout.addWidget(title)
        layout.addWidget(Line())

        form_layout = QFormLayout()

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Логин")
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Email")
        self.pass1_edit = QLineEdit()
        self.pass1_edit.setPlaceholderText("Пароль")
        self.pass1_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass2_edit = QLineEdit()
        self.pass2_edit.setPlaceholderText("Повторите пароль")
        self.pass2_edit.setEchoMode(QLineEdit.EchoMode.Password)

        form_layout.addRow("Логин:", self.username_edit)
        form_layout.addRow("Email:", self.email_edit)
        form_layout.addRow("Пароль:", self.pass1_edit)
        form_layout.addRow("Повтор пароля:", self.pass2_edit)

        layout.addLayout(form_layout)
        layout.addSpacing(16)

        buttons_layout = QHBoxLayout()

        btn_create = QPushButton("Создать аккаунт")
        btn_create.clicked.connect(self.handle_register)
        btn_back = QPushButton("Назад")
        btn_back.clicked.connect(self.reject)

        buttons_layout.addWidget(btn_create)
        buttons_layout.addWidget(btn_back)

        layout.addLayout(buttons_layout)
        layout.addStretch()


    def handle_register(self):
        username = self.username_edit.text().strip()
        email = self.email_edit.text().strip()
        password1 = self.pass1_edit.text()
        password2 = self.pass2_edit.text()

        if not username or not email or not password1 or not password2:
            QMessageBox.warning(self, "Внимание", "Заполните все поля.")
            return

        if password1 != password2:
            QMessageBox.critical(self, "Ошибка", "Пароли не совпадают.")
            return

        try:
            self.parent.create_user(username, email, password1)
            QMessageBox.information(self, "Успех", "Аккаунт успешно создан!")
            self.accept() # это как сказать "Всё хорошо, закрывай окно".
        except ValueError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка базы данных", f"Не удалось создать пользователя: {str(e)}")