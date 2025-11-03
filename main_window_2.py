from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QScrollArea, QDialog, QMessageBox, QCheckBox,
    QGridLayout, QFrame, QMainWindow
)

from PyQt6.QtGui import QPixmap, QColor, QPainter, QCursor
from PyQt6.QtCore import Qt
from database_2 import Database
from dialogs_2 import AddBookDialog, AddCollectionDialog, SearchDialog


class MainWindow(QMainWindow):
    def __init__(self, username="user", user_id=None):
        super().__init__()
        self.username = username
        self.user_id = user_id
        self.main_layout = None
        self.content_widget = None
        self.content_layout = None
        self.left_panel = None
        self.main_area = None
        self.scroll_area = None
        self.scroll_widget = None
        self.grid_layout = None
        self.menu_buttons = None
        self.status_checkboxes = None

        self.setWindowTitle(f"Учёт книг - {username}")
        self.resize(1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.db = Database()
        if self.user_id:
            self.db.set_current_user(self.user_id)
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось определить пользователя")
            return

        self.all_books = []
        self.collections = {}
        self.current_display = 'книги'
        self.current_status_filter = None
        self.current_collection_name = None
        self.search_results = []

        self.load_data()
        self.setup_ui(central_widget)
        self.switch_view('книги')


    def load_data(self):
        try:
            self.all_books = self.db.fetch_books_with_details()
            self.collections = {}
            collections_data = self.db.fetch_collections()

            for col in collections_data:
                try:
                    books_in_col = self.db.fetch_collection_books(col['collection_id'])
                    book_titles = [f"{b['title']} ({b.get('authors', '')})" for b in books_in_col]
                    self.collections[col['name']] = {
                        'id': col['collection_id'],
                        'books': book_titles
                    }
                except Exception as e:
                    continue

        except Exception as e:
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить данные")


    def setup_ui(self, central_widget):
        self.main_layout = QVBoxLayout(central_widget)
        # верхнее меню
        self.create_top_menu()
        # контентная часть
        self.create_content_area()


    def create_top_menu(self):
        top_panel = QWidget()
        top_panel.setFixedHeight(70)
        top_panel.setStyleSheet("background-color: #E5C07B;")
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(15, 0, 15, 0) # от левой и правой границы верхней части
        top_layout.setSpacing(20) # между элементами

        lbl_title = QLabel(f"Учёт книг")
        lbl_title.setStyleSheet("font-weight: bold; font-size: 18px; color: #3F1D1D;")
        top_layout.addWidget(lbl_title, alignment=Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft) # вертикаль, горизонталь

        self.menu_buttons = {}
        menu_names = ["книги", "коллекции", "поиск"]
        menu_widget = QWidget()
        menu_layout = QHBoxLayout(menu_widget)
        menu_layout.setSpacing(5)

        for name in menu_names:
            btn = QPushButton(name)
            btn.setFixedHeight(30)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #B65D5D;
                    color: #3F1D1D;
                    border-radius: 5px;
                    padding: 5px 15px; 
                }
                QPushButton:hover {
                    background-color: #8C4545;
                }
            """) # внутренние отступы: 5px сверху/снизу, 15px слева/справа
            btn.clicked.connect(lambda checked, n=name: self.switch_view(n))
            self.menu_buttons[name] = btn
            menu_layout.addWidget(btn)

        top_layout.addWidget(menu_widget, alignment=Qt.AlignmentFlag.AlignHCenter)
        # Профиль справа
        profile_widget = QWidget()
        lbl_nickname = QLabel(self.username)
        lbl_nickname.setStyleSheet("color: #3F1D1D; font-weight: 600; font-size: 14px;")
        lbl_logout = QLabel("выход из системы")
        lbl_logout.setStyleSheet("color: #3F1D1D; font-size: 12px;")
        lbl_logout.mousePressEvent = lambda event: self.logout()
        profile_texts = QVBoxLayout(profile_widget)
        profile_texts.setContentsMargins(0, 10, 0, 10)
        profile_texts.setSpacing(10)
        profile_texts.addWidget(lbl_nickname)
        profile_texts.addWidget(lbl_logout)

        top_layout.addWidget(profile_widget, alignment=Qt.AlignmentFlag.AlignRight)
        self.main_layout.addWidget(top_panel)


    def logout(self):
        msg = QMessageBox()
        msg.setWindowTitle('Выход')
        msg.setText('Вы уверены, что хотите выйти?')
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.button(QMessageBox.StandardButton.Yes).setText('Да')
        msg.button(QMessageBox.StandardButton.No).setText('Нет')

        if msg.exec() == QMessageBox.StandardButton.Yes:
            self.close()


    def create_content_area(self):
        self.content_widget = QWidget()
        self.content_layout = QHBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        self.left_panel = QWidget()
        self.left_panel.setFixedWidth(250)
        self.left_panel.setStyleSheet("background-color: #8B4C4C;")
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(10)

        lbl_statuses_title = QLabel("Статусы чтения")
        lbl_statuses_title.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #B65D5D, stop:1 #8B4C4C);
            border-radius: 10px;
            color: white;
            font-weight: 600;
            padding: 5px 10px;
        """)
        left_layout.addWidget(lbl_statuses_title)

        self.status_checkboxes = {}
        statuses = [
            ("Запланировано", "📅"),
            ("Прочитано", "✔️"),
            ("Читаю", "⏳"),
            ("Заброшено", "🗑️")
        ]
        for status, icon in statuses:
            cb = QCheckBox(f"{icon}  {status}")
            cb.setStyleSheet("""
                QCheckBox {
                    background-color: #B65D5D;
                    border-radius: 10px;
                    color: #3F1D1D;
                    font-weight: 600;
                    padding: 8px 10px;
                    margin-bottom: 5px;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                }
            """)
            cb.stateChanged.connect(lambda state, s=status: self.on_status_toggled(s, state))
            self.status_checkboxes[status] = cb
            left_layout.addWidget(cb)

        lbl_add_title = QLabel("Добавить")
        lbl_add_title.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #B65D5D, stop:1 #8B4C4C);
            border-radius: 10px;
            color: white;
            font-weight: 600;
            padding: 5px 10px;
            margin-top: 15px;
        """)
        left_layout.addWidget(lbl_add_title)

        btn_add_item = QPushButton("➕ Книга")
        btn_add_item.setStyleSheet("""
            background-color: #B65D5D;
            border-radius: 10px;
            color: #3F1D1D;
            font-weight: 600;
            padding: 8px 10px;
            margin-bottom: 7px;
            text-align: left;
        """)
        btn_add_item.clicked.connect(self.open_add_book_dialog)
        left_layout.addWidget(btn_add_item)

        btn_add_collection = QPushButton("➕ Коллекция")
        btn_add_collection.setStyleSheet("""
            background-color: #B65D5D;
            border-radius: 10px;
            color: #3F1D1D;
            font-weight: 600;
            padding: 8px 10px;
            margin-bottom: 7px;
            text-align: left;
        """)
        btn_add_collection.clicked.connect(self.open_add_collection_dialog)
        left_layout.addWidget(btn_add_collection)

        left_layout.addStretch() # Добавляет растягивающийся пустой элемент, который занимает всё оставшееся пространство
        self.content_layout.addWidget(self.left_panel)
        # Основная часть для книг
        self.main_area = QWidget()
        self.main_area.setStyleSheet("background-color: #FFFACD;")
        main_area_layout = QVBoxLayout(self.main_area)
        main_area_layout.setContentsMargins(15, 15, 15, 15)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.grid_layout = QGridLayout(self.scroll_widget)
        self.grid_layout.setSpacing(15)
        self.scroll_area.setWidget(self.scroll_widget)
        main_area_layout.addWidget(self.scroll_area)

        self.content_layout.addWidget(self.main_area)
        self.main_layout.addWidget(self.content_widget)


    def switch_view(self, view):
        # обнуляем фильтры
        for cb in self.status_checkboxes.values():
            cb.blockSignals(True)
            cb.setChecked(False)
            cb.blockSignals(False)

        self.current_display = view
        self.current_status_filter = None
        self.current_collection_name = None
        self.search_results = []

        if view == 'книги':
            self.display_books()
        elif view == 'коллекции':
            self.display_collections()
        elif view == 'поиск':
            self.open_search_dialog()


    def on_status_toggled(self, status, state):
        if state == Qt.CheckState.Checked.value:
            for s, cb in self.status_checkboxes.items(): # идём по статусам и чекбоксам
                if s != status:
                    cb.blockSignals(True)
                    cb.setChecked(False)
                    cb.blockSignals(False)
            self.current_status_filter = status
        else:
            self.current_status_filter = None
        self.display_books() # там учитывается значение current_status_filter


    def open_add_book_dialog(self):
        try:
            dialog = AddBookDialog()
            result = dialog.exec() # показываем диалог и ждем результат
            if result == QDialog.DialogCode.Accepted:
                data = dialog.get_data()
                success = self.db.add_book(
                    data['title'],
                    data['authors'],
                    data['cover'],
                    data['status'],
                    data['publication_year'],
                    data['page_count'],
                    data['summary']
                )

                if success:
                    self.load_data()
                    self.display_books()
                    QMessageBox.information(self, "Успех", "Книга успешно добавлена!")
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось добавить книгу в базу данных")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Ошибка при добавлении книги: {str(e)}")


    def open_add_collection_dialog(self):
        if not self.all_books:
            QMessageBox.information(self, "Info", "Добавьте книги сначала.")
            return

        try:
            dialog = AddCollectionDialog(self.all_books)
            result = dialog.exec()
            if result == QDialog.DialogCode.Accepted:
                data = dialog.get_data()
                success = self.db.add_collection(data['name'], data['books'])
                if success:
                    self.load_data()
                    self.display_collections()
                    QMessageBox.information(self, "Успех", "Коллекция успешно создана!")
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось создать коллекцию")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании коллекции: {str(e)}")


    def open_search_dialog(self):
        dialog = SearchDialog()
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            criteria = dialog.get_criteria()
            self.search_results = [
                b for b in self.all_books
                if (criteria['title'].lower() in b['title'].lower() if criteria['title'] else True)
                   and (criteria['author'].lower() in b.get('authors', '').lower() if criteria['author'] else True)
            ]
            self.current_display = 'поиск'
            self.display_search_results()


    def display_books(self):
        # очищаем все карточки книг перед отображением новых
        for i in reversed(range(self.grid_layout.count())):
            w = self.grid_layout.itemAt(i).widget()
            if w:
                w.setParent(None) # удаляем виджет из layout
        # Фильтр
        filtered_books = self.all_books
        if self.current_status_filter:
            filtered_books = [b for b in self.all_books if b['reading_status'] == self.current_status_filter]
        # Вывод
        row, col, max_cols = 0, 0, 4
        for book in filtered_books:
            self.grid_layout.addWidget(self.create_book_card(book), row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1


    def display_collections(self):
        for i in reversed(range(self.grid_layout.count())):
            w = self.grid_layout.itemAt(i).widget()
            if w:
                w.setParent(None) # чтобы очистить старые карточки коллекций перед отображением новых, иначе новые карточки добавятся поверх старых.
        row, col, max_cols = 0, 0, 4
        for name, collection_data in self.collections.items():
            self.grid_layout.addWidget(self.create_collection_card(name), row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1


    def display_search_results(self):
        for i in reversed(range(self.grid_layout.count())):
            w = self.grid_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
        row, col, max_cols = 0, 0, 4
        for book in self.search_results:
            self.grid_layout.addWidget(self.create_book_card(book), row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1


    def create_book_card(self, book):
        card = QFrame()
        card.setFrameShape(QFrame.Shape.Box) # прямоугольник
        card.setStyleSheet("""
            background-color: white;
            border-radius: 10px;
            border: 1px solid #B65D5D;
        """)
        card.setFixedSize(220, 320)
        layout = QVBoxLayout(card)

        # обложка
        cover = QLabel() # метка для обложки
        pixmap = QPixmap() # создаем пустое изображение
        loaded = False # флаг загрузки
        if book.get('cover_image'):
            loaded = pixmap.load(book['cover_image']) # загружаем обложку из файла
        if not loaded or pixmap.isNull():
            pixmap = QPixmap(150, 200)
            pixmap.fill(Qt.GlobalColor.transparent) # заполняем прозрачным
            painter = QPainter(pixmap) # создаем рисовальщик для pixmap
            painter.setRenderHint(QPainter.RenderHint.Antialiasing) # включаем сглаживание
            painter.setBrush(QColor("#E5C07B")) # устанавливаем желтую кисть заливки
            painter.setPen(Qt.PenStyle.NoPen) # убираем обводку
            painter.drawRoundedRect(0, 0, 147, 200, 10, 10) # рисуем скругленный прямоугольник (x, y, width, height, radiusX, radiusY)
            painter.end() # завершаем рисование
        else:
            pixmap = pixmap.scaled(150, 200, Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation) # масштабируем изображение до 150x200
        cover.setPixmap(pixmap)
        cover.setFixedSize(150, 200)  # обложка всегда одного размера
        layout.addWidget(cover, alignment=Qt.AlignmentFlag.AlignCenter)

        title = QLabel(book['title'])
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #3F1D1D;")
        title.setWordWrap(True) # разрешаем перенос слов
        title.setFixedHeight(30)
        title.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(title)

        authors_text = book.get('authors', '')
        authors = QLabel(authors_text)
        authors.setStyleSheet("font-size: 12px; color: #666;")
        authors.setWordWrap(True)
        authors.setFixedHeight(33)
        layout.addWidget(authors)

        status = QLabel(f"Статус: {book.get('reading_status', '')}")
        status.setStyleSheet("font-size: 11px; color: #888;")
        status.setFixedHeight(20)
        status.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(status)

        # обработчик клика по карточке
        def mousePressEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.show_book_info(book)
            else:
                event.ignore()  # правую кнопку пропускаем для контекстного меню

        card.mousePressEvent = mousePressEvent
        # контекстное меню для карточки
        card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        card.customContextMenuRequested.connect(lambda pos, b=book: self.show_book_context_menu(pos, b))

        return card


    def show_book_info(self, book):
        try:
            full_book_info = self.db.fetch_full_book_info(book['book_id'])
            if full_book_info:
                book = full_book_info  # используем полную информацию
        except Exception as e:
            print(f"Error loading full book info: {e}")

        from PyQt6.QtWidgets import QTextEdit, QFormLayout # так как не на уровне модуля

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Информация о книге: {book['title']}")
        dialog.resize(600, 700)
        dialog.setStyleSheet("background-color: #FFFACD; color: black;")

        main_layout = QVBoxLayout(dialog)

        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        try:
            full_book_info = self.db.fetch_full_book_info(book['book_id'])
            if full_book_info:
                book = full_book_info
        except Exception as e:
            pass

        # верхняя часть с обложкой и основной информацией
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)

        # Обложка (если есть)
        if book.get('cover_image'):
            cover_label = QLabel()
            pixmap = QPixmap(book['cover_image'])
            if not pixmap.isNull():
                pixmap = pixmap.scaled(200, 280, Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation) # изображение до 200x280px
                cover_label.setPixmap(pixmap)
            else:
                # заглушка если обложка не загружается
                pixmap = QPixmap(200, 280)
                pixmap.fill(QColor("#E5C07B"))
                cover_label.setPixmap(pixmap)
                cover_label.setText("Нет обложки")
                cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cover_label.setStyleSheet("color: black;")
        else:
            # заглушка если обложки нет
            cover_label = QLabel("Нет обложки")
            cover_label.setFixedSize(200, 280)
            cover_label.setStyleSheet("background-color: #E5C07B; border: 1px solid #B65D5D; color: black;")
            cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        top_layout.addWidget(cover_label)

        # основная информация справа от обложки
        info_widget = QWidget()
        info_layout = QFormLayout(info_widget)
        info_layout.setVerticalSpacing(8) # расстояние между строками формы 8px

        label_style = "color: black;"
        title_style = "font-size: 18px; font-weight: bold; color: black;"
        section_style = "font-size: 14px; font-weight: bold; color: black; margin-top: 15px;" # информация о чтении и описание

        title_label = QLabel(book['title'])
        title_label.setStyleSheet(title_style)
        title_label.setWordWrap(True)
        info_layout.addRow("Название:", title_label)

        authors_text = book.get('authors', '')
        if isinstance(authors_text, list):
            authors_text = ', '.join(authors_text)
        authors_label = QLabel(authors_text)
        authors_label.setStyleSheet(label_style)
        authors_label.setWordWrap(True)
        info_layout.addRow("Авторы:", authors_label)

        status_label = QLabel(book.get('reading_status', ''))
        status_label.setStyleSheet(label_style)
        info_layout.addRow("Статус:", status_label)

        if book.get('genres'):
            genres_text = ', '.join(book['genres']) if isinstance(book['genres'], list) else book['genres']
            genres_label = QLabel(genres_text)
            genres_label.setStyleSheet(label_style)
            genres_label.setWordWrap(True)
            info_layout.addRow("Жанры:", genres_label)

        if book.get('publisher_name'):
            publisher_label = QLabel(book['publisher_name'])
            publisher_label.setStyleSheet(label_style)
            info_layout.addRow("Издательство:", publisher_label)

        if book.get('publication_year'):
            year_label = QLabel(str(book['publication_year']))
            year_label.setStyleSheet(label_style)
            info_layout.addRow("Год издания:", year_label)

        if book.get('page_count'):
            pages_label = QLabel(str(book['page_count']))
            pages_label.setStyleSheet(label_style)
            info_layout.addRow("Страниц:", pages_label)

        if book.get('language'):
            language_label = QLabel(book['language'])
            language_label.setStyleSheet(label_style)
            info_layout.addRow("Язык:", language_label)

        top_layout.addWidget(info_widget)
        scroll_layout.addWidget(top_widget)

        # информация о чтении
        reading_widget = QWidget()
        reading_layout = QFormLayout(reading_widget)
        reading_layout.setVerticalSpacing(5)

        reading_title = QLabel("Информация о чтении")
        reading_title.setStyleSheet(section_style)
        scroll_layout.addWidget(reading_title)

        if book.get('acquisition_date'):
            acquisition_label = QLabel(book['acquisition_date'])
            acquisition_label.setStyleSheet(label_style)
            reading_layout.addRow("Дата приобретения:", acquisition_label)

        if book.get('price'):
            price_label = QLabel(f"{book['price']} ₽")
            price_label.setStyleSheet(label_style)
            reading_layout.addRow("Цена:", price_label)

        if book.get('start_date'):
            start_label = QLabel(book['start_date'])
            start_label.setStyleSheet(label_style)
            reading_layout.addRow("Дата начала:", start_label)

        if book.get('end_date'):
            end_label = QLabel(book['end_date'])
            end_label.setStyleSheet(label_style)
            reading_layout.addRow("Дата окончания:", end_label)

        if book.get('current_page'):
            current_page_label = QLabel(str(book['current_page']))
            current_page_label.setStyleSheet(label_style)
            reading_layout.addRow("Текущая страница:", current_page_label)

        scroll_layout.addWidget(reading_widget)

        desc_title = QLabel("Описание")
        desc_title.setStyleSheet(section_style)
        scroll_layout.addWidget(desc_title)

        if book.get('summary'):
            summary_text = QTextEdit() # многострочное текстовое поле
            summary_text.setPlainText(book['summary'])
            summary_text.setReadOnly(True) # делает поле только для чтения (нередактируемым)
            summary_text.setStyleSheet("""
                font-size: 11px; 
                background-color: white;
                border: 1px solid #B65D5D;
                border-radius: 5px;
                padding: 8px;
                color: black;  
            """)
            summary_text.setMaximumHeight(150)
            scroll_layout.addWidget(summary_text)
        else:
            no_summary_label = QLabel("Описание отсутствует")
            no_summary_label.setStyleSheet("color: black; font-style: italic; font-size: 11px;")
            scroll_layout.addWidget(no_summary_label)

        # кнопка расширенного редактирования
        btn_extended = QPushButton("Редактирование")
        btn_extended.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
                margin-top: 15px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        btn_extended.clicked.connect(lambda: self.open_extended_edit(book, dialog))
        scroll_layout.addWidget(btn_extended)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)

        dialog.exec()


    def open_extended_edit(self, book, parent_dialog):
        if parent_dialog: # show_book_info
            parent_dialog.close() # закрываем просмотр информации о книге, чтобы открыть редактирование
        try:
            from dialogs_2 import ExtendedBookInfoDialog
            dialog = ExtendedBookInfoDialog(book, self.db)
            result = dialog.exec()
            if result == QDialog.DialogCode.Accepted:
                self.load_data()
                if self.current_display == 'книги':
                    self.display_books()
                elif self.current_display == 'поиск':
                    self.display_search_results()
                elif self.current_display == 'просмотр_коллекции':
                    self.view_collection(self.current_collection_name)
                elif self.current_display == 'коллекции':
                    self.display_collections()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть редактор: {str(e)}")


    def create_collection_card(self, name):
        card = QFrame()
        card.setFrameShape(QFrame.Shape.Box)
        card.setStyleSheet("""
            background-color: white;
            border-radius: 10px;
            border: 1px solid #B65D5D;
        """)
        card.setFixedSize(200, 250)
        layout = QVBoxLayout(card)

        icon = QLabel("📚")
        icon.setStyleSheet("font-size: 100px;")
        layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)

        title = QLabel(name)
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #3F1D1D;")
        title.setWordWrap(True)
        layout.addWidget(title)

        def mousePressEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.view_collection(name)
            elif event.button() == Qt.MouseButton.RightButton:
                self.show_collection_context_menu(event.pos(), name)

        card.mousePressEvent = mousePressEvent

        card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        card.customContextMenuRequested.connect(
            lambda pos, n=name: self.show_collection_context_menu(pos, n)
        )

        return card


    def show_collection_context_menu(self, pos, collection_name):
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)

        edit_action = menu.addAction("✏️ Редактировать коллекцию")
        delete_action = menu.addAction("🗑️ Удалить коллекцию")

        action = menu.exec(QCursor.pos()) # меню появляется под курсором

        if action == edit_action:
            self.edit_collection(collection_name)
        elif action == delete_action:
            self.delete_collection(collection_name)


    def edit_collection(self, collection_name):
        collection_id = self.collections[collection_name]['id']
        current_books = self.db.fetch_collection_books(collection_id)
        current_book_ids = [book['book_id'] for book in current_books]

        try:
            from dialogs_2 import EditCollectionDialog
            dialog = EditCollectionDialog(
                collection_name,
                self.all_books,
                current_book_ids
            )
            result = dialog.exec()

            if result == QDialog.DialogCode.Accepted:
                data = dialog.get_data()

                if data['delete_requested']:
                    # удаление коллекции
                    success = self.db.delete_collection(collection_id)
                    if success:
                        QMessageBox.information(self, "Успех", "Коллекция удалена!")
                        # обновляем интерфейс после удаления
                        self.load_data()
                        self.current_display = 'коллекции'
                        self.display_collections()
                else:
                    # обновление коллекции
                    success = self.db.update_collection(
                        collection_id,
                        data['new_name'],
                        data['book_ids']
                    )
                    if success:
                        QMessageBox.information(self, "Успех", "Коллекция обновлена!")
                        self.load_data()
                        if self.current_display == 'коллекции':
                            self.display_collections()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось редактировать коллекцию: {str(e)}")


    def delete_collection(self, collection_name):
        collection_id = self.collections[collection_name]['id']

        msg = QMessageBox()
        msg.setWindowTitle('Удаление')
        msg.setText(f'Вы уверены, что хотите удалить коллекцию "{collection_name}"?')
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.button(QMessageBox.StandardButton.Yes).setText('Да')
        msg.button(QMessageBox.StandardButton.No).setText('Нет')

        if msg.exec() == QMessageBox.StandardButton.Yes:
            success = self.db.delete_collection(collection_id)
            if success:
                self.load_data()
                self.current_display = 'коллекции'
                self.display_collections()
                QMessageBox.information(self, "Успех", "Коллекция удалена!")


    def show_book_context_menu(self, pos, book):
        from PyQt6.QtWidgets import QMenu

        menu = QMenu(self)
        status_menu = menu.addMenu("Изменить статус")
        statuses = ['Запланировано', 'Прочитано', 'Читаю', 'Заброшено']
        for status in statuses:
            action = status_menu.addAction(status)
            action.triggered.connect(lambda checked, s=status, b=book: self.change_reading_status(b, s))

        extended_action = menu.addAction("Редактирование")
        extended_action.triggered.connect(lambda: self.open_extended_edit(book, None))

        delete_action = menu.addAction("🗑️ Удалить книгу")
        delete_action.triggered.connect(lambda: self.delete_book(book))

        menu.exec(QCursor.pos())


    def delete_book(self, book):
        """Удаление книги с подтверждением"""
        msg = QMessageBox()
        msg.setWindowTitle('Удаление книги')
        msg.setText(f'Вы уверены, что хотите удалить книгу "{book["title"]}"?\n\nЭто действие нельзя отменить!')
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.button(QMessageBox.StandardButton.Yes).setText('Да')
        msg.button(QMessageBox.StandardButton.No).setText('Нет')

        if msg.exec() == QMessageBox.StandardButton.Yes:
            success = self.db.delete_book(book['book_id'])
            if success:
                self.load_data()
                if self.current_display == 'книги':
                    self.display_books()
                elif self.current_display == 'поиск':
                    self.display_search_results()
                elif self.current_display == 'collection_view':
                    self.view_collection(self.current_collection_name)
                QMessageBox.information(self, "Успех", "Книга успешно удалена!")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось удалить книгу")


    def change_reading_status(self, book, new_status):
        self.db.update_reading_status(book['book_id'], new_status)
        self.load_data()
        if self.current_display == 'книги':
            self.display_books()


    def view_collection(self, name):
        self.current_display = 'collection_view'
        self.current_collection_name = name
        for i in reversed(range(self.grid_layout.count())):
            w = self.grid_layout.itemAt(i).widget() # grid layout - в целом виджет для отображения книг/коллекций
            if w:
                w.setParent(None)

        collection_id = self.collections[name]['id']
        books_in_collection = self.db.fetch_collection_books(collection_id)

        row, col, max_cols = 0, 0, 4
        for book in books_in_collection:
            self.grid_layout.addWidget(self.create_book_card(book), row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1