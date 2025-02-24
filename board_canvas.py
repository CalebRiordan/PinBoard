import time
import tkinter as tk
from typing import List
from colours import *
from PIL import Image as PILImage
import math
from shared_widgets import *
from utilities import resize_image, _draw_image_test
from dataclasses import dataclass

"""
The board_canvas file and BoardCanvas (BC) class is responsible for and keep state of the canvas AND its board items
The BC can be thought of as the View component in MVC pattern, where the BoardHandler is the Controller and the Board model
(models.py) is, of course, the model.
"""


class BoardCanvas(tk.Canvas):
    # Using dataclass with __slots__ for optimal attribute access time
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

        # Zooming
        # Local x and Local y: These values represent the distance between the zoom point and the nearest left and nearest top borders of the cell/image
        self.lx = 0
        self.ly = 0

        self.zoom_point = self.ZoomPoint(0, 0)
        self.last_zoom_point = self.ZoomPoint(0, 0)

        self.cell_width = 800
        self.cell_height = 0

        self.zoom_scale = 1
        self.last_scale = self.zoom_scale
        self.scale_step = 0.1
        self.max_scale = 1.7
        self.min_scale = 0.5

        self.left = 0
        self.right = 0
        self.top = 0
        self.bottom = 0

        # Anchors/Edges
        self.top_anchor = -100
        self.right_anchor = 0
        self.bottom_anchor = 0
        self.left_anchor = -100
        self.adj_x = 0
        self.adj_y = 0

        # Pan
        self.last_x = 0
        self.last_y = 0
        self.move_x = 0
        self.move_y = 0
        self.last_update_time = 0
        self.update_threshold = 0.032

        self.set_bindings()

    def initial_setup(self):
        self.update_idletasks()
        self.width = self.winfo_width()
        self.height = self.winfo_height()
        self.set_texture()
        self.show_items()

        self.right_anchor = self.width * 2.5
        self.bottom_anchor = self.height * 2.5

        self.bind("<1>", self.start_pan)
        self.bind("<B1-Motion>", self.pan)
        self.bind("<ButtonRelease>", self.reset_pan)

    def _test_zoom(self):
        for i in range(5):
            self.zoom(-1, (1, 1))

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
            self.photo_image = resize_image(
                self.img, int(max(self.cell_width * self.zoom_scale, self.cell_height * self.zoom_scale))
            )

            self._set_boundary_adjustments()
            self._calculate_borders()
            self.offset_and_scale_items()
            self._redraw_canvas()

    def _draw_image(self, x: int, y: int):
        self.create_image(x, y, image=self.photo_image, tags="tile")
        # _draw_image_test(self, x, y, self.cell_width, self.cell_height, self.zoom_scale)

    def _set_boundary_adjustments(self):
        x = self.zoom_point.x
        y = self.zoom_point.y
        # Create anchors at all four corners
        self.top_anchor = y - (y - self.top_anchor) / self.last_scale * self.zoom_scale
        self.right_anchor = x - (x - self.right_anchor) / self.last_scale * self.zoom_scale
        self.bottom_anchor = y - (y - self.bottom_anchor) / self.last_scale * self.zoom_scale
        self.left_anchor = x - (x - self.left_anchor) / self.last_scale * self.zoom_scale

        self._adjust_boundaries()

    def _adjust_boundaries(self):
        self.adj_x = 0
        self.adj_y = 0

        if self.top_anchor > 0:
            self.adj_y = -self.top_anchor
        elif self.bottom_anchor < self.height:
            self.adj_y = self.height - self.bottom_anchor

        if self.left_anchor > 0:
            self.adj_x = -self.left_anchor
        elif self.right_anchor < self.width:
            self.adj_x = self.width - self.right_anchor

        self.top_anchor += self.adj_y
        self.right_anchor += self.adj_x
        self.bottom_anchor += self.adj_y
        self.left_anchor += self.adj_x

    def _calculate_borders(self):
        # Calculate Local x (lx) and Local y (ly)
        print()
        x = self.zoom_point.x
        cw = self.cell_width * self.last_scale
        dx = x - self.last_zoom_point.x + self.lx
        x_nearest = self.last_zoom_point.x - self.lx + int(dx / cw) * cw
        self.lx = (x - x_nearest + cw) % cw / self.last_scale * self.zoom_scale

        y = self.zoom_point.y
        ch = self.cell_height * self.last_scale
        dy = y - self.last_zoom_point.y + self.ly
        y_nearest = self.last_zoom_point.y - self.ly + int(dy / ch) * ch
        self.ly = (y - y_nearest + ch) % ch / self.last_scale * self.zoom_scale

        # Calculate co-ordinates of borders
        self.top = int(y - self.ly + self.adj_y)
        self.left = int(x - self.lx + self.adj_x)
        self.bottom = int(self.top + ch / self.last_scale * self.zoom_scale)
        self.right = int(self.left + cw / self.last_scale * self.zoom_scale)

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
            x = x - item.width / 2 + self.adj_x
            y = y - item.height / 2 + self.adj_y
            item.show(x=x, y=y)
        self.zoom_point.x += self.adj_x
        self.zoom_point.y += self.adj_y

    def _redraw_canvas(self):
        self.delete("tile")

        scaled_cell_width = int(self.cell_width * self.zoom_scale)
        scaled_cell_height = int(self.cell_height * self.zoom_scale)
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

    def start_pan(self, e: tk.Event):
        self.last_x = e.x
        self.last_y = e.y
        self.last_update_time = time.time()

    def pan(self, e: tk.Event):
        self.move_x = e.x - self.last_x
        self.move_y = e.y - self.last_y
        current_time = time.time()

        if current_time - self.last_update_time > self.update_threshold:
            # Move boundaries
            self.top_anchor += self.move_y
            self.right_anchor += self.move_x
            self.bottom_anchor += self.move_y
            self.left_anchor += self.move_x
            self._adjust_boundaries()

            self.move_x += self.adj_x
            self.move_y += self.adj_y

            if self.move_x != 0 or self.move_y != 0:
                # Move zoom points
                self.last_zoom_point.x += self.move_x
                self.last_zoom_point.y += self.move_y
                self.zoom_point.x += self.move_x
                self.zoom_point.y += self.move_y

                # Move canvas objects and widgets
                self.move("tile", self.move_x, self.move_y)
                for item in self.board_items:
                    item.pan(self.move_x, self.move_y)
                self.reset_pan(e)
                self._calculate_borders()
                self._redraw_canvas()

            self.last_x = e.x
            self.last_y = e.y
            self.last_update_time = current_time

    def reset_pan(self, e: tk.Event):
        self.move_x = 0
        self.move_y = 0

    def show_items(self):
        if self.board_items:
            for item in self.board_items:
                item.show()

    def hide_items(self):
        if not self.board_items:
            raise ValueError("No items to hide. 'self.board_items' is empty.")

        for item in self.board_items:
            item.hide()

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
