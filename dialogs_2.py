from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QTextEdit, QComboBox,
    QVBoxLayout, QLabel, QCheckBox, QDialogButtonBox, QMessageBox,
    QScrollArea, QWidget, QDateEdit, QDoubleSpinBox, QSpinBox, QTabWidget,
    QPushButton, QFrame, QHBoxLayout, QGroupBox, QInputDialog
)
from PyQt6.QtCore import Qt, QDate
import sqlite3

class AddBookDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Добавление книги")
        self.authors_widgets = []  # Список хранит словари с виджетами каждого автора для управления ими
        layout = QVBoxLayout(self)

        # поля книги
        form_layout = QFormLayout()
        self.title_edit = QLineEdit()
        form_layout.addRow("Название:*", self.title_edit)

        # секция авторов
        authors_group = QGroupBox("Авторы")
        authors_layout = QVBoxLayout(authors_group)
        # первый автор
        self.add_author_fields(authors_layout)
        # Кнопка добавления автора
        btn_add_author = QPushButton("+ Добавить автора")
        btn_add_author.clicked.connect(lambda: self.add_author_fields(authors_layout))
        authors_layout.addWidget(btn_add_author)

        form_layout.addRow(authors_group)

        # остальные поля книги
        self.cover_edit = QLineEdit()
        self.publication_year_edit = QLineEdit()
        self.page_count_edit = QLineEdit()
        self.summary_edit = QTextEdit()
        self.summary_edit.setMaximumHeight(100)

        self.status_combo = QComboBox()
        self.status_combo.addItems(['Запланировано', 'Прочитано', 'Читаю', 'Заброшено'])

        form_layout.addRow("Обложка (путь):", self.cover_edit)
        form_layout.addRow("Год издания:", self.publication_year_edit)
        form_layout.addRow("Количество страниц:", self.page_count_edit)
        form_layout.addRow("Статус чтения:*", self.status_combo)
        form_layout.addRow("Описание:", self.summary_edit)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Сохранить')
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('Закрыть')
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


    def add_author_fields(self, layout):
        author_widget = QWidget()
        author_layout = QHBoxLayout(author_widget)

        last_name = QLineEdit()
        last_name.setPlaceholderText("Фамилия")
        first_name = QLineEdit()
        first_name.setPlaceholderText("Имя")
        middle_name = QLineEdit()
        middle_name.setPlaceholderText("Отчество")

        btn_remove = QPushButton("×")
        btn_remove.setFixedSize(30, 30)
        btn_remove.clicked.connect(lambda: self.remove_author(author_widget))

        author_layout.addWidget(QLabel("Фамилия:*"))
        author_layout.addWidget(last_name)
        author_layout.addWidget(QLabel("Имя:*"))
        author_layout.addWidget(first_name)
        author_layout.addWidget(QLabel("Отчество:"))
        author_layout.addWidget(middle_name)
        author_layout.addWidget(btn_remove)

        layout.addWidget(author_widget)

        # сохраняем виджеты для доступа ко всем данным
        self.authors_widgets.append({
            'widget': author_widget,
            'last_name': last_name,
            'first_name': first_name,
            'middle_name': middle_name
        })


    def remove_author(self, author_widget):
        for author_data in self.authors_widgets[:]:
            if author_data['widget'] == author_widget:
                author_widget.setParent(None) # удаляем виджет из интерфейса
                self.authors_widgets.remove(author_data)
                break


    def validate_and_accept(self):
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Название книги обязательно!")
            return

        for i, author_data in enumerate(self.authors_widgets):
            if not author_data['last_name'].text().strip() or not author_data['first_name'].text().strip():
                QMessageBox.warning(self, "Ошибка", f"У автора #{i + 1} заполните фамилию и имя!")
                return
        current_year = QDate.currentDate().year()
        publication_year_text = self.publication_year_edit.text().strip()

        if publication_year_text and publication_year_text.isdigit():
            publication_year = int(publication_year_text)
            if publication_year > current_year:
                QMessageBox.warning(self, "Ошибка",
                                    f"Год издания не может быть больше текущего ({current_year})!")
                return

        current_date = QDate.currentDate()

        if hasattr(self,
                   'acquisition_date_edit') and self.acquisition_date_edit.date().isValid() and self.acquisition_date_edit.date() > current_date:
            QMessageBox.warning(self, "Ошибка", "Дата приобретения не может быть в будущем!")
            return

        if hasattr(self,
                   'start_date_edit') and self.start_date_edit.date().isValid() and self.start_date_edit.date() > current_date:
            QMessageBox.warning(self, "Ошибка", "Дата начала чтения не может быть в будущем!")
            return

        if hasattr(self, 'end_date_edit') and self.end_date_edit.date().isValid():
            if self.end_date_edit.date() > current_date:
                QMessageBox.warning(self, "Ошибка", "Дата окончания чтения не может быть в будущем!")
                return

            if (hasattr(self, 'start_date_edit') and
                    self.start_date_edit.date().isValid() and
                    self.end_date_edit.date() < self.start_date_edit.date()):
                QMessageBox.warning(self, "Ошибка", "Дата окончания чтения не может быть раньше даты начала!")
                return

        self.accept()


    def get_data(self):
        authors = []
        for author_data in self.authors_widgets:
            authors.append({
                'last_name': author_data['last_name'].text().strip(),
                'first_name': author_data['first_name'].text().strip(),
                'middle_name': author_data['middle_name'].text().strip() or None
            })

        return {
            'title': self.title_edit.text().strip(),
            'authors': authors,
            'cover': self.cover_edit.text().strip() or None,
            'status': self.status_combo.currentText(),
            'publication_year': int(
                self.publication_year_edit.text()) if self.publication_year_edit.text().isdigit() else None,
            'page_count': int(self.page_count_edit.text()) if self.page_count_edit.text().isdigit() else None,
            'summary': self.summary_edit.toPlainText().strip() or None
        }


class AddCollectionDialog(QDialog):
    def __init__(self, books):
        super().__init__()
        self.setWindowTitle("Добавление коллекции")
        self.books = books
        self.selected_books = []

        layout = QVBoxLayout(self)

        self.name_edit = QLineEdit()
        layout.addWidget(QLabel("Название коллекции:*"))
        layout.addWidget(self.name_edit)

        layout.addWidget(QLabel("Выберите книги для коллекции:"))

        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        self.checkboxes = []
        for book in books:
            cb = QCheckBox(f"{book['title']} ({book.get('authors', '')})")
            self.checkboxes.append(cb)
            scroll_layout.addWidget(cb)

        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(300)
        layout.addWidget(scroll_area)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Сохранить')
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('Закрыть')
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


    def validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Название коллекции обязательно!")
            return
        self.accept()


    def get_data(self):
        selected = [book['book_id'] for cb, book in zip(self.checkboxes, self.books) if cb.isChecked()] # zip объединяет два списка в пары
        return {
            'name': self.name_edit.text(),
            'books': selected
        }


class SearchDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Поиск")
        layout = QFormLayout(self)

        self.title_edit = QLineEdit()
        self.author_edit = QLineEdit()

        layout.addRow("Название содержит:", self.title_edit)
        layout.addRow("Автор содержит:", self.author_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Сохранить')
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('Закрыть')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


    def get_criteria(self):
        return {
            'title': self.title_edit.text(),
            'author': self.author_edit.text()
        }


class ExtendedBookInfoDialog(QDialog):
    def __init__(self, book_data, db_instance): # принимает книги и экземпляр бд
        super().__init__()
        self.book_data = book_data
        self.db = db_instance

        self.title_edit = None
        self.authors_layout_inner = None
        self.authors_widgets = None
        self.genres_scroll = None
        self.genres_widget = None
        self.genres_layout = None
        self.cover_edit = None
        self.publication_year_edit = None
        self.page_count_edit = None
        self.status_combo = None
        self.summary_edit = None
        self.language_edit = None
        self.publisher_combo = None
        self.acquisition_date_edit = None
        self.price_edit = None
        self.start_date_edit = None
        self.end_date_edit = None
        self.current_page_edit = None
        self.genre_checkboxes = None

        self.setWindowTitle(f"Расширенная информация: {book_data['title']}")
        self.resize(600, 500)

        self.setup_ui()

        # загружаем отдельно, потому что списки издательств и жанров не зависят от конкретной книги
        self.load_publishers()
        self.load_genres()

        self.load_data()


    def setup_ui(self):
        layout = QVBoxLayout(self)

        tabs = QTabWidget() # вкладки: основная информация и чтение

        basic_tab = QWidget()
        basic_layout = QFormLayout(basic_tab)

        self.title_edit = QLineEdit()
        basic_layout.addRow("Название:*", self.title_edit)

        # секция авторов
        authors_group = QGroupBox("Авторы")
        self.authors_layout_inner = QVBoxLayout(authors_group)
        self.authors_widgets = []
        self.add_author_fields(self.authors_layout_inner)
        btn_add_author = QPushButton("+ Добавить автора")
        btn_add_author.clicked.connect(lambda: self.add_author_fields(self.authors_layout_inner))
        self.authors_layout_inner.addWidget(btn_add_author)
        basic_layout.addRow(authors_group)

        genres_group = QGroupBox("Жанры")
        genres_layout = QVBoxLayout(genres_group)

        self.genres_scroll = QScrollArea()
        self.genres_widget = QWidget()
        self.genres_layout = QVBoxLayout(self.genres_widget)
        self.genres_scroll.setWidget(self.genres_widget)
        self.genres_scroll.setWidgetResizable(True)
        self.genres_scroll.setMaximumHeight(150)
        btn_add_genre = QPushButton("Добавить жанр")
        btn_add_genre.clicked.connect(self.add_new_genre)
        genres_layout.addWidget(self.genres_scroll)
        genres_layout.addWidget(btn_add_genre)
        basic_layout.addRow(genres_group)

        self.cover_edit = QLineEdit()
        self.publication_year_edit = QLineEdit()
        self.page_count_edit = QLineEdit()

        self.status_combo = QComboBox()
        self.status_combo.addItems(['Запланировано', 'Прочитано', 'Читаю', 'Заброшено'])

        self.summary_edit = QTextEdit()
        self.summary_edit.setMaximumHeight(100)

        basic_layout.addRow("Обложка (путь):", self.cover_edit)
        basic_layout.addRow("Год издания:", self.publication_year_edit)
        basic_layout.addRow("Количество страниц:", self.page_count_edit)
        basic_layout.addRow("Статус чтения:*", self.status_combo)  # ← ДОБАВЛЯЕМ СТАТУС
        basic_layout.addRow("Описание:", self.summary_edit)

        self.language_edit = QLineEdit()
        publisher_layout = QHBoxLayout()
        self.publisher_combo = QComboBox()
        btn_add_publisher = QPushButton("+")
        btn_add_publisher.clicked.connect(self.add_new_publisher)
        publisher_layout.addWidget(self.publisher_combo)
        publisher_layout.addWidget(btn_add_publisher)

        basic_layout.addRow("Язык:", self.language_edit)
        basic_layout.addRow("Издательство:", publisher_layout)

        # информация о чтении
        reading_tab = QWidget()
        reading_layout = QFormLayout(reading_tab)

        self.acquisition_date_edit = QDateEdit() # виджет выбора даты
        self.acquisition_date_edit.setCalendarPopup(True) # всплывающий календарь при нажатии
        self.acquisition_date_edit.setDate(QDate())

        self.price_edit = QDoubleSpinBox()
        self.price_edit.setRange(0, 100000)
        self.price_edit.setPrefix("₽ ")
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.current_page_edit = QSpinBox()
        self.current_page_edit.setRange(0, 10000)

        reading_layout.addRow("Дата приобретения:", self.acquisition_date_edit)
        reading_layout.addRow("Цена:", self.price_edit)
        reading_layout.addRow("Дата начала чтения:", self.start_date_edit)
        reading_layout.addRow("Дата окончания:", self.end_date_edit)
        reading_layout.addRow("Текущая страница:", self.current_page_edit)

        # добавляем вкладки
        tabs.addTab(basic_tab, "Основная информация")
        tabs.addTab(reading_tab, "Чтение")

        layout.addWidget(tabs)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Сохранить')
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('Закрыть')
        buttons.accepted.connect(self.validate_and_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


    def add_author_fields(self, layout):
        author_widget = QWidget()
        author_layout = QHBoxLayout(author_widget)

        last_name = QLineEdit()
        last_name.setPlaceholderText("Фамилия*")
        first_name = QLineEdit()
        first_name.setPlaceholderText("Имя*")
        middle_name = QLineEdit()
        middle_name.setPlaceholderText("Отчество")

        btn_remove = QPushButton("×")
        btn_remove.setFixedSize(30, 30)
        btn_remove.clicked.connect(lambda: self.remove_author(author_widget))

        author_layout.addWidget(QLabel("Фамилия:"))
        author_layout.addWidget(last_name)
        author_layout.addWidget(QLabel("Имя:"))
        author_layout.addWidget(first_name)
        author_layout.addWidget(QLabel("Отчество:"))
        author_layout.addWidget(middle_name)
        author_layout.addWidget(btn_remove)

        layout.addWidget(author_widget)

        self.authors_widgets.append({
            'widget': author_widget,
            'last_name': last_name,
            'first_name': first_name,
            'middle_name': middle_name
        })


    def remove_author(self, author_widget):
        for author_data in self.authors_widgets[:]:
            if author_data['widget'] == author_widget:
                author_widget.setParent(None)
                self.authors_widgets.remove(author_data)
                break


    def validate_and_save(self):
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Название книги обязательно!")
            return

        for i, author_data in enumerate(self.authors_widgets):
            if not author_data['last_name'].text().strip() or not author_data['first_name'].text().strip():
                QMessageBox.warning(self, "Ошибка", f"У автора #{i + 1} заполните фамилию и имя!")
                return

        current_year = QDate.currentDate().year()
        publication_year_text = self.publication_year_edit.text().strip()

        if publication_year_text and publication_year_text.isdigit():
            publication_year = int(publication_year_text)
            if publication_year > current_year:
                QMessageBox.warning(self, "Ошибка", f"Год издания не может быть больше текущего ({current_year})!")
                return

        current_date = QDate.currentDate()

        if self.acquisition_date_edit.date().isValid() and self.acquisition_date_edit.date() > current_date:
            QMessageBox.warning(self, "Ошибка", "Дата приобретения не может быть в будущем!")
            return

        if self.start_date_edit.date().isValid() and self.start_date_edit.date() > current_date:
            QMessageBox.warning(self, "Ошибка", "Дата начала чтения не может быть в будущем!")
            return

        if self.end_date_edit.date().isValid():
            if self.end_date_edit.date() > current_date:
                QMessageBox.warning(self, "Ошибка", "Дата окончания чтения не может быть в будущем!")
                return

            if self.start_date_edit.date().isValid() and self.end_date_edit.date() < self.start_date_edit.date():
                QMessageBox.warning(self, "Ошибка", "Дата окончания чтения не может быть раньше даты начала!")
                return

        self.save_data()


    def get_connection(self):
        return self.db.conn


    def load_publishers(self):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT publisher_id, name FROM Publisher ORDER BY name")
        publishers = cur.fetchall()

        current_publisher_id = self.publisher_combo.currentData()

        self.publisher_combo.clear()
        self.publisher_combo.addItem("Не выбрано", None)

        current_index = 0
        for publisher in publishers:
            self.publisher_combo.addItem(publisher['name'], publisher['publisher_id'])
            if publisher['publisher_id'] == current_publisher_id:
                current_index = self.publisher_combo.count() - 1

        self.publisher_combo.setCurrentIndex(current_index)


    def load_genres(self):
        try:
            conn = self.get_connection()
            cur = conn.cursor()

            cur.execute("SELECT genre_id, name FROM Genre ORDER BY name")
            all_genres = cur.fetchall()

            # получаем выбранные жанры для книги
            cur.execute("""
                SELECT g.genre_id FROM Genre g
                JOIN BookGenre bg ON g.genre_id = bg.genre_id
                WHERE bg.book_id = ?
            """, (self.book_data['book_id'],))
            selected_genres = [row['genre_id'] for row in cur.fetchall()]

            for i in reversed(range(self.genres_layout.count())):
                widget = self.genres_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)

            # Создаем чекбоксы для жанров
            self.genre_checkboxes = {}
            for genre in all_genres:
                cb = QCheckBox(genre['name'])
                cb.setChecked(genre['genre_id'] in selected_genres)
                self.genre_checkboxes[genre['genre_id']] = cb
                self.genres_layout.addWidget(cb)

            self.genres_layout.addStretch()

        except Exception as e:
            print(f"Error loading genres: {e}")


    def load_data(self):
        conn = self.get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT title, cover_image, publication_year, page_count, summary, 
                   language, publisher_id
            FROM Book WHERE book_id = ?
        """, (self.book_data['book_id'],))
        book_info = cur.fetchone()

        if book_info:
            self.title_edit.setText(book_info['title'] or '')
            self.cover_edit.setText(book_info['cover_image'] or '')
            self.language_edit.setText(book_info['language'] or '')
            self.publication_year_edit.setText(
                str(book_info['publication_year']) if book_info['publication_year'] else '')
            self.page_count_edit.setText(str(book_info['page_count']) if book_info['page_count'] else '')
            self.summary_edit.setPlainText(book_info['summary'] or '')

            if book_info['publisher_id']: # если у книги есть издательство
                index = self.publisher_combo.findData(book_info['publisher_id']) # есть ID издательства, ищем это издательство в комбобоксе
                if index >= 0:
                    self.publisher_combo.setCurrentIndex(index)

        cur.execute("SELECT reading_status FROM BookCopy WHERE book_id = ?", (self.book_data['book_id'],))
        status_info = cur.fetchone()
        if status_info:
            index = self.status_combo.findText(status_info['reading_status']) # ищет текст статуса в выпадающем списке
            if index >= 0:
                self.status_combo.setCurrentIndex(index)

        cur.execute("""
            SELECT a.first_name, a.last_name, a.middle_name
            FROM Author a
            JOIN BookAuthor ba ON a.author_id = ba.author_id
            WHERE ba.book_id = ?
        """, (self.book_data['book_id'],))
        authors = cur.fetchall()

        # очищаем существующие поля авторов
        for author_data in self.authors_widgets[:]: # нет проблем с индексами, не reverse
            author_data['widget'].setParent(None)
        self.authors_widgets.clear() # очищаем список ссылок на виджеты

        for author in authors:
            self.add_author_fields(self.authors_layout_inner)
            last_widget = self.authors_widgets[-1]
            last_widget['last_name'].setText(author['last_name'] or '')
            last_widget['first_name'].setText(author['first_name'] or '')
            last_widget['middle_name'].setText(author['middle_name'] or '')


        cur.execute("""
            SELECT acquisition_date, price, start_date, end_date, current_page
            FROM BookCopy WHERE book_id = ?
        """, (self.book_data['book_id'],))
        copy_info = cur.fetchone()

        if copy_info:
            if copy_info['acquisition_date']:
                try:
                    date = QDate.fromString(copy_info['acquisition_date'], 'yyyy-MM-dd') # преобразует строку в дату
                    if date.isValid():
                        self.acquisition_date_edit.setDate(date)
                except:
                    pass

            if copy_info['price']:
                self.price_edit.setValue(float(copy_info['price']))

            if copy_info['start_date']:
                try:
                    date = QDate.fromString(copy_info['start_date'], 'yyyy-MM-dd')
                    if date.isValid():
                        self.start_date_edit.setDate(date)
                except:
                    pass

            if copy_info['end_date']:
                try:
                    date = QDate.fromString(copy_info['end_date'], 'yyyy-MM-dd')
                    if date.isValid():
                        self.end_date_edit.setDate(date)
                except:
                    pass

            if copy_info['current_page']:
                self.current_page_edit.setValue(copy_info['current_page'])


        cur.execute("SELECT genre_id, name FROM Genre ORDER BY name")
        all_genres = cur.fetchall()

        cur.execute("""
            SELECT g.genre_id FROM Genre g
            JOIN BookGenre bg ON g.genre_id = bg.genre_id
            WHERE bg.book_id = ?
        """, (self.book_data['book_id'],))
        selected_genres = [row['genre_id'] for row in cur.fetchall()]

        for i in reversed(range(self.genres_layout.count())): # в обратном порядке из-за смещения индексов
            widget = self.genres_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        self.genre_checkboxes = {}
        for genre in all_genres:
            cb = QCheckBox(genre['name'])
            cb.setChecked(genre['genre_id'] in selected_genres)
            self.genre_checkboxes[genre['genre_id']] = cb
            self.genres_layout.addWidget(cb)

        self.genres_layout.addStretch()


    def add_new_publisher(self):
        name, ok = QInputDialog.getText(self, "Новое издательство", "Введите название издательства:")     # получает введенное название и флаг подтверждения
        if ok and name.strip():
            conn = self.get_connection()
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO Publisher (name) VALUES (?)", (name.strip(),))
                conn.commit()
                self.load_publishers()
                QMessageBox.information(self, "Успех", "Издательство добавлено!")
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Ошибка", "Издательство с таким названием уже существует!")


    def add_new_genre(self):
        name, ok = QInputDialog.getText(self, "Новый жанр", "Введите название жанра:")
        if ok and name.strip():
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO Genre (name) VALUES (?)", (name.strip(),))
            conn.commit()
            self.load_genres()
            QMessageBox.information(self, "Успех", "Жанр добавлен!")


    def save_data(self):
        try:
            conn = self.get_connection()
            cur = conn.cursor()

            publisher_id = self.publisher_combo.currentData()
            publication_year = int(
                self.publication_year_edit.text()) if self.publication_year_edit.text().isdigit() else None
            page_count = int(self.page_count_edit.text()) if self.page_count_edit.text().isdigit() else None

            cur.execute("""
                UPDATE Book SET 
                title = ?, cover_image = ?, language = ?, publication_year = ?, 
                page_count = ?, summary = ?, publisher_id = ?
                WHERE book_id = ?
            """, (
                self.title_edit.text().strip(),
                self.cover_edit.text().strip() or None,
                self.language_edit.text() or None,
                publication_year,
                page_count,
                self.summary_edit.toPlainText().strip() or None,
                publisher_id,
                self.book_data['book_id']
            ))

            cur.execute("""
                UPDATE BookCopy SET reading_status = ? WHERE book_id = ?
            """, (self.status_combo.currentText(), self.book_data['book_id']))

            # обновляем авторов
            cur.execute("DELETE FROM BookAuthor WHERE book_id = ?", (self.book_data['book_id'],))

            authors = []
            for author_data in self.authors_widgets:
                authors.append({
                    'last_name': author_data['last_name'].text().strip(),
                    'first_name': author_data['first_name'].text().strip(),
                    'middle_name': author_data['middle_name'].text().strip() or None
                })

            for author in authors:
                cur.execute('''
                    INSERT OR IGNORE INTO Author (first_name, last_name, middle_name)
                    VALUES (?, ?, ?)
                ''', (author['first_name'], author['last_name'], author['middle_name']))

                cur.execute('''
                    SELECT author_id FROM Author 
                    WHERE first_name = ? AND last_name = ? AND (middle_name = ? OR (middle_name IS NULL AND ? IS NULL))
                ''', (author['first_name'], author['last_name'], author['middle_name'], author['middle_name']))

                author_row = cur.fetchone()
                if author_row:
                    author_id = author_row[0]
                    cur.execute('INSERT OR IGNORE INTO BookAuthor (book_id, author_id) VALUES (?, ?)',
                                (self.book_data['book_id'], author_id))

            acquisition_date = self.acquisition_date_edit.date().toString(
                'yyyy-MM-dd') if self.acquisition_date_edit.date().isValid() else None # получаем дату и преобразуем в строку
            start_date = self.start_date_edit.date().toString(
                'yyyy-MM-dd') if self.start_date_edit.date().isValid() else None
            end_date = self.end_date_edit.date().toString('yyyy-MM-dd') if self.end_date_edit.date().isValid() else None

            cur.execute("""
                UPDATE BookCopy SET 
                acquisition_date = ?, price = ?, start_date = ?, 
                end_date = ?, current_page = ?
                WHERE book_id = ?
            """, (
                acquisition_date,
                self.price_edit.value() if self.price_edit.value() > 0 else None,
                start_date,
                end_date,
                self.current_page_edit.value(),
                self.book_data['book_id']
            ))

            cur.execute("DELETE FROM BookGenre WHERE book_id = ?", (self.book_data['book_id'],))

            selected_genres = [genre_id for genre_id, cb in self.genre_checkboxes.items() if cb.isChecked()]
            for genre_id in selected_genres:
                cur.execute("INSERT INTO BookGenre (book_id, genre_id) VALUES (?, ?)",
                            (self.book_data['book_id'], genre_id))

            conn.commit()
            QMessageBox.information(self, "Успех", "Данные успешно сохранены!")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить данные: {str(e)}")


class EditCollectionDialog(QDialog):
    def __init__(self, collection_name, all_books, current_book_ids):
        super().__init__()
        self.setWindowTitle("Редактирование коллекции")
        self.all_books = all_books
        self.current_book_ids = current_book_ids
        self.collection_name = collection_name
        self.delete_requested = False # запрос на удаление
        self.name_edit = None
        self.checkboxes = None

        self.setup_ui()


    def setup_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Название коллекции:*"))
        self.name_edit = QLineEdit(self.collection_name)
        layout.addWidget(self.name_edit)

        layout.addWidget(QLabel("Книги в коллекции:"))

        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        self.checkboxes = []
        for book in self.all_books:
            cb = QCheckBox(f"{book['title']} ({book.get('authors', '')})") # создаем текст для чекбокса
            cb.setChecked(book['book_id'] in self.current_book_ids) # создаем сам чекбокс с этим текстом
            self.checkboxes.append(cb)
            scroll_layout.addWidget(cb)

        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(300)
        layout.addWidget(scroll_area)

        buttons_layout = QHBoxLayout()

        btn_delete = QPushButton("Удалить коллекцию")
        btn_delete.setStyleSheet("background-color: #ff6b6b; color: white;")
        btn_delete.clicked.connect(self.delete_collection)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Сохранить')
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('Закрыть')
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)

        buttons_layout.addWidget(btn_delete)
        buttons_layout.addWidget(buttons)
        layout.addLayout(buttons_layout)


    def validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Название коллекции обязательно!")
            return
        self.accept()


    def delete_collection(self):
        msg = QMessageBox()
        msg.setWindowTitle('Удаление')
        msg.setText('Вы уверены, что хотите удалить коллекцию?')
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.button(QMessageBox.StandardButton.Yes).setText('Да')
        msg.button(QMessageBox.StandardButton.No).setText('Нет')

        if msg.exec() == QMessageBox.StandardButton.Yes:
            self.delete_requested = True
            self.accept()


    def get_data(self):
        selected_books = [
            book['book_id'] for cb, book in zip(self.checkboxes, self.all_books)
            if cb.isChecked()
        ]
        return {
            'new_name': self.name_edit.text().strip(),
            'book_ids': selected_books,
            'delete_requested': getattr(self, 'delete_requested', False) # флаг удаления коллекции
        }