from abc import abstractmethod
import tkinter as tk
from tkinter import font
from colours import *
from models import *
from utilities import add_bg_colour_hover_effect, add_hover_effect, get_display_size, get_setting
import customtkinter as ctk

DEVICE_SCALE_FACTOR = get_setting("DEVICE_SCALE_FACTOR")


class CloseButton(ctk.CTkCanvas):

    def __init__(
        self,
        parent,
        button_size,
        icon_size,
        command,
        colour=WHITE,
        hover_effect: bool = True,
        thickness=3,
        rounding=1,
        colourVar: tk.StringVar = None,
    ):
        self.original_bg = parent.cget("background") if colourVar is None else colourVar.get()
        super().__init__(
            parent,
            width=button_size,
            height=button_size,
            background=self.original_bg,
            highlightthickness=0,
        )
        self.command = command
        self.button_size = button_size
        self.icon_size = icon_size
        self.thickness = thickness

        self.draw_x(colour)
        self.bind("<Button-1>", self.on_click)
        if hover_effect:
            add_hover_effect(
                widget=self,
                rounding=rounding,
                shape="square",
                restore_foreground_command=lambda: self.draw_x(colour),
            )

    def on_click(self, _event):
        if callable(self.command):
            self.command()
        else:
            raise ValueError("Provided 'command' argument is not callable")

    def draw_x(self, colour):
        offset = (self.button_size - self.icon_size) / 2
        self.create_line(
            offset,
            offset,
            self.button_size - offset,
            self.button_size - offset,
            width=self.thickness,
            fill=colour,
        )
        self.create_line(
            offset,
            self.button_size - offset,
            self.button_size - offset,
            offset,
            width=self.thickness,
            fill=colour,
        )


class ContextMenu(tk.Frame):
    # This class should be instantiated when the application is opened but the
    #   widget itself should not be shown until the "open_menu" method is called

    _instance = None
    window = None
    surface = None
    buttons = None
    registry: dict = {}

    @staticmethod
    def get_instance():
        if ContextMenu._instance is None:
            ContextMenu()
        return ContextMenu._instance

    def __init__(self):
        if ContextMenu._instance is not None:
            raise Exception("TabHandler class is a singleton. An instance already exists")
        else:
            ContextMenu._instance = self

    def create_surface(self):
        self.surface = tk.Frame(self, background=PRIMARY_COLOUR)
        self.surface.pack(fill="both", padx=(1, 1), pady=(1, 1), expand=True)

    def set_window(self, window: tk.Tk):
        self.window = window
        super().__init__(window, width=400, bg=HIGHLIGHT_COLOUR)
        self.create_surface()

    def register(self, context: tk.Widget, buttons: tuple[tk.Frame]):
        self.registry[context] = buttons

    def deregister(self, context: tk.Widget):
        try:
            del self.registry[context]
        except:
            raise Exception(
                f'Context "<{context}>" not found in context menu registry and therefore cannot be deregistered'
            )

    def open_menu(self, context: tk.Widget, event: tk.Event):
        self.hide_buttons()

        try:
            self.buttons = self.registry[context]
        except KeyError as e:
            raise Exception(f'Context {context} not registered. Register context before calling "open_menu"')

        if not self.buttons:
            return

        for button in self.buttons:
            button.pack(side="top", fill="x", padx=(2, 2), pady=(0, 2))

        x = event.x_root - self.window.winfo_x()
        y = event.y_root - self.window.winfo_y()
        self.place(x=x, y=y)
        self.tkraise()

        # Set binding to close popup if user clicks off context menu
        self.window.bind("<1>", lambda event: self.close_popup())

    def button(self, label, command):
        button = tk.Frame(self.surface, bg=PRIMARY_COLOUR)
        ctk_label = ctk.CTkLabel(
            button,
            text=label,
            fg_color=PRIMARY_COLOUR,
            font=ctk.CTkFont(family="Helvetica", size=16),
            height=26,
        )
        ctk_label.pack(side="left", padx=(4, 2))

        button.bind("<Button-1>", command)
        ctk_label.bind("<Button-1>", command)

        add_bg_colour_hover_effect(button, partners=(ctk_label, button))
        return button

    def close_popup(self):
        self.hide_buttons()

        self.window.unbind("<1>")
        self.place_forget()

    def hide_buttons(self):
        if self.buttons:
            for button in self.buttons:
                button.pack_forget()


class SingleInputWindow:

    def __init__(self, width=350, height=180):
        # Create and position window
        top = tk.Toplevel(highlightthickness=4, highlightbackground=BORDER_COLOUR)
        sc_width, sc_height = get_display_size()
        w_width, w_height = width, height
        x_offset = int(sc_width / 2.0 - w_width / 2.0)
        y_offset = int(sc_height / 2.0 - w_height * 2)
        top.wm_geometry(f"{w_width}x{w_height}+{x_offset}+{y_offset}")

        # Set up title bar
        top.overrideredirect(1)

        # Set up background frame
        bg_frame = tk.Frame(top, bg=PRIMARY_COLOUR)
        bg_frame.pack(fill="both", expand=True)
        close_button = CloseButton(bg_frame, 30, 15, top.destroy)
        close_button.pack(side="right", anchor="n", padx=(0, 5))

        # Set up grid for label and text field
        # bg_frame.rowconfigure(index=0, weight=)

        # Set up text field
        txt_input = tk.Text(bg_frame, highlightbackground=BORDER_COLOUR, highlightthickness=2)
        # txt_input.


class BoardItemWidget(tk.Frame):
    def __init__(self, canvas, width, height, item: BoardItem, **kwargs):
        self.original_width = width
        self.original_height = height
        self.width = width
        self.height = height
        self.item = item

        self.scale_factor = 1
        self.native_x = self.item.x * DEVICE_SCALE_FACTOR
        self.native_y = self.item.y * DEVICE_SCALE_FACTOR
        self.scaled_x = self.native_x
        self.scaled_y = self.native_y

        super().__init__(canvas, width=width, height=height, **kwargs)

    def scale(self, factor=1.0):
        self.scale_factor = factor
        self.width = self.original_width * factor
        self.height = self.original_height * factor

        self.scale_font()
        self.configure(width=self.width, height=self.height)

    def show(self, x=None, y=None):
        if x != None:
            self.scaled_x = x
        if y != None:
            self.scaled_y = y
        self.place(x=self.scaled_x, y=self.scaled_y)

    def hide(self):
        self.place_forget()

    def displace(self, dx, dy):
        self.hide()
        self.item.x += dx / self.scale_factor
        self.item.y += dy / self.scale_factor
        self.scaled_x += dx
        self.scaled_y += dy
        self.show()

    @abstractmethod
    def scale_font(self):
        pass


class NoteWidget(BoardItemWidget):

    def __init__(self, canvas, item: Note):
        width = 280 * DEVICE_SCALE_FACTOR
        height = 280 * DEVICE_SCALE_FACTOR
        font_scale = int(12 * DEVICE_SCALE_FACTOR)
        super().__init__(canvas, width, height, item, bg=item.colour, highlightthickness=2, highlightbackground=BLACK)

        # Set up grid
        self.rowconfigure(index=0, weight=1, uniform="note_grid")
        self.rowconfigure(index=1, weight=2, uniform="note_grid")
        self.rowconfigure(index=2, weight=1, uniform="note_grid")
        self.rowconfigure(index=3, weight=12, uniform="note_grid")
        self.rowconfigure(index=4, weight=1, uniform="note_grid")
        self.columnconfigure(index=0, weight=1, uniform="note_grid")
        self.columnconfigure(index=1, weight=18, uniform="note_grid")
        self.columnconfigure(index=2, weight=1, uniform="note_grid")
        self.grid_propagate(False)

        self.title_label = tk.Label(
            self, bg=item.colour, font=("Commons", font_scale + 2, "bold"), text=self.item.title, anchor="w", pady=0
        )
        self.title_label.grid(row=1, column=1, sticky="nesw", padx=0, pady=0)

        self.text_widget = tk.Text(self, bg=item.colour, relief=tk.FLAT, font=("Dubai Medium", font_scale))
        self.text_widget.grid(row=3, column=1, sticky="nesw", padx=0, pady=0)
        self.text_widget.insert("1.0", item.content)

    def scale_font(self):
        font_scale = int(12 * self.scale_factor)
        self.title_label.config(font=("Commons", font_scale + 2, "bold"))
        self.text_widget.config(font=("Dubai Medium", font_scale))


class ImageWidget(BoardItemWidget):

    def __init__(self, canvas, item: Image):
        width = 400 * DEVICE_SCALE_FACTOR
        height = 300 * DEVICE_SCALE_FACTOR
        super().__init__(canvas, width, height, item, bg=WHITE, highlightthickness=2, highlightbackground=BLACK)


class PageWidget(BoardItemWidget):

    def __init__(self, canvas, item: Page):
        width = 280 * DEVICE_SCALE_FACTOR
        height = 400 * DEVICE_SCALE_FACTOR
        font_scale = int(12 * DEVICE_SCALE_FACTOR)
        super().__init__(canvas, width, height, item, bg=WHITE, highlightthickness=2, highlightbackground=BLACK)
