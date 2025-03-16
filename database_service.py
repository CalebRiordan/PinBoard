from datetime import datetime
from utilities import _create_mock_data
import models


class DatabaseService:

    # temp
    _boards = None

    # cache
    _board_previews = []

    def __init__(self):
        # TODO: Set connection in future?
        self._boards = _create_mock_data()

    def set_connection():
        raise ValueError("Not implemented yet")

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
