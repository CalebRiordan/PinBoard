import tkinter as tk
import customtkinter as ctk
from utilities import (
    adjust_brightness,
    add_hover_effect,
    add_bg_colour_hover_effect,
    set_defocus_on,
    rounded_square,
    rounded_rectangle,
    ctk_font,
    add_hover_commands,
    resize_image,
    make_label
)
from colours import *
from PIL import Image, ImageTk
from tooltip import ToolTip
from components import TagList
from shared_widgets import NoteWidget
import models


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
        super().__init__(parent, width=width, height=height, bg=canvas_colour, highlightthickness=0)
        self.width = width
        self.height = height
        self.thickness = thickness
        self.rounding = rounding
        self.border_colour = border_colour

        self.after(50, lambda: self.draw_border(bg_colour=bg_colour))

    def draw_border(self, bg_colour):
        rounded_rectangle(
            self,
            int(self.width - 2),
            int(self.height - 2),
            self.rounding,
            self.border_colour,
        )
        rounded_rectangle(
            self,
            int(self.width - 2 * self.thickness),
            int(self.height - 2 * self.thickness),
            self.rounding,
            bg_colour,
        )


# TagEditor is a reusable class that describes the UI component used to show, add, and remove tags for a board item


class TagEditor(ctk.CTkFrame):
    def __init__(self, parent, width, window):
        editor_placeholder_colour = "#63472B"
        super().__init__(parent, width=width, fg_color=BROWN, corner_radius=0)

        self.width = width
        self.tag_height = 0.13 * width
        self.tag_list_height = 0
        self.scrollbar_height = 15
        self.gap = self.width / 75
        self.max_space = self.width - self.gap - 10
        self.tag_list = None
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
            font=ctk_font(18, True),
            border_width=0,
            corner_radius=0,
        )
        self.entry.pack(side="top", padx=5, pady=(5, 3), fill="x")

        set_defocus_on(window, self.entry, [self.entry._entry])
        self.entry.bind("<Return>", lambda event: self.add_tag(self.entry.get()))

        self.canvas = tk.Canvas(self, width=self.width, height=0, highlightthickness=0, bg=BROWN)
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

        def update_scroll_region(event = None):
            x1, y1, x2, y2 = self.canvas.bbox("all")
            x2 += 5
            self.canvas.configure(scrollregion=(x1, y1, x2, y2))

        self.canvas.bind("<Configure>", update_scroll_region)

        # Add absolute border on right
        self.update_idletasks()
        tk.Frame(self, width=5, bg=BROWN).place(x=self.width - 5, y=0, relheight=1)

    def add_tag(self, text):
        if len(text) > 0 and self.tag_list.add(text):
            self._add_tag_widget(text)

    def _add_tag_widget(self, text):
        if self.tag_list is None:
            raise ValueError("tag_list not set")

        self.entry.pack_configure(pady=(5, 0))

        # Initially master = self (TagsEditor), since we do not know if the tag will be placed in a new row
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
        if TagList is None:
            raise ValueError("tag_list not set")

        if not tag in self.tag_widgets_list:
            raise ValueError(f"Tag '{tag}' not found in tag_list")

        self.tag_list.remove(tag.text)
        self.tag_widgets_list.remove(tag)
        self.space_occupied -= tag.winfo_width() + self.gap
        if self.space_occupied < self.max_space:
            self.scrollbar.pack_forget()
            self.canvas.configure(height=self.tag_list_height)
            
            if len(self.tag_list.list) == 0:
                self.canvas.configure(height=5)

        tag.destroy()

    def set_tag_list(self, tag_list: TagList):
        self.tag_list = tag_list
        
        def set_tags():
            for tag in tag_list.list:
                self._add_tag_widget(tag)
                
        self.after(10, set_tags)

    class Tag(RoundedBorderCanvas):
        def __init__(self, parent, tag_editor: "TagEditor", height, text):
            self.parent = parent
            self.height = height
            self.text = text
            self.gap = 6
            self.tag_colour = adjust_brightness(LIGHT_BROWN, -0.2)
            padding = 5

            super().__init__(parent, 0, 0, 3, BROWN, self.tag_colour, BLACK, 0.65)

            label = tk.Label(self, bg=self.tag_colour, text=text, fg=WHITE, font=ctk_font(14))
            label.pack(padx=padding, pady=height * 0.12)
            label.after(10, self.redraw_border)

            if len(text) < 4:
                label.configure(width=3)

            self.bind("<3>", lambda event: tag_editor.remove_tag(self))
            label.bind("<3>", lambda event: tag_editor.remove_tag(self))

            self.tooltip = ToolTip(label, msg="Right-click to remove", delay=0.3, bg=PRIMARY_COLOUR, relief=tk.RAISED)

        def redraw_border(self):
            self.width = self.winfo_width()
            self.height = self.winfo_height()
            self.delete("all")
            self.draw_border(self.tag_colour)

        def show(self):
            self.pack(side="left", padx=(self.gap - 1, 0), pady=(self.gap - 2, self.gap))

        def destroy(self):
            self.tooltip.destroy()
            return super().destroy()


class MainSidePanelFrame(tk.Frame):

    def __init__(self, parent, window, width):
        super().__init__(parent, bg=PRIMARY_COLOUR, width=width)

        self.pack(side="left", fill="y")
        self.pack_propagate(False)
        """ 
        This side panel widget houses the following widgets/features:
            Search bar
            Add:
                Note
                Page
                Image
            Open Board
            Delete Board
            Save Board
            
        """

        self.displayed_sections: list = []
        self.section_title_font = ctk_font(22, True)
        spacing = 22
        width = 0.85 * width
        height = 0.75 * width

        self.search = self.Search(self, width, height, spacing, window)
        self.board_options = self.BoardOptions(self, width - 10, height, spacing)
        self.add_items_widgets = self.AddItemOptions(self, width, height, spacing)
        self.colour_selector = self.ColourSelector(self, width - 10, height * 0.45, spacing)
        self.tags_editor = self.TagsSidePanel(self, width, spacing + 3, window)
        tag_list = TagList(["recipes", "C#", "General"])
        self.tags_editor.set_tag_list(tag_list)
        self.search.show()
        # self.board_options.show()
        self.add_items_widgets.show()
        self.colour_selector.show("Note")
        self.tags_editor.show()

    def clear(self):
        for section in self.displayed_sections:
            section.hide()

    ### ========================================== ###
    ### ============== Search Notes ============== ###
    ### ========================================== ###

    class Search(tk.Frame):

        def __init__(self, parent, width, height, spacing, window):
            self.width = width
            self.height = height
            self.child_widgets_height = 0.21 * self.height
            self.spacing = spacing
            super().__init__(parent, width=self.width, height=self.height, bg=PRIMARY_COLOUR)

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

            make_label(
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
                fg_color=adjust_brightness(PRIMARY_COLOUR, 0.1),
                text_color=BLACK,
                font=ctk_font(18, True),
                corner_radius=8,
            )
            self.search_bar.pack(side="left", padx=(0, 2))

            icon_size = 0.68 * self.child_widgets_height
            icon = ctk.CTkImage(
                Image.open("assets/images/search_icon_olive.png"),
                size=(icon_size, icon_size),
            )
            icon_disabled = ctk.CTkImage(
                Image.open("assets/images/search_icon_disabled.png"),
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
                hover_color=adjust_brightness(PRIMARY_COLOUR, 0.3),
                image=icon_disabled,
            )
            search_button.pack(side="right", fill="both")

            self.search_bar.bind("<Return>", lambda event: search_global(self.search_bar.get()))
            # This ensures the placeholder can still be shown after the initial focus in on the entry
            set_defocus_on(window, self.search_bar, [self.search_bar._entry])
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
            # self.pack_propagate(False)
            self.spacing = spacing
            self.button_height = int(height * 0.28)

            # ======== Open Board ========
            self.open_board_button = RoundedBorderCanvas(self, width, self.button_height)
            self.open_board_button.pack(side="top")
            self.open_board_image = resize_image(Image.open("assets/images/open_board.png"), self.button_height - 14)
            self.open_board_button.after(110, lambda: self.open_board_button.event_generate("<Leave>"))
            self.set_redraw_on_hover(self.open_board_button, self.open_board_image, 14)
            rel_x = 0.5 + 0.1 * self.button_height / width
            open_board_label = tk.Label(
                self.open_board_button,
                font=ctk_font(24),
                text="Open Board",
                bg=PRIMARY_COLOUR,
            )
            open_board_label.place(relx=rel_x, rely=0.5, anchor=tk.CENTER)
            add_bg_colour_hover_effect(self.open_board_button, open_board_label)

            # Frame to pack Lower three buttons onto
            lower_option_group = tk.Frame(self, width=width, height=self.button_height, bg=PRIMARY_COLOUR)
            lower_option_group.pack(side="top", pady=(10, 0))
            lower_option_group.pack_propagate(False)

            # ========= Save Board ==========
            save_button_width = width / 2 + 14
            self.save_board_button = RoundedBorderCanvas(lower_option_group, save_button_width, self.button_height)
            self.save_board_button.pack(side="left")
            self.save_board_image = resize_image(Image.open("assets/images/save.png"), self.button_height - 23)
            self.save_board_button.after(110, lambda: self.save_board_button.event_generate("<Leave>"))
            self.set_redraw_on_hover(self.save_board_button, self.save_board_image, 14)
            rel_x = (save_button_width - self.button_height) / save_button_width
            save_board_label = tk.Label(
                self.save_board_button,
                font=ctk_font(24),
                text="Save",
                bg=PRIMARY_COLOUR,
            )
            save_board_label.place(relx=rel_x, rely=0.5, anchor=tk.CENTER)
            add_bg_colour_hover_effect(self.save_board_button, save_board_label)

            # ======== Delete Board =========
            self.delete_board_button = RoundedBorderCanvas(lower_option_group, width / 4 - 12, self.button_height)
            self.delete_board_button.pack(side="left", padx=(5, 0))
            self.delete_board_image = resize_image(Image.open("assets/images/delete.png"), self.button_height - 20)
            self.delete_board_button.after(110, lambda: self.delete_board_button.event_generate("<Leave>"))
            self.set_redraw_on_hover(self.delete_board_button, self.delete_board_image, 10)

            # ======== Add New Board ========
            self.add_board_button = RoundedBorderCanvas(lower_option_group, width / 4 - 12, self.button_height)
            self.add_board_button.pack(side="left", padx=(5, 0))
            self.add_board_button.pack_propagate(False)
            self.add_board_button.after(110, lambda: self.add_board_button.event_generate("<Leave>"))
            plus_icon = tk.Label(
                self.add_board_button,
                bg=PRIMARY_COLOUR,
                text="+",
                font=("", 54),
                fg=GREEN,
            )
            plus_icon.pack(fill="both", expand=True, padx=(11, 9), pady=10)
            self.set_redraw_on_hover(self.add_board_button)
            add_bg_colour_hover_effect(self.add_board_button, plus_icon)

        # Method to redraw the border, background, and image of button every time the mouse hovers over
        def set_redraw_on_hover(self, canvas: RoundedBorderCanvas, image: Image = None, padding_left=0):
            x = int(image.width() / 2 + padding_left) if image else 0
            y = self.button_height / 2
            enter_commands = (
                lambda: canvas.delete("all"),
                lambda: canvas.draw_border(adjust_brightness(PRIMARY_COLOUR, 0.2)),
                lambda: image and canvas.create_image(x, y, image=image, anchor=tk.CENTER),
            )
            leave_commands = (
                lambda: canvas.delete("all"),
                lambda: canvas.draw_border(PRIMARY_COLOUR),
                lambda: image and canvas.create_image(x, y, image=image, anchor=tk.CENTER),
            )

            add_hover_commands(canvas, enter_commands, leave_commands)

        def center_coords(self, image: Image, padding_left=7):
            return int(image.width() / 2 + padding_left), self.button_height / 2

        def show(self):
            self.pack(side="top", pady=(self.spacing, 0))

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

            make_label(
                self,
                width=self.width,
                height=self.child_widgets_height,
                text="Add Items",
                fg=BLACK,
                anchor="w",
                font=parent.section_title_font,
                background=PRIMARY_COLOUR,
            ).pack(side="top")

            self.new_note_button = self.ItemButton(self, "New Note", "assets/images/items_note.png")
            self.new_page_button = self.ItemButton(self, "New Page", "assets/images/items_page.png", 2, 2)
            self.new_image_button = self.ItemButton(self, "New Image", "assets/images/items_image.png", 2, 2)

        class ItemButton(tk.Canvas):

            def __init__(self, parent, text: str, image_path: str, x_offset=0, y_offset=0):
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
                image_tk = Image.open(image_path)

                self.image = resize_image(image_tk, int(self.image_frame_size - 14))
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
                label = tk.Label(self, font=ctk_font(24), text=text, bg=PRIMARY_COLOUR, anchor="w")
                label.grid(row=0, column=1, padx=(14, 0), sticky="ew")

                # Hover effect
                add_hover_effect(
                    widget=self,
                    shape="rectangle",
                    rounding=0.5,
                    partners=(label, self.image_frame),
                )

                add_hover_commands(
                    self,
                    enter_commands=self.highlight_item_frame,
                    leave_commands=self.remove_highlight_item_frame,
                )

            def render_item_frame(self, canvas, size, thickness, colour, border_colour, image):
                # This simple method creates a square 'button' by using two rounded squares drawn on a canvas to
                # give off the appearance of a rounded border. Also loads image/icon

                rounded_square(canvas, size, 0.4, border_colour)
                rounded_square(canvas, size - thickness * 2, 0.4, colour)
                center_x = size / 2 + self.x_offset
                center_y = size / 2 + self.y_offset
                self.canvas_image = canvas.create_image(center_x, center_y, image=image, anchor=tk.CENTER)

            def highlight_item_frame(self):
                self.image_frame.delete("all")
                self.render_item_frame(
                    self.image_frame,
                    self.image_frame_size - 2,
                    3,
                    adjust_brightness(PRIMARY_COLOUR, 0.2),
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

    ### ========================================= ###
    ### ============ Colour Selector ============ ###
    ### ========================================= ###

    class ColourSelector(tk.Frame):
        def __init__(self, parent, width, height, spacing):
            super().__init__(parent, width=width, height=height, bg=PRIMARY_COLOUR)

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
                self.ColourTile(self, palette_frame, tile_width, colour).grid(row=0, column=i)
            for i, colour in enumerate(colours_row_2):
                self.ColourTile(self, palette_frame, tile_width, colour).grid(row=1, column=i)

            self.current_colour_tile = self.ColourTile(
                self,
                palette_frame,
                int(width / 4),
                STICKY_NOTE_YELLOW,
                BORDER_COLOUR,
                False,
            )
            self.current_colour_tile.grid(row=0, column=6, rowspan=2, columnspan=2, padx=(2, 0))

        def change_current_colour(self, colour):
            self.current_colour_tile.swatch.configure(bg=colour)

        def show(self, item_type: str):
            self.label.configure(text=f"Change {str.capitalize(item_type)} Colour")
            self.pack(side="top", pady=(self.spacing, 0))

        class ColourTile(tk.Frame):
            def __init__(
                self,
                colour_selector,
                parent,
                size,
                colour,
                hover_colour=PRIMARY_COLOUR,
                hover_effect=True,
            ):
                super().__init__(parent, bg=hover_colour, width=size, height=size)
                # self.colour = colour
                self.pack_propagate(False)

                self.swatch = tk.Frame(self, bg=colour)
                self.swatch.pack(padx=3, pady=3, fill="both", expand=True)

                if hover_effect:
                    add_bg_colour_hover_effect(self, hover_colour=adjust_brightness(PRIMARY_COLOUR, 0.3))

                self.bind("<1>", lambda event: colour_selector.change_current_colour(colour))
                self.swatch.bind("<1>", lambda event: colour_selector.change_current_colour(colour))

    ### ========================================= ###
    ### ============== Tags Editor ============== ###
    ### ========================================= ###

    class TagsSidePanel(TagEditor):
        def __init__(self, parent, width, spacing, window):
            self.spacing = spacing
            super().__init__(parent, width, window)

        def show(self):
            self.pack(side="top", pady=(self.spacing, 0))


class TabsAndBoard(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent, bg="purple")

        self.pack(side="left", fill="both", expand=True)


class BoardArea(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent, background=PRIMARY_COLOUR, highlightthickness=0)
        border_thickness = 10

        # Set up 3x3 grid
        self.rowconfigure(index=0, weight=0)
        self.rowconfigure(index=1, weight=1)
        self.rowconfigure(index=2, weight=0)
        self.columnconfigure(index=0, weight=0)
        self.columnconfigure(index=1, weight=1)
        self.columnconfigure(index=2, weight=0)

        # Top border
        top_border = tk.Frame(self, bg=BORDER_COLOUR, height=border_thickness)
        top_border.grid(row=0, column=0, columnspan=3, sticky="nsew")

        bottom_border = tk.Frame(self, bg=BORDER_COLOUR, height=border_thickness)
        bottom_border.grid(row=2, column=0, columnspan=3, sticky="nsew")

        right_border = tk.Frame(self, bg=BORDER_COLOUR, width=border_thickness)
        right_border.grid(row=1, column=0, sticky="nsew")

        left_border = tk.Frame(self, bg=BORDER_COLOUR, width=border_thickness)
        left_border.grid(row=1, column=2, sticky="nsew")

        self.pack(fill="both", expand=True)


class RestoreButton(ctk.CTkCanvas):

    def __init__(
        self,
        parent,
        button_size,
        icon_size,
        command,
        colour=WHITE,
        thickness=3,
        rounding=1,
    ):
        super().__init__(
            parent,
            width=button_size,
            height=button_size,
            background=parent.cget("background"),
            highlightthickness=0,
        )

        self.command = command
        self.button_size = button_size
        self.icon_size = icon_size
        self.thickness = thickness
        self.colour = colour

        self.draw_sqaure(self.thickness)
        self.bind("<Button-1>", self.on_click)
        add_hover_effect(
            widget=self,
            rounding=rounding,
            shape="square",
            restore_foreground_command=lambda: self.draw_sqaure(self.thickness),
        )

    def on_click(self, _event):
        if callable(self.command):
            self.command()
        else:
            raise ValueError("Error: provided 'command' argument is not callable")

    def draw_sqaure(self, th):
        th = th / 2
        offset = (self.button_size - self.icon_size) / 2
        self.create_line(
            offset - th,
            offset,
            self.button_size - offset + th,
            offset,
            width=self.thickness,
            fill=self.colour,
        )
        self.create_line(
            self.button_size - offset,
            offset - th,
            self.button_size - offset,
            self.button_size - offset + th,
            width=self.thickness,
            fill=self.colour,
        )
        self.create_line(
            self.button_size - offset + th,
            self.button_size - offset,
            offset - th,
            self.button_size - offset,
            width=self.thickness,
            fill=self.colour,
        )
        self.create_line(
            offset,
            self.button_size - offset + th,
            offset,
            offset - th,
            width=self.thickness,
            fill=self.colour,
        )


class MinimizeButton(ctk.CTkCanvas):

    def __init__(
        self,
        parent,
        button_size,
        icon_size,
        command,
        colour=WHITE,
        thickness=3,
        rounding=1,
    ):
        super().__init__(
            parent,
            width=button_size,
            height=button_size,
            background=parent.cget("background"),
            highlightthickness=0,
        )

        self.command = command
        self.button_size = button_size
        self.icon_size = icon_size
        self.thickness = thickness
        self.colour = colour

        self.draw_line()
        self.bind("<Button-1>", self.on_click)
        add_hover_effect(
            widget=self,
            rounding=rounding,
            shape="square",
            restore_foreground_command=self.draw_line,
        )

    def on_click(self, _event):
        if callable(self.command):
            self.command()
        else:
            raise ValueError("Error: provided 'command' argument is not callable")

    def draw_line(self):
        offset = (self.button_size - self.icon_size) / 2
        self.create_line(
            offset,
            self.button_size - offset,
            self.button_size - offset,
            self.button_size - offset,
            width=self.thickness,
            fill=self.colour,
        )

