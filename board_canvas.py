import tkinter as tk
from typing import List
from colours import *
from PIL import Image as PILImage
import math
from shared_widgets import *
from utilities import resize_image
from dataclasses import dataclass

"""
The board_canvas file and BoardCanvas (BC) class is responsible for and keep state of the canvas AND its board items
The BC can be thought of as the View component in MVC pattern, where the BoardHandler is the Controller and the Board model
(models.py) is, of course, the model.
"""


class BoardCanvas(tk.Canvas):

    @dataclass(slots=True)
    class ZoomPoint:
        x: int
        y: int

    def __init__(self, parent, item_models=[]):
        super().__init__(parent, background=ORANGE, highlightthickness=0)

        self.previously_opened = False
        self.observers = []
        self.img = None
        self.photo_image = None
        self.width = 0
        self.height = 0

        self.board_items: List[BoardItemWidget] = []
        if item_models != []:
            for model in item_models:
                widget = self.item_model_to_widget(model)
                self.board_items.append(widget)

        # Local x and Local y: These values represent the distance between the zoom point and the nearest left and nearest top borders of the cell/image
        self.lx = 0
        self.ly = 0

        # Using dataclass with __slots__ for optimal attribute access time

        self.zoom_point = self.ZoomPoint(0, 0)
        self.last_zoom_point = self.ZoomPoint(0, 0)

        self.cell_width = 800
        self.cell_height = 0

        self.zoom_scale = 1
        self.last_scale = self.zoom_scale
        self.scale_step = 0.1
        self.max_scale = 1.7
        self.min_scale = 0.2

        self.x_scale_offset = 0
        self.y_scale_offset = 0

        self.left = 0
        self.right = 0
        self.top = 0
        self.bottom = 0

        # Anchors/Edges
        self.top_anchor = 0
        self.right_anchor = 0
        self.bottom_anchor = 0
        self.left_anchor = 0

        self.set_bindings()

    def initial_setup(self):
        self.update_idletasks()
        self.width = self.winfo_width()
        self.height = self.winfo_height()
        self.set_texture()
        self.show_items()

        self.right_anchor = self.width * (2 - self.min_scale) + 100
        self.bottom_anchor = self.height * (2 - self.min_scale) + 50

    def add_board_item(self, item: BoardItem):
        item_widget = self.item_model_to_widget(item)
        self.board_items.append(item_widget)
        item_widget.show()

    def item_model_to_widget(self, item: BoardItem):
        if isinstance(item, Note):
            return NoteWidget(self, item)
        elif isinstance(item, Image):
            return ImageWidget(self, item)
        elif isinstance(item, Page):
            return PageWidget(self, item)
        else:
            raise ValueError(f"Cannot convert item '{item} to any sort of BoardItem widget'")

    def set_texture(self):
        self.img = PILImage.open("assets/images/pinboard_background.png")
        self.photo_image = resize_image(self.img, self.cell_width)
        self.cell_height = self.photo_image.height()

        self._redraw_canvas()

    def set_bindings(self):
        self.bind("<MouseWheel>", self.wheel)
        self.bind("<Configure>", self.resize_canvas)

    def wheel(self, event: tk.Event):
        self.zoom(event.delta / 120, (int(event.x), int(event.y)))

    def zoom(self, delta, point):
        self.last_scale = self.zoom_scale
        self.zoom_scale = round((self.zoom_scale + delta * self.scale_step), 2)

        if self.zoom_scale > self.max_scale:
            self.zoom_scale = self.max_scale
        elif self.zoom_scale < self.min_scale:
            self.zoom_scale = self.min_scale
        else:
            self.last_zoom_point.x, self.last_zoom_point.y = self.zoom_point.x, self.zoom_point.y
            self.zoom_point.x, self.zoom_point.y = point
            self._calculate_borders()
            self._redraw_canvas()
            self.offset_and_scale_items()

    def _draw_image(self, x: int, y: int):
        self.create_image(x, y, image=self.photo_image, tags="tile")

    def _calculate_borders(self):
        # Calculate Local x (lx) and Local y (ly)
        self.delete("line")

        x = self.zoom_point.x
        cw = self.cell_width
        dx = x - self.last_zoom_point.x + self.lx
        x_nearest = self.last_zoom_point.x - self.lx + int(dx / cw) * cw
        self.lx = (x - x_nearest + cw) % cw

        y = self.zoom_point.y
        ch = self.cell_height
        dy = y - self.last_zoom_point.y + self.ly
        y_nearest = self.last_zoom_point.y - self.ly + int(dy / ch) * ch
        self.ly = (y - y_nearest + ch) % ch

        # Calculate co-ordinates of borders
        self.left = int(x - self.lx * self.zoom_scale)
        self.right = int(self.left + cw * self.zoom_scale)
        self.top = int(y - self.lx * self.zoom_scale)
        self.bottom = int(self.top + ch * self.zoom_scale)

    def _redraw_canvas(self):
        self.delete("tile")

        scaled_cell_width = int(self.cell_width * self.zoom_scale)
        scaled_cell_height = int(self.cell_height * self.zoom_scale)

        self.photo_image = resize_image(self.img, scaled_cell_width)
        # Left Side
        x = self.left
        while x > 0 - scaled_cell_width:
            # Top & Bottom
            y = self.top
            while y > 0 - scaled_cell_height:
                self._draw_image(x, y)
                y -= scaled_cell_height
            y = self.bottom
            while y < self.height + scaled_cell_width:
                self._draw_image(x, y)
                y += scaled_cell_height
            x -= scaled_cell_width

        # Right side
        x = self.right
        while x < self.width + scaled_cell_width:
            # Top & Bottom
            y = self.top
            while y > 0 - scaled_cell_height:
                self._draw_image(x, y)
                y -= scaled_cell_height
            y = self.bottom
            while y < self.height + scaled_cell_height:
                self._draw_image(x, y)
                y += scaled_cell_height
            x += scaled_cell_width

    def resize_canvas(self, _event):
        if self.img:
            self.update_idletasks()
            self.width = self.winfo_width()
            self.height = self.winfo_height()
            self._redraw_canvas()

    def show_items(self):
        if self.board_items:
            for item in self.board_items:
                item.show()

    def hide_items(self):
        if not self.board_items:
            raise ValueError("No items to hide. 'self.board_items' is empty.")

        for item in self.board_items:
            item.hide()

    def offset_and_scale_items(self):
        for item in self.board_items:
            # change in zoom level
            dx = item.scaled_x + item.width / 2 - self.zoom_point.x
            dy = item.scaled_y + item.height / 2 - self.zoom_point.y
            # Calculate new dx and dy by first rescaling it to default size and then calculating the next dx and dy
            new_dx = dx / self.last_scale * self.zoom_scale
            new_dy = dy / self.last_scale * self.zoom_scale

            x = self.zoom_point.x + new_dx
            y = self.zoom_point.y + new_dy

            # Scale before using calculating top-left co-ordinates
            item.scale(self.zoom_scale)
            x = x - item.width / 2
            y = y - item.height / 2

            item.show(x=x, y=y)

    def open(self):
        self.grid(row=1, column=1, sticky="nsew")
        if not self.previously_opened:
            self.initial_setup()

    def close(self):
        self.grid_forget()

    def destroy(self):
        for item in self.board_items:
            item.destroy()
        return super().destroy()
