from abc import abstractmethod
from utilities import bytes_to_image, get_display_size, random_colour
from colours import *

class Board():
    def __init__(self, id, name, date_created, board_items: list):
        self.id = id
        self.name = name
        self.date_created = date_created
        self.board_items = board_items
        
        self.saved = True
        
class BoardItem():
    def __init__(self, item_id, title, colour, tags, date_created, x, y):
        self.item_id = item_id
        self.title = title
        self.colour = colour
        self.tags: set[str] = set(tags)
        self.date_created = date_created        
        self.x = x
        self.y = y
        
        self.changed = False
        
class Note(BoardItem):
    def __init__(self, item_id, title, date_created, content, x, y, colour=None, tags = []):
        colour = colour or random_colour()
        super().__init__(item_id, title, colour, tags, date_created, x, y)
        
        self.content = content
        
class Page(BoardItem):
    def __init__(self, item_id, title, date_created, content, x, y, colour=WHITE, tags = []):
        super().__init__(item_id, title, colour, tags, date_created, x, y)
        
        self.content = content
        
class Image(BoardItem):
    def __init__(self, item_id, title, date_created, image_bytes: bytes, x, y, colour=WHITE, tags = []):
        super().__init__(item_id, title, colour, tags, date_created, x, y)
        
        self.image = bytes_to_image(image_bytes)
        
