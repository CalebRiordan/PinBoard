from utilities import _create_mock_data
import models

class DatabaseService:

    # temp
    _boards = None

    def __init__(self):
        # TODO: Set connection in future?
        self._boards = _create_mock_data()
    
    # def set_connection():
    #     raise ValueError("Not implemented yet")

    def get_all_board_ids(self):
        pass
    
    def get_boards(self):
        return _create_mock_data()
    
    def get_board(self, id: int):            
        for board in self._boards:
            if board.board_id == id:
                return board
        return None
    
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

        
        
        
        