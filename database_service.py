from datetime import datetime
from enum import Enum
import os
from typing import List
from utilities import get_setting
import models
import sqlite3
import models


class QueryTypes(Enum):
    """
    Enum representing the types of sqlite3 execution methods:
        SINGLE -> execute,
        MANY -> executemany,
        SCRIPT -> executescript
    """

    SINGLE = "execute"
    MANY = "executemany"
    SCRIPT = "executescript"


class DatabaseService:

    conn: sqlite3.Connection = None

    # cache
    _boards: List[models.Board] = []

    def __init__(self, db_name=None):
        if db_name:
            self.set_connection(db_name=db_name)

    def set_connection(self, db_name):
        self.conn = sqlite3.connect(f"{db_name}.db")
        self.conn.execute("PRAGMA foreign_keys = ON;")

    def create_tables(self):
        c = self.conn.cursor()

        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS board (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
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
                FOREIGN KEY (board_id) REFERENCES board(id) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS tag (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                
                FOREIGN KEY (item_id) REFERENCES board_item(id) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS note (
                id INTEGER PRIMARY KEY,
                content TEXT NOT NULL,
                
                FOREIGN KEY (id) REFERENCES board_item(id) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS page (
                id INTEGER PRIMARY KEY,
                content TEXT NOT NULL,
                
                FOREIGN KEY (id) REFERENCES board_item(id) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS image (
                id INTEGER PRIMARY KEY,
                image BLOB NOT NULL,
                
                FOREIGN KEY (id) REFERENCES board_item(id) ON DELETE CASCADE
            );
        """
        )

        self.conn.commit()

    def get_all_board_ids(self):
        if self._boards:
            return [board.id for board in self._boards]
        return self._query("SELECT id FROM board;")

    def get_boards(self):
        """
        Returns a list of boards each including its items
        """
        if not self._boards:
            result = self._query("SELECT id, name, date_created FROM board;")
            for record in result:
                items = self.get_items(record[0])
                board = models.Board(record[0], record[1], record[2], items)
                self._boards.append(board)
        return self._boards

    def get_board(self, id: int):
        if not self._boards:
            record = next(
                iter(self._query("SELECT * FROM board WHERE id=?;", data=(id,))), None
            )
            if record:
                items = self.get_items(record[0])
                return models.Board(record[0], record[1], record[2], items)
            return None

        return next(iter(board for board in self._boards if board.id == id), None)

    def get_open_boards(self):
        open_ids = get_setting("OPEN_TABS")

        boards = self.get_boards()
        if boards:
            return [board for board in boards if board.id not in open_ids] or None
        return None

    def create_board(self, board: models.Board):
        """
        Create a new record in the Board table
        Note: Modifies board object's ID attribute with ID stored generated by SQLite
        """

        cursor = self._execute(
            "INSERT INTO board (name, date_created) VALUES (?, ?);",
            data=(
                board.name,
                board.date_created,
            ),
        )
        board.id = cursor.lastrowid
        self._boards.append(board)

    def save_board_items(self, board: models.Board):
        if not board.saved:
            # board contains unsaved items
            changes = []
            for item in board.board_items:
                if item.changed:
                    changes.append(
                        (item.title, item.colour, item.x_pos, item.y_pos, item.id)
                    )
                    item.changed = False

            if changes:
                self._execute(
                    sql="UPDATE board_item SET title = ?, colour = ?, x_pos= ?, y_pos= ? WHERE id =?;",
                    type=QueryTypes.MANY,
                    data=changes,
                )

    def update_board_name(self, id, name):
        self._execute(
            "UPDATE board SET name=? WHERE id=?",
            data=(
                name,
                id,
            ),
        )

    def delete_board(self, id: int):
        """
        Removes board with provided ID from database and cache. NB: Assumes boards are stored in cache already
        """
        for board in self._boards:
            if board.id == id:
                self._execute("DELETE * FROM board WHERE id=?", data=(id,))
                self._boards.remove(board)
                return
        raise ValueError(f"No board with id '{id}' exists")

    def get_item(self, id):
        result = next(
            (
                self._query(
                    "SELECT id, title, colour, date_created, x_pos, y_pos FROM board_item WHERE id=?",
                    data=(id,),
                )
            ),
            None,
        )

        if result:
            tags = [
                tag[0]
                for tag in self._query(
                    "SELECT text FROM tag WHERE item_id=?", data=(result[0],)
                )
            ]
            return models.BoardItem(
                result[0],
                result[1],
                result[2],
                tags,
                result[3],
                result[4],
                result[5],
            )

        return None

    def get_items(self, board_id):
        notes = self._query(
            """
            SELECT bi.id, bi.title, bi.date_created, n.content, bi.x_pos, bi.y_pos, bi.colour
            FROM board_item bi
            LEFT JOIN note n ON bi.id = n.id
            WHERE board_id=? AND bi.type = 'note';
            """,
            data=(board_id,),
        )
        pages = self._query(
            """
            SELECT bi.id, bi.title, bi.date_created, p.content, bi.x_pos, bi.y_pos, bi.colour
            FROM board_item bi
            LEFT JOIN page p ON bi.id = p.id
            WHERE board_id=? AND bi.type = 'page';
            """,
            data=(board_id,),
        )
        images = self._query(
            """
            SELECT bi.id, bi.title, bi.date_created, i.image, bi.x_pos, bi.y_pos, bi.colour
            FROM board_item bi
            LEFT JOIN image i ON bi.id = i.id
            WHERE bi.board_id = ? AND bi.type = 'image'
            """,
            data=(board_id,),
        )
        all_tags = self._query(
            "SELECT i.id, t.text FROM board_item i JOIN tag t ON i.id = t.item_id WHERE i.board_id=?",
            data=(board_id,),
        )

        class_map = {
            "Note": models.Note,
            "Page": models.Page,
            "Image": models.Image,
        }

        def tuple_to_item(item, type):
            tags = [tag[1] for tag in all_tags if tag[0] == item[0]]
            return class_map.get(type)(*item, tags)

        items = []

        for note in notes:
            items.append(tuple_to_item(note, "Note"))
        for page in pages:
            items.append(tuple_to_item(page, "Page"))
        for image in images:
            items.append(tuple_to_item(image, "Image"))

        return items

    def _query(self, sql: str, type: QueryTypes = QueryTypes.SINGLE, data=None):
        c = self.conn.cursor()

        if type == QueryTypes.SINGLE:
            c.execute(sql, data or ())
        elif type == QueryTypes.MANY:
            c.executemany(sql, data)
        elif type == QueryTypes.SCRIPT:
            c.executescript(sql)
        else:
            raise ValueError(
                f"Query type '{type}' not recognized. Use QueryTypes enum to see relevant types"
            )

        return c.fetchall()

    def _execute(self, sql: str, type: QueryTypes = QueryTypes.SINGLE, data=None):
        c = self.conn.cursor()

        if type == QueryTypes.SINGLE:
            c.execute(sql, data or ())
        elif type == QueryTypes.MANY:
            c.executemany(sql, data)
        elif type == QueryTypes.SCRIPT:
            c.executescript(sql)
        else:
            raise ValueError(
                f"Query type '{type}' not recognized. Use QueryTypes enum to see relevant types"
            )

        self.conn.commit()
        return c
