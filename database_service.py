from datetime import datetime
from utilities import _create_mock_data
import models
import sqlite3


class DatabaseService:

    conn: sqlite3.Connection = None

    # temp
    _boards = None

    # cache
    _board_previews = []

    def __init__(self):
        self._boards = _create_mock_data()
        self.set_connection()
        self.create_tables()

    def set_connection(self):
        self.conn = sqlite3.connect("pinboard.db")
        
    def create_tables(self):
        c = self.conn.cursor()
        
        c.executescript("""
            CREATE TABLE IF NOT EXISTS board (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                date_created TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS board_item (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                board_id INT NOT NULL,
                colour TEXT NOT NULL,
                date_created TEXT NOT NULL,
                type TEXT CHECK(type IN ('note', 'page', 'image')),
                x_pos INTEGER NOT NULL,
                y_pos INTEGER NOT NULL,
                
                CHECK(length(color) = 7)
                FOREIGN KEY (board_id) REFERENCES board(id)
            );
            
            CREATE TABLE IF NOT EXISTS tag (
                id INTEGER PRIMARY KEY AUTO INCREMENT,
                item_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                
                FOREIGN KEY (item_id) REFERENCES board_item(id)
            );
            
            CREATE TABLE IF NOT EXISTS Note (
                id INTEGER PRIMARY KEY,
                content TEXT NOT NULL,
                
                FOREIGN KEY (id) REFERENCES board_item(id)
            )
            
            CREATE TABLE IF NOT EXISTS Page (
                id INTEGER PRIMARY KEY,
                content TEXT NOT NULL,
                
                FOREIGN KEY (id) REFERENCES board_item(id)
            )
            
            CREATE TABLE IF NOT EXISTS Image (
                id INTEGER PRIMARY KEY,
                image BLOB NOT NULL,
                
                FOREIGN KEY (id) REFERENCES board_item(id)
            )
        """)

        self.conn.commit()
        self.conn.close()

    def get_all_board_ids(self):
        pass

    def get_boards(self):
        return _create_mock_data()

    def get_board(self, id: int):
        for board in self._boards:
            if board.board_id == id:
                return board
        return None

    def get_board_previews(self):
        dates = [
            datetime(2025, 3, 10, 14, 30, 0),
            datetime(2025, 2, 21, 18, 20, 1),
            datetime(2024, 12, 6, 20, 20, 21),
            datetime(2024, 8, 2, 10, 51, 41),
            datetime(2025, 1, 28, 15, 11, 58),
            datetime(2025, 3, 10, 14, 30, 0),
            datetime(2025, 2, 21, 18, 20, 1),
            datetime(2024, 12, 6, 20, 20, 21),
            datetime(2024, 8, 2, 10, 51, 41),
            datetime(2025, 1, 28, 15, 11, 58),
        ]

        board_previews = [
            (1, "Programming", dates[0]),
            (2, "Recipes", dates[1]),
            (3, "Reminders", dates[2]),
            (4, "ITOOA Notes", dates[3]),
            (5, "2025 Goals", dates[4]),
            (6, "momomomoumoumou", dates[5]),
            (7, "Recipes", dates[6]),
            (8, "Reminders", dates[7]),
            (9, "ITOOA Notes", dates[8]),
            (10, "2025 Goals", dates[9]),
            (11, "Programming", dates[1]),
            (12, "Recipes", dates[2]),
            (13, "Reminders", dates[3]),
            (14, "ITOOA Notes", dates[4]),
            (15, "2025 Goals", dates[5]),
        ]

        return board_previews

    def get_open_boards(self):
        # TODO: create query to retrieve only boards with open = True
        pass

    def create_board(self, board: models.Board):
        # Save board to database

        if board.board_items:
            for item in board.board_items:
                # Save item to database
                pass

    def save_board(self, board: models.Board):
        if board.changed:
            # Save board to database
            pass

        for item in board.board_items:
            if item.changed:
                # Save item to database
                pass

    def delete_board(self, id: int):
        for board in self._boards:
            if board.id == id:
                # Remove board from database
                pass
