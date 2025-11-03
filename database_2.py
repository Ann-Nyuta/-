import sqlite3
class Database:
    def __init__(self, db_path='library.db'):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.current_user_id = None
        self.create_tables()

    def set_current_user(self, user_id):
        self.current_user_id = user_id


    def create_tables(self):
        cur = self.conn.cursor()

        cur.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS Publisher (
                publisher_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS Genre (
                genre_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS Author (
                author_id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                middle_name TEXT
            )
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS Book (
                book_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                publisher_id INTEGER,
                title TEXT NOT NULL,
                publication_year INTEGER,
                page_count INTEGER,
                summary TEXT,
                language TEXT,
                cover_image TEXT,
                FOREIGN KEY (publisher_id) REFERENCES Publisher(publisher_id) ON DELETE SET NULL,
                FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
            )
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS BookCopy (
                copy_id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                acquisition_date TEXT,
                price REAL,
                start_date TEXT,
                end_date TEXT,
                current_page INTEGER DEFAULT 0,
                reading_status TEXT NOT NULL DEFAULT 'Запланировано',
                FOREIGN KEY (book_id) REFERENCES Book(book_id) ON DELETE CASCADE ON UPDATE CASCADE
            )
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS BookAuthor (
                book_id INTEGER NOT NULL,
                author_id INTEGER NOT NULL,
                PRIMARY KEY (book_id, author_id),
                FOREIGN KEY (book_id) REFERENCES Book(book_id) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY (author_id) REFERENCES Author(author_id) ON DELETE CASCADE ON UPDATE CASCADE
            )
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS BookGenre (
                book_id INTEGER NOT NULL,
                genre_id INTEGER NOT NULL,
                PRIMARY KEY (book_id, genre_id),
                FOREIGN KEY (book_id) REFERENCES Book(book_id) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY (genre_id) REFERENCES Genre(genre_id) ON DELETE CASCADE ON UPDATE CASCADE
            )
        ''')

        cur.execute('''
        CREATE TABLE IF NOT EXISTS Collections (
            collection_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,  
            name TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
        )
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS BookColl (
                book_id INTEGER NOT NULL,
                collection_id INTEGER NOT NULL,
                PRIMARY KEY (book_id, collection_id),
                FOREIGN KEY (book_id) REFERENCES Book(book_id) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY (collection_id) REFERENCES Collections(collection_id) ON DELETE CASCADE ON UPDATE CASCADE
            )
        ''')

        self.conn.commit()


    def fetch_books_with_details(self):
        if not self.current_user_id:
            return []

        try:
            cur = self.conn.cursor()
            cur.execute('''
                SELECT 
                    b.book_id, 
                    b.title, 
                    b.cover_image, 
                    b.publication_year, 
                    b.page_count,
                    bc.reading_status,
                    GROUP_CONCAT(a.first_name || ' ' || a.last_name, ', ') as authors
                FROM Book b
                LEFT JOIN BookCopy bc ON b.book_id = bc.book_id 
                LEFT JOIN BookAuthor ba ON b.book_id = ba.book_id
                LEFT JOIN Author a ON ba.author_id = a.author_id
                WHERE b.user_id = ?
                GROUP BY b.book_id
            ''', (self.current_user_id,))
            # left - чтобы отображались книги даже с некоторыми нулевыми значениями

            rows = cur.fetchall()
            books = []
            for row in rows:
                try:
                    book_dict = dict(row)
                    books.append(book_dict)
                except Exception:
                    continue

            return books

        except Exception:
            return []


    def fetch_collections(self):
        if not self.current_user_id:
            return []

        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM Collections WHERE user_id = ?", (self.current_user_id,))

            rows = cur.fetchall()
            collections = [dict(row) for row in rows]
            return collections
        except Exception:
            return []


    def fetch_collection_books(self, collection_id):
        try:
            cur = self.conn.cursor()
            cur.execute('''
                SELECT 
                    b.book_id, b.title, b.cover_image, b.publication_year, b.page_count,
                    bc.reading_status,
                    GROUP_CONCAT(a.first_name || ' ' || a.last_name, ', ') as authors
                FROM Book b
                JOIN BookColl bcol ON b.book_id = bcol.book_id
                LEFT JOIN BookCopy bc ON b.book_id = bc.book_id
                LEFT JOIN BookAuthor ba ON b.book_id = ba.book_id
                LEFT JOIN Author a ON ba.author_id = a.author_id
                WHERE bcol.collection_id = ? AND b.user_id = ?
                GROUP BY b.book_id
            ''', (collection_id, self.current_user_id))

            rows = cur.fetchall()
            books = [dict(row) for row in rows]
            return books

        except Exception:
            return []


    def fetch_full_book_info(self, book_id):
        try:
            cur = self.conn.cursor()
            cur.execute('''
                SELECT 
                    b.book_id, b.title, b.cover_image, b.publication_year, b.page_count,
                    b.summary, b.language, b.publisher_id,
                    bc.reading_status, bc.acquisition_date, bc.price, bc.start_date, 
                    bc.end_date, bc.current_page,
                    p.name as publisher_name,
                    GROUP_CONCAT(DISTINCT a.first_name || ' ' || a.last_name || 
                    CASE WHEN a.middle_name IS NOT NULL THEN ' ' || a.middle_name ELSE '' END) as authors,
                    GROUP_CONCAT(DISTINCT g.name) as genres
                FROM Book b
                LEFT JOIN BookCopy bc ON b.book_id = bc.book_id
                LEFT JOIN Publisher p ON b.publisher_id = p.publisher_id
                LEFT JOIN BookAuthor ba ON b.book_id = ba.book_id
                LEFT JOIN Author a ON ba.author_id = a.author_id
                LEFT JOIN BookGenre bg ON b.book_id = bg.book_id
                LEFT JOIN Genre g ON bg.genre_id = g.genre_id
                WHERE b.book_id = ?
                GROUP BY b.book_id
            ''', (book_id,))

            row = cur.fetchone()
            if row:
                book_dict = dict(row)
                # Преобразуем строки с жанрами и авторами в списки
                if book_dict.get('genres'):
                    book_dict['genres'] = book_dict['genres'].split(',')
                if book_dict.get('authors'):
                    book_dict['authors'] = book_dict['authors'].split(',')

                return book_dict
            return None
        except Exception:
            return None


    def add_book(self, title, authors, cover_image, reading_status, publication_year=None, page_count=None,
                 summary=None):
        if not self.current_user_id:
            return False

        cur = self.conn.cursor()
        try:
            cur.execute('''
                INSERT INTO Book (user_id, title, cover_image, publication_year, page_count, summary)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.current_user_id, title, cover_image or None, publication_year, page_count, summary))

            book_id = cur.lastrowid # это ID последней вставленной записи (auto_increment)

            for author in authors: # INSERT OR IGNORE - добавляет, если автора еще нет
                cur.execute('''
                                INSERT OR IGNORE INTO Author (first_name, last_name, middle_name)
                                VALUES (?, ?, ?)
                            ''', (author['first_name'], author['last_name'], author['middle_name']))

                cur.execute('''
                                SELECT author_id FROM Author 
                                WHERE first_name = ? AND last_name = ? AND (middle_name = ? OR (middle_name IS NULL AND ? IS NULL)) 
                            ''',
                            (author['first_name'], author['last_name'], author['middle_name'], author['middle_name']))

                author_row = cur.fetchone()
                if author_row:
                    author_id = author_row[0]
                    cur.execute('INSERT OR IGNORE INTO BookAuthor (book_id, author_id) VALUES (?, ?)',
                                (book_id, author_id))

            cur.execute('''
                            INSERT INTO BookCopy (book_id, reading_status)
                            VALUES (?, ?)
                        ''', (book_id, reading_status))

            self.conn.commit()
            return True

        except Exception:
            self.conn.rollback()
            return False


    def add_collection(self, name, book_ids=None):
        if not self.current_user_id:
            return False

        try:
            if book_ids is None:
                book_ids = []

            cur = self.conn.cursor()
            cur.execute("INSERT INTO Collections (name, user_id) VALUES (?, ?)",
                        (name, self.current_user_id))
            collection_id = cur.lastrowid

            for book_id in book_ids:
                try:
                    cur.execute("INSERT OR IGNORE INTO BookColl (book_id, collection_id) VALUES (?, ?)",
                                (book_id, collection_id))

                except Exception:
                    pass

            self.conn.commit()
            return True

        except Exception:
            self.conn.rollback()
            return False


    def update_reading_status(self, book_id, status):
        cur = self.conn.cursor()
        cur.execute('''
            UPDATE BookCopy 
            SET reading_status = ? 
            WHERE book_id = ?
        ''', (status, book_id))
        self.conn.commit()


    def update_collection(self, collection_id, new_name, book_ids):
        try:
            cur = self.conn.cursor()

            # обновляем название коллекции
            cur.execute("UPDATE Collections SET name = ? WHERE collection_id = ?",
                        (new_name, collection_id))

            # удаляем старые связи
            cur.execute("DELETE FROM BookColl WHERE collection_id = ?", (collection_id,))

            # добавляем новые связи
            for book_id in book_ids:
                cur.execute("INSERT INTO BookColl (book_id, collection_id) VALUES (?, ?)",
                            (book_id, collection_id))

            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            return False


    def delete_book(self, book_id):
        try:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM Book WHERE book_id = ?", (book_id,))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            return False


    def delete_collection(self, collection_id):
        try:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM Collections WHERE collection_id = ?", (collection_id,))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            return False


    def close(self):
        self.conn.close() # Закрывает соединение с БД при завершении работы приложения