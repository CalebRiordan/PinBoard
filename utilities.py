import random
import json
from io import BytesIO
from typing import List, Union, Iterable
from PIL import Image, ImageTk
from datetime import date
import tkinter as tk
from ctypes import windll
from colours import *
import customtkinter as ctk

__all__ = ["_create_mock_data"]

with open("app_settings.json", "r") as f:
    settings = json.load(f)

def resize_image(image: Image.Image, maximum_size: int):
    aspect_ratio = image.width / image.height

    if aspect_ratio >= 1:
        # Width > Height
        image_width = maximum_size
        image_height = int(image_width / aspect_ratio)
    else:
        # height > Width
        image_height = maximum_size
        image_width = int(image_height * aspect_ratio)

    return ImageTk.PhotoImage(image.resize((image_width, image_height)))

def get_setting(setting: str, default=None):
    return settings.get(setting, default)

def update_setting(key: str, value):
    if key in settings:
        settings[key] = value
        _write_settings_to_file()

def new_setting(key: str, value):
    if key not in settings:
        settings[key] = value
        _write_settings_to_file()
    else:
        raise Exception(f"setting '{key}' already exists.")

def get_display_size():
    # returns the width and height of the screen using a temporary Tk() instance
    root = tk.Tk()
    root.update_idletasks()
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    root.destroy()

    return width, height

def _write_settings_to_file():
    with open("app_settings.json", "w") as f:
        json.dump(settings, f, indent=4)

def bytes_to_image(image_bytes):
    input_stream = BytesIO(image_bytes)
    pil_image = Image.open(input_stream)
    return pil_image

def _create_test_image_bytes():
    img = Image.new("RGB", (100, 100), color="red")
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format="PNG")
    return img_byte_arr.getvalue()

def random_colour():
    colours = (
        STICKY_NOTE_YELLOW,
        STICKY_NOTE_PINK,
        STICKY_NOTE_BLUE,
        STICKY_NOTE_GREEN,
        STICKY_NOTE_ORANGE,
        STICKY_NOTE_PURPLE,
        STICKY_NOTE_MINT,
        STICKY_NOTE_LAVENDER,
        STICKY_NOTE_PEACH,
        STICKY_NOTE_RED,
        STICKY_NOTE_TEAL,
        STICKY_NOTE_GRAY,
    )
    return colours[random.randint(0, len(colours) - 1)]

def _create_mock_data():
    # Use lazy importing to avoid circular import error
    from models import Board, Note, Page, Image

    mock_image = _create_test_image_bytes
    # Create board items for Board 1
    board_1_items = [
        Note(1, "Note 1", date(2020, 5, 2), "This is the first note.", 20, 20),
        Page(2, "Page 1", date(2020, 5, 2), "This is the content of page 1.", 320, 100),
        Image(3, "Image 1", date(2020, 5, 2), _create_test_image_bytes(), 600, 500),
    ]

    # Create board items for Board 2
    board_2_items = [
        Note(4, "Note 2", date(2024, 3, 21), "This is the second note.", 40, 100),
        Page(
            5, "Page 2", date(2024, 3, 21), "This is the content of page 2.", 1000, 500
        ),
        Image(6, "Image 2", date(2024, 3, 21), _create_test_image_bytes(), 120, 350),
    ]

    # Create board items for Board 3
    board_3_items = [
        Note(7, "Note 3", date(2023, 1, 2), "This is the third note.", 300, 50),
        Page(8, "Page 3", date(2023, 1, 2), "This is the content of page 3.", 40, 550),
        Image(9, "Image 3", date(2023, 1, 2), _create_test_image_bytes(), 50, 100),
    ]

    # board_4_items = [
    #     Note(10, "Test Note", date(2023, 1, 2), "This is another note.", 1, 5),
    #     Note(11, "Test Note", date(2023, 1, 2), "This is another note.", 281, 5),
    #     Note(12, "Test Note", date(2023, 1, 2), "This is another note.", 561, 5),
    #     Note(13, "Test Note", date(2023, 1, 2), "This is another note.", 841, 5),
    #     Note(14, "Test Note", date(2023, 1, 2), "This is another note.", 1121, 5),
    #     Note(15, "Test Note", date(2023, 1, 2), "This is another note.", 1401, 5),
    #     Note(16, "Test Note", date(2023, 1, 2), "This is another note.", 1681, 5),
    #     Note(17, "Test Note", date(2023, 1, 2), "This is another note.", 1961, 5),
    #     Note(18, "Test Note", date(2023, 1, 2), "This is another note.", 2241, 5),
    #     Note(19, "Test Note", date(2023, 1, 2), "This is another note.", 2521, 5),
    # ]

    # Create boards with associated items
    all_boards = [
        Board(1, "First Board Long Name", date(2020, 5, 2), board_1_items),
        Board(2, "Second Board", date(2024, 3, 21), board_2_items),
        Board(3, "Third Board", date(2023, 1, 2), board_3_items),
        Board(
            4, "Fourth Board", date(2024, 10, 9), []
        ),  # No items for this board
    ]

    return all_boards

def _draw_image_test(canvas, x, y, cell_width, cell_height, zoom_scale):
    canvas.create_rectangle(
        x,
        y,
        x + int(cell_width * zoom_scale),
        y + int(cell_height * zoom_scale),
        fill=WHITE,
        outline=BLACK,
        tags="tile",
    )

def adjust_brightness(hex_colour, factor=0):
    factor /= 1.5

    def distribute_rgb(value, members: list):
        total = 0
        for m in members:
            total += 255 - m
        for i in range(len(members)):
            m = members[i]
            members[i] = int(m + (255 - m) / total * value)

        return tuple(members)

    hex_colour = hex_colour.lstrip("#")
    rgb = tuple(int(hex_colour[i : i + 2], 16) for i in (0, 2, 4))

    members = []
    for c in rgb:
        if c < 255:
            members.append(c)

    if len(members) == 3:  # All values are initially within 255
        adjusted_rgb = tuple(min(255, int(c + c * factor / 1.5)) for c in rgb)
    else:
        adjusted_rgb = distribute_rgb(255 * factor * 1.5, list(rgb))

    # Convert back to hex
    return "#{:02x}{:02x}{:02x}".format(*adjusted_rgb)

def ctk_font(size: int = 16, bold: bool = False):
    return ctk.CTkFont(family="Helvetica", size=size, weight="bold" if bold else None)

def rounded_square(canvas: tk.Canvas, shape_size, rounding=1, colour=WHITE):
    offset = (canvas.winfo_width() - shape_size) / 2
    r = rounding * shape_size / 2
    inner_bottom = offset + shape_size - r * 2

    # Draw sectors
    canvas.create_arc(
        offset,
        offset,
        offset + 2 * r,
        offset + 2 * r,
        extent=90,
        start=90,
        fill=colour,
        outline=colour,
    )
    canvas.create_arc(
        inner_bottom,
        offset,
        offset + shape_size,
        offset + 2 * r,
        extent=90,
        start=0,
        fill=colour,
        outline=colour,
    )
    canvas.create_arc(
        offset,
        inner_bottom,
        offset + 2 * r,
        offset + shape_size,
        extent=90,
        start=180,
        fill=colour,
        outline=colour,
    )
    canvas.create_arc(
        inner_bottom,
        inner_bottom,
        offset + shape_size,
        offset + shape_size,
        extent=90,
        start=270,
        fill=colour,
        outline=colour,
    )

    canvas.create_rectangle(
        offset + r,
        offset,
        offset + shape_size - r,
        offset + shape_size,
        fill=colour,
        outline=colour,
    )
    canvas.create_rectangle(
        offset,
        offset + r,
        offset + shape_size,
        offset + shape_size - r,
        fill=colour,
        outline=colour,
    )

def rounded_rectangle(canvas: tk.Canvas, width, height, rounding=1, colour=WHITE):
    canvas.update_idletasks()
    x_offset = (canvas.winfo_width() - width) / 2
    y_offset = (canvas.winfo_height() - height) / 2
    r = rounding * min(width, height) / 2
    inner_right_x = x_offset + width - r * 2
    inner_bottom_y = y_offset + height - r * 2

    # Draw sectors
    canvas.create_arc(
        x_offset,
        y_offset,
        x_offset + 2 * r,
        y_offset + 2 * r,
        extent=90,
        start=90,
        fill=colour,
        outline=colour,
    )
    canvas.create_arc(
        inner_right_x,
        y_offset,
        x_offset + width,
        y_offset + 2 * r,
        extent=90,
        start=0,
        fill=colour,
        outline=colour,
    )
    canvas.create_arc(
        x_offset,
        inner_bottom_y,
        x_offset + 2 * r,
        y_offset + height,
        extent=90,
        start=180,
        fill=colour,
        outline=colour,
    )
    canvas.create_arc(
        inner_right_x,
        inner_bottom_y,
        x_offset + width,
        y_offset + height,
        extent=90,
        start=270,
        fill=colour,
        outline=colour,
    )

    canvas.create_rectangle(
        x_offset + r,
        y_offset,
        x_offset + width - r,
        y_offset + height,
        fill=colour,
        outline=colour,
    )
    canvas.create_rectangle(
        x_offset,
        y_offset + r,
        x_offset + width,
        y_offset + height - r,
        fill=colour,
        outline=colour,
    )

def add_hover_commands(widgets: Union[tk.Widget, Iterable[tk.Widget]], enter_commands=(), leave_commands=()):
    if not isinstance(widgets, Iterable):  
        widgets = [widgets]
    
    if enter_commands is None:
        enter_commands = []
    elif callable(enter_commands):
        enter_commands = [enter_commands]

    if leave_commands is None:
        leave_commands = []
    elif callable(leave_commands):
        leave_commands = [leave_commands]

    def execute_enter_commands(_e):
        for command in enter_commands:
            if callable(command):
                command()

    def execute_leave_commands(_e):
        for command in leave_commands:
            if callable(command):
                command()

    for w in widgets:
        w.bind("<Enter>", execute_enter_commands, add=True)
        w.bind("<Leave>", execute_leave_commands, add=True)

def add_hover_effect(
    widgets: Union[tk.Widget, Iterable[tk.Widget]],
    shape: str,
    hover_colour=None,
    rounding=0,
    target_widget: tk.Canvas = None,
    margin=0,
    restore_foreground_command=None,
    partners=(),
):

    if not isinstance(widgets, Iterable):
        if isinstance(widgets, (tk.Canvas, ctk.CTkCanvas)) and not target_widget:
            target_widget = widgets
        elif not target_widget:
            raise Exception(
                "No target canvas provided ('target_widget' attribute) - 'widget' argument must therefore be a tk.Canvas"
            )
        widgets = [widgets]
    elif not target_widget:
        raise Exception("Multiple widgets provided - please specify a target canvas widget for the hover effect")
        
    previous_colour = target_widget.cget(tk_or_ctk_arguments(target_widget, "background"))
        
    for w in widgets:
        w.bind(
            "<Enter>", lambda event: hover_effect(True, target_widget, hover_colour)
        )
        w.bind(
            "<Leave>", lambda event: hover_effect(False, target_widget, hover_colour)
        )

    def hover_effect(mouse_enter, target_widget, hover_colour):
        nonlocal previous_colour

        effect_width = target_widget.winfo_width() - margin
        effect_height = target_widget.winfo_height() - margin

        if mouse_enter:
            if hover_colour is None:
                hover_colour = adjust_brightness(previous_colour, 0.2)

            if shape == "rectangle":
                rounded_rectangle(
                    target_widget, effect_width, effect_height, rounding, hover_colour
                )
            elif shape == "square":
                rounded_square(target_widget, effect_width, rounding, hover_colour)

            for w in partners:
                configure_widget(w, bg=hover_colour)

            if callable(restore_foreground_command):
                restore_foreground_command()
        else:
            target_widget.delete("all")  # clear canvas

            for w in partners:
                configure_widget(w, bg=previous_colour)

            if callable(restore_foreground_command):
                restore_foreground_command()

def add_bg_colour_hover_effect(
    widgets: Union[tk.Widget, Iterable[tk.Widget]], target_widgets: Union[tk.Widget, Iterable[tk.Widget]] = None, hover_colour=None
):
    previous_colour = None

    if not isinstance(widgets, Iterable):
        widgets = [widgets]
    if target_widgets is None:
        target_widgets = widgets
    elif not isinstance(target_widgets, Iterable):
        target_widgets = [target_widgets]
        
    for w in widgets:
        w.bind("<Enter>", lambda event: hover_effect(True, hover_colour, target_widgets), add=True)
        w.bind("<Leave>", lambda event: hover_effect(False, hover_colour, target_widgets), add=True)

    def hover_effect(mouse_enter, hover_colour, target_widgets):
        nonlocal previous_colour

        for target_widget in target_widgets:
            if mouse_enter:

                previous_colour = target_widget.cget(tk_or_ctk_arguments(target_widget, "background"))

                if hover_colour is None:
                    hover_colour = adjust_brightness(previous_colour, 0.2)

                configure_widget(target_widget, bg=hover_colour)
            else:
                configure_widget(target_widget, bg=previous_colour)

def remove_hover_effect(widgets: Union[tk.Widget, Iterable[tk.Widget]]):
    if not isinstance(widgets, Iterable):
        widgets = [widgets]
    for w in widgets:
        w.unbind("<Enter>")
        w.unbind("<Leave>")

def configure_widget(widget, **kwargs):
    mapping = {
        "bg": "fg_color",
        "background": "fg_color",
        "fg": "text_color",
        "foreground": "text_color",
        "font": "font",
        "bd": "border_width",
        "borderwidth": "border_width",
    }

    if isinstance(widget, ctk.CTkBaseClass):
        kwargs = {mapping.get(k, k): v for k, v in kwargs.items()}

    widget.configure(**kwargs)

def tk_or_ctk_arguments(widget, arg):
    mapping = {
        "bg": "fg_color",
        "background": "fg_color",
        "fg": "text_color",
        "foreground": "text_color",
        "font": "font",
        "bd": "border_width",
        "borderwidth": "border_width",
    }

    if isinstance(widget, ctk.CTkBaseClass):
        arg = mapping[arg]
        
    return arg

def set_opacity(widget: tk.Widget, value: float):
    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x00080000
    LWA_ALPHA = 0x00000002

    widget_id = widget.winfo_id()

    # make the widget a layered window
    style = windll.user32.GetWindowLongPtrW(widget_id, GWL_EXSTYLE)
    style = style | WS_EX_LAYERED
    windll.user32.SetWindowLongPtrW(widget_id, GWL_EXSTYLE, style)

    if value > 0:
        opacity = int(value * 255)
        windll.user32.SetLayeredWindowAttributes(widget_id, 0, opacity, LWA_ALPHA)
    else:
        windll.user32.SetLayeredWindowAttributes(widget_id, 0, 1, LWA_ALPHA)

def set_defocus_on(
    trigger_widget: tk.Widget,
    focused_widget: tk.Widget,
    exceptions: list[tk.Widget] = [],
    defocus_command=None,
):
    def set_focus_binding(event):
        def remove_focus(event):
            if event.widget not in exceptions:
                dummy_widget = tk.Frame(trigger_widget, width=0, height=0)
                # Set focus to something else
                trigger_widget.focus()
                dummy_widget.destroy()

                if callable(defocus_command):
                    defocus_command()

        # Binding to remove focus when clicking off the entry widget:
        trigger_widget.bind("<1>", remove_focus)

    def remove_focus_binding(event):
        trigger_widget.unbind("<1>")

    focused_widget.bind("<FocusIn>", set_focus_binding)
    focused_widget.bind("<FocusOut>", remove_focus_binding)

def make_label(master, width=None, height=None, *args, **kwargs):
    frame = tk.Frame(master, height=height, width=width)
    frame.pack_propagate(False)
    label = tk.Label(frame, *args, **kwargs)
    label.pack(fill="both", expand=1)
    return frame

def set_bindings(sequence: str, command, *widgets):
    for widget in widgets:
        if not isinstance(widget, tk.Widget):
            raise ValueError(
                f"*widgets argument must contain only widgets, not '{type(widget)}'"
            )
        widget.bind(sequence=sequence, func=command, add=True)
