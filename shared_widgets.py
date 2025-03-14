from abc import abstractmethod
from enum import Enum
import tkinter as tk
from colours import *
from database_service import DatabaseService
from models import *
from service_locator import Services
from tooltip import ToolTip
import utilities as utils
import customtkinter as ctk
from PIL import ImageTk, Image as PILImage
import models

DEVICE_SCALE_FACTOR = utils.get_setting("DEVICE_SCALE_FACTOR")


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
        self.original_bg = (
            parent.cget("background") if colourVar is None else colourVar.get()
        )
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
            utils.add_hover_effect(
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

    def __init__(self, window=None):
        self.window = window or Services.get("WindowManager").root
        super().__init__(self.window, width=400, bg=HIGHLIGHT_COLOUR)
        self.surface = tk.Frame(self, background=PRIMARY_COLOUR)
        self.surface.pack(fill="both", padx=(1, 1), pady=(1, 1), expand=True)

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
            raise Exception(
                f'Context {context} not registered. Register context before calling "open_menu"'
            )

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
            text_color=BLACK,
            font=ctk.CTkFont(family="Helvetica", size=16),
            height=26,
        )
        ctk_label.pack(side="left", padx=(4, 2))

        button.bind("<Button-1>", command)
        ctk_label.bind("<Button-1>", command)

        utils.add_bg_colour_hover_effect(button, partners=(ctk_label, button))
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
        txt_input = tk.Text(
            bg_frame, highlightbackground=BORDER_COLOUR, highlightthickness=2
        )
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

        self.prev_x = 0
        self.prev_y = 0

        self.font_scale = int(11 * DEVICE_SCALE_FACTOR) + 2

        super().__init__(canvas, width=width, height=height, **kwargs)

    def scale(self, factor=1.0):
        self.scale_factor = factor
        self.width = self.original_width * factor
        self.height = self.original_height * factor

        self.scale_content()
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
        # self.hide()
        self.item.x += dx / self.scale_factor
        self.item.y += dy / self.scale_factor
        self.scaled_x += dx
        self.scaled_y += dy
        self.show()

    def pan(self, dx, dy):
        self.scaled_x += dx
        self.scaled_y += dy
        self.place(x=self.scaled_x, y=self.scaled_y)

    def highlight(self):
        self.configure(
            highlightcolor=HIGHLIGHT_COLOUR,
            highlightbackground=HIGHLIGHT_COLOUR,
            highlightthickness=3,
        )

    def remove_highlight(self):
        self.configure(highlightcolor=BLACK, highlightbackground=BLACK)
        self.after(10, lambda: self.configure(highlightthickness=2))

    @abstractmethod
    def scale_content(self):
        self.font_scale = int(10 * self.scale_factor) + 2

    @abstractmethod
    def set_colour(self, colour):
        self.item.colour = colour


class NoteWidget(BoardItemWidget):

    def __init__(self, canvas, item: Note):
        width = 280 * DEVICE_SCALE_FACTOR
        height = 280 * DEVICE_SCALE_FACTOR
        super().__init__(
            canvas,
            width,
            height,
            item,
            bg=item.colour,
            highlightthickness=2,
            highlightbackground=BLACK,
        )

        # Set up grid
        self.rowconfigure(index=0, weight=1, uniform="note_grid")
        self.rowconfigure(index=1, weight=2, uniform="note_grid")
        self.rowconfigure(index=2, weight=1, uniform="note_grid")
        self.rowconfigure(index=3, weight=22, uniform="note_grid")
        self.rowconfigure(index=4, weight=1, uniform="note_grid")
        self.columnconfigure(index=0, weight=1, uniform="note_grid")
        self.columnconfigure(index=1, weight=32, uniform="note_grid")
        self.columnconfigure(index=2, weight=1, uniform="note_grid")
        self.grid_propagate(False)

        self.title_label = tk.Label(
            self,
            bg=item.colour,
            font=("Commons", self.font_scale + 2, "bold"),
            text=self.item.title,
            anchor="w",
            pady=0,
        )
        self.title_label.grid(row=1, column=1, sticky="nesw", padx=0, pady=0)

        self.content_widget = tk.Text(
            self, bg=item.colour, relief=tk.FLAT, font=("Dubai Medium", self.font_scale)
        )
        self.content_widget.grid(row=3, column=1, sticky="nesw", padx=0, pady=0)
        self.content_widget.insert("1.0", item.content)
        self.content_widget.configure(state="disabled")

    def scale_content(self):
        super().scale_content()
        self.title_label.config(font=("Commons", self.font_scale + 3, "bold"))
        self.content_widget.config(font=("Dubai Medium", self.font_scale))

    def set_colour(self, colour):
        self.configure(bg=colour)
        self.title_label.config(bg=colour)
        self.content_widget.configure(bg=colour)
        super().set_colour(colour)


class ImageWidget(BoardItemWidget):

    def __init__(self, canvas, item: models.Image):
        width = 400 * DEVICE_SCALE_FACTOR
        height = 300 * DEVICE_SCALE_FACTOR
        super().__init__(
            canvas,
            width,
            height,
            item,
            bg=WHITE,
            highlightthickness=2,
            highlightbackground=BLACK,
        )

        max_size = 800 * DEVICE_SCALE_FACTOR
        self.img = None

        # Set up grid
        if item.image.width > max_size or item.image.height > max_size:
            self.img = utils.resize_image(item.image, max_size)
        else:
            self.img = ImageTk.PhotoImage(item.image)

        self.largest_dimension = max(self.img.width(), self.img.height())
        w = int(self.img.width()) + 20 * self.scale_factor
        h = int(self.img.height()) + 20 * self.scale_factor
        self.configure(width=w, height=h)

        self.image_canvas = tk.Canvas(
            self, width=w, height=h, highlightthickness=0, bg=WHITE
        )
        self.image_canvas.pack(fill="both", expand=True)
        self.image_canvas.create_image(
            w / 2, h / 2, image=self.img, anchor="center", tag="image"
        )

        self.original_width = w
        self.original_height = h
        self.width = w
        self.height = h

    def scale_content(self):
        self.img = utils.resize_image(
            self.item.image, int(self.largest_dimension * self.scale_factor)
        )
        self.image_canvas.delete("image")
        w = int(self.img.width()) + 20 * self.scale_factor
        h = int(self.img.height()) + 20 * self.scale_factor
        self.image_canvas.configure(width=w, height=h)
        self.image_canvas.create_image(
            w / 2, h / 2, image=self.img, anchor="center", tag="image"
        )

    def set_colour(self, colour):
        self.configure(bg=colour)
        super().set_colour(colour)


class PageWidget(BoardItemWidget):

    def __init__(self, canvas, item: Page):
        width = 280 * DEVICE_SCALE_FACTOR
        height = 400 * DEVICE_SCALE_FACTOR
        super().__init__(
            canvas,
            width,
            height,
            item,
            bg=WHITE,
            highlightthickness=2,
            highlightbackground=BLACK,
        )

        # Set up grid
        self.rowconfigure(index=0, weight=1, uniform="page_grid")
        self.rowconfigure(index=1, weight=2, uniform="page_grid")
        self.rowconfigure(index=2, weight=1, uniform="page_grid")
        self.rowconfigure(index=3, weight=28, uniform="page_grid")
        self.rowconfigure(index=4, weight=1, uniform="page_grid")
        self.columnconfigure(index=0, weight=1, uniform="page_grid")
        self.columnconfigure(index=1, weight=18, uniform="page_grid")
        self.columnconfigure(index=2, weight=1, uniform="page_grid")
        self.grid_propagate(False)

        self.title_label = tk.Label(
            self,
            bg=item.colour,
            font=("Commons", self.font_scale + 2, "bold"),
            text=self.item.title,
            anchor="w",
            pady=0,
        )
        self.title_label.grid(row=1, column=1, sticky="nesw", padx=0, pady=0)

        self.content_widget = tk.Text(
            self, bg=item.colour, relief=tk.FLAT, font=("Dubai Medium", self.font_scale)
        )
        self.content_widget.grid(row=3, column=1, sticky="nesw", padx=0, pady=0)
        self.content_widget.insert("1.0", item.content)
        self.content_widget.configure(state="disabled")

    def scale_content(self):
        super().scale_content()
        self.title_label.config(font=("Commons", self.font_scale + 3, "bold"))
        self.content_widget.config(font=("Dubai Medium", self.font_scale))

    def set_colour(self, colour):
        self.configure(bg=colour)
        self.title_label.configure(bg=colour)
        self.content_widget.configure(bg=colour)
        super().set_colour(colour)


class OpenBoardWindow(tk.Toplevel):
    def __init__(self, parent, width, height):

        print("OpenBoardWindow instantiated")
        db_service: DatabaseService = Services.get("DatabaseService")
        th = Services.get("TabHandler")
        self.parent = parent

        super().__init__(parent, bg=TRANSPARENT_COLOUR)
        self.geometry(f"{int(width)}x{int(height)}+500+300")

        # Make TopLevel widget transparent for rounded corners
        self.attributes("-transparentcolor", TRANSPARENT_COLOUR)
        self.update_idletasks()
        canvas = RoundedBorderCanvas(
            self,
            width,
            height,
            canvas_colour=TRANSPARENT_COLOUR,
            border_colour=BORDER_COLOUR,
            rounding=0.1,
        )
        canvas.pack(fill="both", expand=True)
        canvas.draw_border()
        self.overrideredirect(1)

        top_frame = tk.Frame(canvas, bg=PRIMARY_COLOUR)
        top_frame.pack(side="top", fill="x", padx=20, pady=(18, 20))
        top_frame.rowconfigure(index=0, weight=0)
        top_frame.columnconfigure(index=0, weight=1)
        top_frame.columnconfigure(index=1, weight=0)

        ctk.CTkLabel(
            top_frame,
            text="Select a board to open",
            font=utils.ctk_font(22, True),
            text_color=BLACK,
            fg_color=PRIMARY_COLOUR,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        updated_colour = tk.StringVar(value=PRIMARY_COLOUR)
        CloseButton(
            top_frame,
            30,
            15,
            self.destroy,
            thickness=4,
            rounding=0.4,
            colourVar=updated_colour,
        ).grid(row=0, column=1, sticky="e")

        # Set grip at top
        self.grip = tk.Frame(canvas, height=18)
        self.grip.place(x=0, y=0, relwidth=1)
        utils.set_opacity(self.grip, 0)
        self.rel_x = 0
        self.rel_y = 0
        self.grip.bind("<1>", self.hold)
        self.grip.bind("<B1-Motion>", self.move_window)

        # Scrollable area
        scrollable_canvas = tk.Canvas(canvas, highlightthickness=0, bg=PRIMARY_COLOUR)
        scrollable_canvas.pack(
            side="top", fill="both", expand=True, padx=20, pady=(20, 30)
        )

        # Get boards currently not open
        all_boards = db_service.get_board_previews()
        unopened_boards = [board for board in all_boards if board[0] not in th.get_open_board_ids()]

        for board in unopened_boards:
            self.BoardOption(scrollable_canvas, board)
            
    class BoardOption(ctk.CTkFrame):
        def __init__(self, parent, board):
            super().__init__(parent, fg_color=PRIMARY_COLOUR, border_width=0, corner_radius=2)
            self.pack(side="top", fill="x")

            self.rowconfigure(index=0, weight=0)
            self.columnconfigure(index=0, weight=1)
            self.columnconfigure(index=1, weight=0)
            self.columnconfigure(index=2, weight=0)

            parent.update_idletasks()
            icon_size = int(parent.winfo_width()/20)

            self.label = tk.Label(self, font=utils.ctk_font(18), bg=PRIMARY_COLOUR, fg=BLACK, text=board[1])
            self.label.grid(row=0, column=0, sticky="w")
            self.date_modified = tk.Label(self, font=utils.ctk_font(16), bg=PRIMARY_COLOUR, fg=GRAY, text=board[2].strftime("%Y/%m/%d %H:%M"))
            self.date_modified.grid(row=0, column=1, sticky="e")
            self.tk_image = utils.resize_image(PILImage.open("assets/icons/kebab.png"), icon_size)
            self.icon_canvas = tk.Canvas(self, width=icon_size, height=icon_size*2, bg=PRIMARY_COLOUR, highlightthickness=0)
            self.icon_canvas.create_image(icon_size/2, icon_size, image=self.tk_image, anchor="center")
            self.icon_canvas.grid(row=0, column=2)
            
            utils.add_bg_colour_hover_effect(self.icon_canvas)
            utils.add_bg_colour_hover_effect(self, partners=(self.label, self.date_modified, self.icon_canvas))
            utils.add_bg_colour_hover_effect(self.label, partners=(self, self.date_modified, self.icon_canvas))
            utils.add_bg_colour_hover_effect(self.date_modified, partners=(self.label, self, self.icon_canvas))

    def move_window(self, e):
        x = e.x_root - self.rel_x
        y = e.y_root - self.rel_y
        self.geometry(f"+{x}+{y}")

    def hold(self, e):
        self.rel_x = e.x
        self.rel_y = e.y

    def destroy(self):
        self.parent.focus()
        return super().destroy()

    # TagEditor is a reusable class that describes the UI component used to show, add, and remove tags for a board item


class RoundedBorderCanvas(tk.Canvas):
    def __init__(
        self,
        parent,
        width,
        height,
        thickness=6,
        canvas_colour=PRIMARY_COLOUR,
        bg_colour=PRIMARY_COLOUR,
        border_colour=HIGHLIGHT_COLOUR,
        rounding=0.4,
    ):
        """
        Canvas widget with rounded rectangle and border drawn on top to give the illusion of
        a rounded button.
        IMPORTANT: Must call draw_border on the RoundedBorderCanvas AFTER it has been packed, gridded, or placed
        """
        super().__init__(
            parent, width=width, height=height, bg=canvas_colour, highlightthickness=0
        )
        self.width = width
        self.height = height
        self.thickness = thickness
        self.rounding = rounding
        self.bg_colour = bg_colour
        self.border_colour = border_colour
        
        self.update_idletasks()

    def draw_border(self, bg_colour = None):
        self.delete("all")
        bg_colour = bg_colour or self.bg_colour
        utils.rounded_rectangle(
            self,
            int(self.width - 2),
            int(self.height - 2),
            self.rounding,
            self.border_colour,
        )
        utils.rounded_rectangle(
            self,
            int(self.width - 2 * self.thickness),
            int(self.height - 2 * self.thickness),
            self.rounding,
            bg_colour,
        )


class TagEditor(ctk.CTkFrame):
    def __init__(self, parent, width, window):
        editor_placeholder_colour = "#63472B"
        super().__init__(parent, width=width, fg_color=BROWN, corner_radius=0)

        self.item: models.BoardItem = None
        self.width = width
        self.tag_height = 0.13 * width
        self.tag_list_height = 0
        self.scrollbar_height = 15
        self.gap = self.width / 75
        self.max_space = self.width - self.gap - 10
        self.tag_list: set[str] = None
        self.tag_widgets_list = []
        self.space_occupied = 0

        # Entry field
        self.entry = ctk.CTkEntry(
            self,
            width=width - 10,
            height=width * 0.16,
            placeholder_text="Enter new tag...",
            placeholder_text_color=editor_placeholder_colour,
            fg_color=LIGHT_BROWN,
            text_color=BLACK,
            font=utils.ctk_font(18, True),
            border_width=0,
            corner_radius=0,
        )
        self.entry.pack(side="top", padx=5, pady=(5, 3), fill="x")

        utils.set_defocus_on(window, self.entry, [self.entry._entry])
        self.entry.bind("<Return>", lambda event: self.add_tag(self.entry.get()))

        self.canvas = tk.Canvas(
            self, width=self.width, height=0, highlightthickness=0, bg=BROWN
        )
        self.canvas.pack_propagate(False)
        self.canvas.pack(side="bottom", fill="x")

        self.scrollbar = ctk.CTkScrollbar(
            self.canvas,
            orientation="horizontal",
            height=self.scrollbar_height,
            command=self.canvas.xview,
            button_color=LIGHT_BROWN,
            button_hover_color=OLIVE_GREEN,
        )
        self.canvas.configure(xscrollcommand=self.scrollbar.set)

        self.scrollable_frame = tk.Frame(self.canvas, bg=BROWN)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        def update_scroll_region(event=None):
            x1, y1, x2, y2 = self.canvas.bbox("all")
            x2 += 5
            self.canvas.configure(scrollregion=(x1, y1, x2, y2))

        self.canvas.bind("<Configure>", update_scroll_region)

        # Add absolute border on right
        self.update_idletasks()
        tk.Frame(self, width=5, bg=BROWN).place(x=self.width - 5, y=0, relheight=1)

    def add_tag(self, text):
        if self.tag_list is None:
            raise ValueError("tag_list not set")

        if len(text) > 0:
            if len(text) > 15:
                # TODO: popup -> tag is too long
                print("Tag can only have a maximum of 15 characters")
                return
            if len(self.tag_list) > 10:
                # TODO: popup -> too many tags
                print("too many tags")
                return
            if text in self.tag_list:
                # TODO: popup -> tag already exists
                print("tag already exists")
                return

            self.item.tags.add(text)
            self.tag_list.add(text)
            self._add_tag_widet(text)

    def _add_tag_widet(self, text):
        self.entry.pack_configure(pady=(5, 0))

        new_tag = self.Tag(self, self, self.tag_height, text)
        new_tag.show()
        self.update_idletasks()
        tag_width = new_tag.winfo_width()
        tag_height = new_tag.winfo_height()

        # Recreate tag with canvas as parent
        new_tag.destroy()
        new_tag = self.Tag(self.scrollable_frame, self, self.tag_height, text)
        new_tag.show()
        self.update_idletasks()

        # Update instance variables
        self.tag_widgets_list.append(new_tag)
        self.space_occupied += tag_width + self.gap

        # Update size of canvas to make room for first tag
        if len(self.tag_widgets_list) == 1:
            self.tag_list_height = int(tag_height * 1.2) + 2
            self.canvas.configure(height=self.tag_list_height)

        if self.space_occupied > self.max_space:
            self.canvas.update_idletasks()
            self.canvas.configure(height=self.tag_list_height + self.scrollbar_height)
            self.canvas.update_idletasks()
            self.scrollbar.pack(side="bottom", fill="x")

        if self.entry.get():
            self.entry.delete(0, "end")

        # TODO: immediately save changes to database

    def remove_tag(self, tag: "Tag"):
        if self.tag_list is None:
            raise ValueError("tag_list not set")

        if not tag in self.tag_widgets_list:
            raise ValueError(f"Tag '{tag}' not found in tag list")

        self.tag_list.remove(tag.text)
        self.item.tags.remove(tag.text)
        self.tag_widgets_list.remove(tag)

        self.space_occupied -= tag.winfo_width() + self.gap
        if self.space_occupied < self.max_space:
            self.scrollbar.pack_forget()
            self.canvas.configure(height=self.tag_list_height)

            if len(self.tag_list) == 0:
                self.canvas.configure(height=5)

        tag.destroy()

    def set_item(self, item: models.BoardItem):
        self.item = item

        self.tag_list = self.item.tags

        def set_tags():
            for text in self.tag_list:
                self._add_tag_widet(text)

        self.after(10, set_tags)

    class Tag(RoundedBorderCanvas):
        def __init__(self, parent, tag_editor: "TagEditor", height, text):
            self.parent = parent
            self.height = height
            self.text = text
            self.gap = 6
            self.tag_colour = utils.adjust_brightness(LIGHT_BROWN, -0.2)
            padding = 5

            super().__init__(parent, 0, 0, 3, BROWN, self.tag_colour, BLACK, 0.65)

            label = tk.Label(
                self, bg=self.tag_colour, text=text, fg=WHITE, font=utils.ctk_font(14)
            )
            label.pack(padx=padding, pady=height * 0.12)
            label.after(10, self.redraw_border)

            if len(text) < 4:
                label.configure(width=3)

            self.bind("<3>", lambda event: tag_editor.remove_tag(self))
            label.bind("<3>", lambda event: tag_editor.remove_tag(self))

            self.tooltip = ToolTip(
                label,
                msg="Right-click to remove",
                delay=0.3,
                bg=PRIMARY_COLOUR,
                relief=tk.RAISED,
            )

        def redraw_border(self):
            self.width = self.winfo_width()
            self.height = self.winfo_height()
            self.delete("all")
            self.draw_border(self.tag_colour)

        def show(self):
            self.pack(
                side="left", padx=(self.gap - 1, 0), pady=(self.gap - 2, self.gap)
            )

        def destroy(self):
            self.tooltip.destroy()
            return super().destroy()


class MainSidePanelFrame(tk.Frame):
    """
    Set different side panel contexts to display sections relevant to the current context\n
    Sections:
        Search bar
        Add Items (Note, Page, Image)
        Board Options (Open, Save, Delete)
        Colour Selector
        Tag Editor
    """

    class Contexts(Enum):
        BOARD = "board"
        ITEM = "item"
        TAB = "tab"

    def __init__(self, parent, window, width):
        super().__init__(parent, bg=PRIMARY_COLOUR, width=width)

        self.pack(side="left", fill="y")
        self.pack_propagate(False)

        self.current_ctx = None
        self.current_ctx_instance = None

        self.displayed_sections: list = []
        self.section_title_font = utils.ctk_font(22, True)
        spacing = 22
        width = 0.85 * width
        height = 0.75 * width

        self.search = self.Search(self, width, height, spacing, window)
        self.board_options = self.BoardOptions(self, width - 10, height, spacing)
        self.add_items_widgets = self.AddItemOptions(self, width, height, spacing)
        self.colour_selector = self.ColourSelector(
            self, width - 10, height * 0.45, spacing
        )
        self.tags_editor = self.TagsSidePanel(self, width, spacing + 3, window)

    def clear(self):
        for section in self.displayed_sections:
            section.hide()

    def set_context(self, context_type, context_instance):

        if context_instance == self.current_ctx_instance:
            return
        self.current_ctx_instance = context_instance

        match context_type:
            case self.Contexts.BOARD:
                self.clear()

                self.search.show()
                self.board_options.show(context_instance)
                self.add_items_widgets.show()

                self.displayed_sections = [
                    self.search,
                    self.board_options,
                    self.add_items_widgets,
                ]
            case self.Contexts.ITEM:
                if not isinstance(context_instance, BoardItemWidget):
                    raise ValueError(
                        f"Context Menu: Context instance must be of type 'BoardItemWidget', not '{type(context_instance)}'"
                    )
                self.clear()

                self.search.show()
                self.board_options.show(None)
                self.colour_selector.show(context_instance)
                self.tags_editor.show(context_instance)

                self.displayed_sections = [
                    self.search,
                    self.board_options,
                    self.colour_selector,
                    self.tags_editor,
                ]
            case self.Contexts.TAB:
                self.clear()

                self.search.show()
                self.board_options.show(None)
                self.add_items_widgets.show()

                self.displayed_sections = [
                    self.search,
                    self.board_options,
                    self.add_items_widgets,
                ]

    ### ========================================== ###
    ### ============== Search Notes ============== ###
    ### ========================================== ###

    class Search(tk.Frame):

        def __init__(self, parent, width, height, spacing, window):
            self.width = width
            self.height = height
            self.child_widgets_height = 0.21 * self.height
            self.spacing = spacing
            super().__init__(
                parent, width=self.width, height=self.height, bg=PRIMARY_COLOUR
            )

            def change_button_state(event):

                def change_state():
                    if self.search_bar.get() == "":
                        search_button.configure(state="disabled", image=icon_disabled)
                    else:
                        search_button.configure(state="normal", image=icon)

                event.widget.after(1, change_state)

            def search_global(query: str):
                # TODO: Use SQL to search through all text of items in database
                print(query)

            utils.make_label(
                self,
                width=self.width,
                height=self.child_widgets_height,
                text="Search notes for:",
                fg=BLACK,
                anchor="w",
                font=parent.section_title_font,
                background=PRIMARY_COLOUR,
            ).pack(side="top")

            search_widgets = tk.Frame(
                self,
                width=self.width,
                height=self.child_widgets_height,
                background=PRIMARY_COLOUR,
            )
            search_widgets.pack(side="top", pady=(3, 0))

            self.search_bar = ctk.CTkEntry(
                search_widgets,
                width=self.width - 45,
                height=self.child_widgets_height,
                placeholder_text="Enter a search term",
                placeholder_text_color=GRAY,
                bg_color=PRIMARY_COLOUR,
                border_color=HIGHLIGHT_COLOUR,
                border_width=4,
                fg_color=utils.adjust_brightness(PRIMARY_COLOUR, 0.1),
                text_color=BLACK,
                font=utils.ctk_font(18, True),
                corner_radius=8,
            )
            self.search_bar.pack(side="left", padx=(0, 2))

            icon_size = 0.68 * self.child_widgets_height
            icon = ctk.CTkImage(
                PILImage.open("assets/images/search_icon_olive.png"),
                size=(icon_size, icon_size),
            )
            icon_disabled = ctk.CTkImage(
                PILImage.open("assets/images/search_icon_disabled.png"),
                size=(icon_size, icon_size),
            )
            search_button = ctk.CTkButton(
                search_widgets,
                width=self.child_widgets_height,
                height=self.child_widgets_height,
                fg_color=PRIMARY_COLOUR,
                text_color=WHITE,
                text="",
                command=lambda: search_global(self.search_bar.get()),
                hover_color=utils.adjust_brightness(PRIMARY_COLOUR, 0.3),
                image=icon_disabled,
            )
            search_button.pack(side="right", fill="both")

            self.search_bar.bind(
                "<Return>", lambda event: search_global(self.search_bar.get())
            )
            # This ensures the placeholder can still be shown after the initial focus in on the entry
            utils.set_defocus_on(window, self.search_bar, [self.search_bar._entry])
            self.search_bar.bind("<Key>", change_button_state)

        def show(self):
            self.pack(side="top", pady=(self.spacing, 0))

        def hide(self):
            self.pack_forget()

    ### ========================================= ###
    ### ============= Board Options ============= ###
    ### ========================================= ###

    class BoardOptions(tk.Frame):

        def __init__(self, side_panel, width, height, spacing):
            super().__init__(side_panel, width=width, height=height, bg=PRIMARY_COLOUR)

            self.board = None
            self.spacing = spacing
            self.button_height = int(height * 0.28)
            app_width = utils.get_setting("APP_WIDTH_INITIAL", width)
            app_height = utils.get_setting("APP_HEIGHT_INITIAL", height)

            # ======== Open Board ========
            # Open Board - Widgets
            self.open_board_button = RoundedBorderCanvas(
                self, width, self.button_height
            )
            self.open_board_button.pack(side="top")
            self.open_board_button.draw_border()
            self.open_board_image = utils.resize_image(
                PILImage.open("assets/images/open_board.png"), self.button_height - 14
            )
            rel_x = 0.5 + 0.1 * self.button_height / width
            open_board_label = tk.Label(
                self.open_board_button,
                font=utils.ctk_font(24),
                text="Open Board",
                bg=PRIMARY_COLOUR,
            )
            open_board_label.place(relx=rel_x, rely=0.5, anchor=tk.CENTER)

            # Open Board - Events
            self.set_redraw_on_hover(self.open_board_button, self.open_board_image, 14)
            utils.add_bg_colour_hover_effect(self.open_board_button, open_board_label)
            utils.set_bindings(
                "<1>",
                lambda event: OpenBoardWindow(self, app_width * 0.3, app_height * 0.6),
                self.open_board_button,
                open_board_label,
            )

            # Frame to pack Lower three buttons onto
            lower_option_group = tk.Frame(
                self, width=width, height=self.button_height, bg=PRIMARY_COLOUR
            )
            lower_option_group.pack(side="top", pady=(10, 0))
            lower_option_group.pack_propagate(False)

            # ========= Save Board ==========
            # Save Board - Widgets
            save_button_width = width / 2 + 14
            self.save_board_button = RoundedBorderCanvas(
                lower_option_group, save_button_width, self.button_height
            )
            self.save_board_button.pack(side="left")
            self.save_board_button.draw_border()
            self.save_board_image = utils.resize_image(
                PILImage.open("assets/images/save.png"), self.button_height - 23
            )
            rel_x = (save_button_width - self.button_height) / save_button_width
            save_board_label = tk.Label(
                self.save_board_button,
                font=utils.ctk_font(24),
                text="Save",
                bg=PRIMARY_COLOUR,
            )
            save_board_label.place(relx=rel_x, rely=0.5, anchor=tk.CENTER)

            # Save Board - Events
            self.set_redraw_on_hover(self.save_board_button, self.save_board_image, 14)
            utils.add_bg_colour_hover_effect(self.save_board_button, save_board_label)

            # ======== Delete Board =========
            # Delete Board - Widgets
            self.delete_board_button = RoundedBorderCanvas(
                lower_option_group, width / 4 - 12, self.button_height
            )
            self.delete_board_button.pack(side="left", padx=(5, 0))
            self.delete_board_button.draw_border()
            self.delete_board_image = utils.resize_image(
                PILImage.open("assets/images/delete.png"), self.button_height - 20
            )

            # Delete Board - Events
            self.set_redraw_on_hover(
                self.delete_board_button, self.delete_board_image, 10
            )

            # ======== Add New Board ========
            # Add Board - Widgets
            self.add_board_button = RoundedBorderCanvas(
                lower_option_group, width / 4 - 12, self.button_height
            )
            self.add_board_button.pack(side="left", padx=(5, 0))
            self.add_board_button.draw_border()
            self.add_board_button.pack_propagate(False)
            plus_icon = tk.Label(
                self.add_board_button,
                bg=PRIMARY_COLOUR,
                text="+",
                font=("", 54),
                fg=GREEN,
            )
            plus_icon.pack(fill="both", expand=True, padx=(11, 9), pady=10)

            # Add Board - Events
            self.set_redraw_on_hover(self.add_board_button)
            utils.add_bg_colour_hover_effect(self.add_board_button, plus_icon)

        def set_redraw_on_hover(
            self, canvas: RoundedBorderCanvas, image: PILImage = None, padding_left=0
        ):
            """
            Method to redraw the border, background, and image of button every time the mouse hovers over
            """
            x = int(image.width() / 2 + padding_left) if image else 0
            y = self.button_height / 2
            enter_commands = (
                lambda: canvas.draw_border(
                    utils.adjust_brightness(PRIMARY_COLOUR, 0.2)
                ),
                lambda: image
                and canvas.create_image(x, y, image=image, anchor=tk.CENTER),
            )
            leave_commands = (
                lambda: canvas.draw_border(PRIMARY_COLOUR),
                lambda: image
                and canvas.create_image(x, y, image=image, anchor=tk.CENTER),
            )

            utils.add_hover_commands(canvas, enter_commands, leave_commands)

        def redraw_button(
            self,
            button: RoundedBorderCanvas,
            image: PILImage = None,
            padding=0,
        ):
            x = int(image.width() / 2 + padding) if image else 0
            y = self.button_height / 2

            button.draw_border()
            if image:
                button.create_image(x, y, image=image, anchor=tk.CENTER)

        def show(self, board=None):
            if board is not None:
                self.board = board

            self.pack(side="top", pady=(self.spacing, 0))
            self.update_idletasks()

            self.redraw_button(
                self.open_board_button, self.open_board_image, padding=14
            )
            self.redraw_button(
                self.save_board_button, self.save_board_image, padding=14
            )
            self.redraw_button(
                self.delete_board_button, self.delete_board_image, padding=10
            )
            self.redraw_button(self.add_board_button)

        def hide(self):
            self.pack_forget()

    ### ========================================= ###
    ### =============== Add Items =============== ###
    ### ========================================= ###

    class AddItemOptions(tk.Frame):

        def __init__(self, parent, width, height, spacing):
            self.width = width
            self.height = height
            self.child_widgets_height = 0.2 * self.height
            self.spacing = spacing

            super().__init__(parent, width=self.width, bg=PRIMARY_COLOUR)

            utils.make_label(
                self,
                width=self.width,
                height=self.child_widgets_height,
                text="Add Items",
                fg=BLACK,
                anchor="w",
                font=parent.section_title_font,
                background=PRIMARY_COLOUR,
            ).pack(side="top")

            self.new_note_button = self.ItemButton(
                self, "New Note", "assets/images/items_note.png"
            )
            self.new_page_button = self.ItemButton(
                self, "New Page", "assets/images/items_page.png", 2, 2
            )
            self.new_image_button = self.ItemButton(
                self, "New Image", "assets/images/items_image.png", 2, 2
            )

        class ItemButton(tk.Canvas):

            def __init__(
                self, parent, text: str, image_path: str, x_offset=0, y_offset=0
            ):
                # Main button widget
                button_width = parent.width * 0.9
                button_height = parent.width * 0.22
                self.x_offset = x_offset
                self.y_offset = y_offset
                super().__init__(
                    parent,
                    width=button_width,
                    height=button_height,
                    bg=PRIMARY_COLOUR,
                    highlightthickness=0,
                )

                self.pack(side="top", padx=(8, 0), pady=(5, 0))
                self.pack_propagate(False)

                self.rowconfigure(index=0, weight=1)
                self.columnconfigure(index=0, weight=0)
                self.columnconfigure(index=1, weight=1)
                self.grid_propagate(False)

                # Frame that surrounds image
                self.image_frame_size = button_height * 0.81
                self.image_frame = tk.Canvas(
                    self,
                    width=self.image_frame_size,
                    height=self.image_frame_size,
                    highlightthickness=0,
                    bg=PRIMARY_COLOUR,
                )
                self.image_frame.grid(row=0, column=0, padx=(5, 0))

                # Image loaded on each image_frame
                image_tk = PILImage.open(image_path)

                self.image = utils.resize_image(
                    image_tk, int(self.image_frame_size - 14)
                )
                self.canvas_image = None
                # Ensure render_item_frame is called after canvas initialization to avoid rendering bugs with the rounded squares and the image
                self.image_frame.after(
                    100,
                    lambda: self.render_item_frame(
                        self.image_frame,
                        self.image_frame_size - 2,
                        3,
                        PRIMARY_COLOUR,
                        OLIVE_GREEN,
                        self.image,
                    ),
                )

                # Label
                label = tk.Label(
                    self,
                    font=utils.ctk_font(24),
                    text=text,
                    bg=PRIMARY_COLOUR,
                    anchor="w",
                )
                label.grid(row=0, column=1, padx=(14, 0), sticky="ew")

                # Hover effect
                utils.add_hover_effect(
                    widget=self,
                    shape="rectangle",
                    rounding=0.5,
                    partners=(label, self.image_frame),
                )

                utils.add_hover_commands(
                    self,
                    enter_commands=self.highlight_item_frame,
                    leave_commands=self.remove_highlight_item_frame,
                )

            def render_item_frame(
                self, canvas, size, thickness, colour, border_colour, image
            ):
                # This simple method creates a square 'button' by using two rounded squares drawn on a canvas to
                # give off the appearance of a rounded border. Also loads image/icon

                utils.rounded_square(canvas, size, 0.4, border_colour)
                utils.rounded_square(canvas, size - thickness * 2, 0.4, colour)
                center_x = size / 2 + self.x_offset
                center_y = size / 2 + self.y_offset
                self.canvas_image = canvas.create_image(
                    center_x, center_y, image=image, anchor=tk.CENTER
                )

            def highlight_item_frame(self):
                self.image_frame.delete("all")
                self.render_item_frame(
                    self.image_frame,
                    self.image_frame_size - 2,
                    3,
                    utils.adjust_brightness(PRIMARY_COLOUR, 0.2),
                    OLIVE_GREEN,
                    self.image,
                )
                self.image_frame.move(self.canvas_image, -1, -1)

            def remove_highlight_item_frame(self):
                self.image_frame.delete("all")
                self.render_item_frame(
                    self.image_frame,
                    self.image_frame_size - 2,
                    3,
                    PRIMARY_COLOUR,
                    OLIVE_GREEN,
                    self.image,
                )

        # Show "Add Item Widgets" section
        def show(self):
            self.pack(side="top", pady=(self.spacing, 0))

        def hide(self):
            self.pack_forget()

    ### ========================================= ###
    ### ============ Colour Selector ============ ###
    ### ========================================= ###

    class ColourSelector(tk.Frame):
        def __init__(self, parent, width, height, spacing):
            super().__init__(parent, width=width, height=height, bg=PRIMARY_COLOUR)

            self.item: BoardItemWidget = None
            self.spacing = spacing
            self.button_height = int(height * 0.56)

            # Cannot use 'make_label' method since the text must be dynamic here, thus the label from the method must be accessible. Unfortunately,
            # this means the title/label must be manually offset to the right ('padx') with a certain value to align it with other section titles.

            # For future refactoring: Convert make_label to a class OR standardize the way it is decided how far from the left-hand side of the
            # panel to offset the section title for each section
            self.label = tk.Label(
                self,
                width=int(width),
                anchor="w",
                font=parent.section_title_font,
                text="Change colour",
                bg=PRIMARY_COLOUR,
            )
            self.label.pack(side="top", padx=width * 0.075)

            # Colour palette
            palette_frame = tk.Frame(self, width=width, bg=PRIMARY_COLOUR)
            palette_frame.pack(side="top", pady=(10, 0))

            palette_frame.rowconfigure(index=0, weight=1)
            palette_frame.rowconfigure(index=1, weight=1)
            for i in range(8):
                palette_frame.columnconfigure(index=i, weight=1)

            colours_row_1 = (
                STICKY_NOTE_YELLOW,
                STICKY_NOTE_PINK,
                STICKY_NOTE_BLUE,
                STICKY_NOTE_GREEN,
                STICKY_NOTE_ORANGE,
                STICKY_NOTE_PURPLE,
            )
            colours_row_2 = (
                STICKY_NOTE_MINT,
                STICKY_NOTE_LAVENDER,
                STICKY_NOTE_PEACH,
                STICKY_NOTE_RED,
                STICKY_NOTE_TEAL,
                STICKY_NOTE_GRAY,
            )
            tile_width = width / 8
            for i, colour in enumerate(colours_row_1):
                self.ColourTile(self, palette_frame, tile_width, colour).grid(
                    row=0, column=i
                )
            for i, colour in enumerate(colours_row_2):
                self.ColourTile(self, palette_frame, tile_width, colour).grid(
                    row=1, column=i
                )

            self.current_colour_tile = self.ColourTile(
                self,
                palette_frame,
                int(width / 4),
                STICKY_NOTE_YELLOW,
                BORDER_COLOUR,
                False,
            )
            self.current_colour_tile.grid(
                row=0, column=6, rowspan=2, columnspan=2, padx=(2, 0)
            )

        def change_current_colour(self, colour):
            self.current_colour_tile.swatch.configure(bg=colour)
            self.item.set_colour(colour)

        def show(self, item: BoardItemWidget):
            item_type = ""
            item_type = type(item)
            if item_type == NoteWidget:
                item_type = "Note"
            elif item_type == ImageWidget:
                item_type = "Image"
            elif item_type == PageWidget:
                item_type = "Page"
            else:
                raise ValueError(
                    f"Colour Selector: Context instance should be a type of BoardItem, not '{type(item)}'"
                )

            self.label.configure(text=f"Change {item_type} Colour")
            self.item = item
            self.change_current_colour(item.item.colour)

            self.pack(side="top", pady=(self.spacing, 0))

        def hide(self):
            self.pack_forget()

        class ColourTile(tk.Frame):
            def __init__(
                self,
                colour_selector,
                parent,
                size,
                colour,
                hover_colour=PRIMARY_COLOUR,
                hover_effect=True,
                view_only=False,
            ):
                super().__init__(parent, bg=hover_colour, width=size, height=size)
                # self.colour = colour
                self.pack_propagate(False)

                self.swatch = tk.Frame(self, bg=colour)
                self.swatch.pack(padx=3, pady=3, fill="both", expand=True)

                if hover_effect:
                    utils.add_bg_colour_hover_effect(
                        self, hover_colour=utils.adjust_brightness(PRIMARY_COLOUR, 0.3)
                    )

                if not view_only:
                    self.bind(
                        "<1>",
                        lambda event: colour_selector.change_current_colour(colour),
                    )
                    self.swatch.bind(
                        "<1>",
                        lambda event: colour_selector.change_current_colour(colour),
                    )

    ### ========================================= ###
    ### ============== Tags Editor ============== ###
    ### ========================================= ###

    class TagsSidePanel(TagEditor):
        def __init__(self, parent, width, spacing, window):
            self.spacing = spacing
            super().__init__(parent, width, window)

            self.item = None

        def show(self, item: BoardItemWidget):
            self.set_item(item.item)
            self.pack(side="top", pady=(self.spacing, 0))

        def hide(self):
            self.pack_forget()
