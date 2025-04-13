from services.database_service import DatabaseService
from datetime import date
from app.board_canvas import BoardCanvas
from app.models import *
from services.service_locator import Services
from typing import Dict

class BoardHandler:
    # maintain list of Board objects
    _open_boards: Dict[int, Board] = {}
    _current_board: Board = None
    _open_canvases: Dict[int, BoardCanvas] = {}
    _canvas_parent = None
    _all_boards_ids = []

    """
        The BoardHandler (BH) is a singleton class responsible for managing boards, including the items stored within a board.
        It interacts primarily with the BoardCanvas to translate logic item models into viewable widgets and the TabHandler to
        keep track of which boards should be open and displayed.
        The steps involved in
    """

    def __init__(self, canvas_parent):
        self._canvas_parent = canvas_parent
        self.db_service: DatabaseService = Services.get("DatabaseService")

    def initialize_boards(self):
        # Create sublist for boards that are OPEN
        open_boards = self.db_service.get_open_boards()
        self._all_boards_ids = self.db_service.get_all_board_ids()

        return open_boards or []

    def get_board(self, board_id):
        if board_id in self._open_boards.keys():
            return self._open_boards[board_id]
        else:
            try:
                return self.db_service.get_board(board_id)
            except:
                raise ValueError(f"Board with id {board_id} does not exist")

    def swap_boards(self, board_id):

        # Swapping boards involves:
        # swap_boards
        #  1: Check if self.current_board exists
        #  2. Close canvas for current board
        # show_board(board_id)
        #  3. Change self.current_board to new board using board_id
        #  4. Open relavant canvas in _open_canvases dictionary

        if self._current_board is not None:
            self.current_canvas().close()

        self.show_board(board_id)

    def show_board(self, id):
        if id in self._open_boards.keys():
            self._current_board = self._open_boards[id]
            self.current_canvas().open()
            self.set_side_panel_context()
            self.current_canvas().bind("<1>", self.set_side_panel_context, add=True)
        else:
            raise ValueError(
                f"Board with id '{id}' not found amongst currently open boards"
            )

    def new_board(self):
        new_board = Board(None, "", date.today(), [])
        new_board.saved = False
        self.db_service.create_board(new_board)
        self._open_boards[new_board.id] = new_board
        self._open_canvases[new_board.id] = BoardCanvas(self._canvas_parent)
        self._all_boards_ids.append(new_board.id)
        return new_board

    def open_board(self, id: int):
        """
        Retrieves board with provided ID from database and adds it to list of open boards. Also creates a corresponding BoardCanvas
        """
        if not id in self._open_boards:
            board: Board = self.db_service.get_board(id)
            if board:
                self._open_boards[id] = board
                self._open_canvases[id] = BoardCanvas(self._canvas_parent, board.board_items)
            else:
                raise ValueError(f"Board with id '{id} does not exist'")

    def close_board(self, board_id=-1, next_board_id=-1):
        """
        Removes board from of open boards and destroys corresponding canvas
        Optionally shows a different board after the initial one is closed
        """

        if board_id == -1:
            if self._current_board != None:
                board_id = self._current_board.id
            else:
                raise ValueError(
                    f"No current board set - Please specify a board id for the board to close."
                )
        try:
            self._open_boards.pop(board_id)
            self._open_canvases[board_id].destroy()
            self._open_canvases.pop(board_id)
        except:
            raise ValueError(f"Board with id {board_id} does not exist")
        if next_board_id != -1:
            self.show_board(next_board_id)

    def save_board(self, board_id, name=""):
        if board_id in self._open_boards.keys():
            board = self._open_boards[board_id]
            if name != "":
                board.name = name

            # TODO: Update board and all it's items in database
            board.saved = True
            return True
        else:
            raise ValueError(f"No open board with ID {board_id} exists.")

    def current_canvas(self):
        return self._open_canvases[self._current_board.id]

    def set_side_panel_context(self, event=None):
        sp = Services.get("SidePanel")
        sp.set_context(sp.Contexts.BOARD, self._current_board)
