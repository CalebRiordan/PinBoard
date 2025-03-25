from datetime import datetime
from enum import Enum
import os
from utilities import get_setting
import models
import sqlite3


class QueryTypes(Enum):
    SINGLE = "execute"
    MANY = "executemany"
    SCRIPT = "executescript"
class DatabaseService:

    conn: sqlite3.Connection = None

    # cache
    _board_previews = []

    def __init__(self, db_name = None):
        if db_name:
            self.set_connection(db_name=db_name)
        

    def set_connection(self, db_name):
        if not os.path.exists(db_name + ".db"):
            self.conn = sqlite3.connect(f"{db_name}.db")

    def create_tables(self):
        c = self.conn.cursor()

        c.executescript(
            """
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
                
                CHECK(length(colour) = 7)
                FOREIGN KEY (board_id) REFERENCES board(id)
            );
            
            CREATE TABLE IF NOT EXISTS tag (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                
                FOREIGN KEY (item_id) REFERENCES board_item(id)
            );
            
            CREATE TABLE IF NOT EXISTS note (
                id INTEGER PRIMARY KEY,
                content TEXT NOT NULL,
                
                FOREIGN KEY (id) REFERENCES board_item(id)
            );
            
            CREATE TABLE IF NOT EXISTS page (
                id INTEGER PRIMARY KEY,
                content TEXT NOT NULL,
                
                FOREIGN KEY (id) REFERENCES board_item(id)
            );
            
            CREATE TABLE IF NOT EXISTS image (
                id INTEGER PRIMARY KEY,
                image BLOB NOT NULL,
                
                FOREIGN KEY (id) REFERENCES board_item(id)
            );
        """
        )

        self.conn.commit()

    def get_all_board_ids(self):
        return self._query("SELECT id FROM board")

    def get_boards(self):
        return self._query("SELECT * FROM board")

    def get_board(self, id: int):
        return self._query("SELECT * FROM board WHERE id=?", data=(id,))

    def get_board_previews(self):
        # TODO: Remove this method and test code
        
        # dates = [
        #     datetime(2025, 3, 10, 14, 30, 0),
        #     datetime(2025, 2, 21, 18, 20, 1),
        #     datetime(2024, 12, 6, 20, 20, 21),
        #     datetime(2024, 8, 2, 10, 51, 41),
        #     datetime(2025, 1, 28, 15, 11, 58),
        #     datetime(2025, 3, 10, 14, 30, 0),
        #     datetime(2025, 2, 21, 18, 20, 1),
        #     datetime(2024, 12, 6, 20, 20, 21),
        #     datetime(2024, 8, 2, 10, 51, 41),
        #     datetime(2025, 1, 28, 15, 11, 58),
        # ]

        # board_previews = [
        #     (1, "Programming", dates[0]),
        #     (2, "Recipes", dates[1]),
        #     (3, "Reminders", dates[2]),
        #     (4, "ITOOA Notes", dates[3]),
        #     (5, "2025 Goals", dates[4]),
        #     (6, "momomomoumoumou", dates[5]),
        #     (7, "Recipes", dates[6]),
        #     (8, "Reminders", dates[7]),
        #     (9, "ITOOA Notes", dates[8]),
        #     (10, "2025 Goals", dates[9]),
        #     (11, "Programming", dates[1]),
        #     (12, "Recipes", dates[2]),
        #     (13, "Reminders", dates[3]),
        #     (14, "ITOOA Notes", dates[4]),
        #     (15, "2025 Goals", dates[5]),
        # ]
        pass

    def get_open_boards(self):
        open_ids = get_setting("OPEN_TABS")
        self._query(f"SELECT * FROM board WHERE id IN ({", ".join("?" * len(open_ids))})", open_ids)

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

    def _query(self, sql: str, type: QueryTypes = QueryTypes.SINGLE, data=None):
        c = self.conn.cursor()
        
        if type == QueryTypes.SINGLE:
            c.execute(sql, data or ())
        elif type == QueryTypes.MANY:
            c.executemany(sql, data)
        elif type== QueryTypes.SCRIPT:
            c.executescript(sql)
        else:
            raise ValueError(f"Query type '{type}' not recognized. Use QueryTypes enum to see relevant types")
        
        return c.fetchall()
        
    def _execute(self, sql: str, type: QueryTypes = QueryTypes.SINGLE, data=None):
        c = self.conn.cursor()
        
        if type == QueryTypes.SINGLE:
            c.execute(sql, data or ())
        elif type == QueryTypes.MANY:
            c.executemany(sql, data)
        elif type== QueryTypes.SCRIPT:
            c.executescript(sql)
        else:
            raise ValueError(f"Query type '{type}' not recognized. Use QueryTypes enum to see relevant types")
        
        self.conn.commit()
        return c.rowcount
        