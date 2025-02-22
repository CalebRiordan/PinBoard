import asyncio
import re
from database_service import DatabaseService
from datetime import date
import customtkinter as ctk
from board_canvas import BoardCanvas
from models import *
from shared_widgets import CloseButton, ContextMenu
from typing import List
import tkinter as tk
from tooltip import ToolTip
from typing import List, Dict
import utilities as utils
from tkinter import messagebox

# Singleton class for TABS and BOARDS with related utility methods


class BoardHandler:
    _instance = None
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

    @staticmethod
    def get_instance(canvas_parent=None):
        if BoardHandler._instance is None:
            if not canvas_parent:
                raise ValueError("BoardHandler cannot be initialized without a 'canvas_parent'.")
            return BoardHandler()
        return BoardHandler._instance

    def __init__(self, canvas_parent):
        if BoardHandler._instance is not None:
            raise Exception("BoardHandler class is a singleton. An instance already exists")
        BoardHandler._instance = self
        self._canvas_parent = canvas_parent

        # Set scale factor for items
        sc_width, sc_height = utils.get_display_size()
        scale_factor = sc_width / 1920 * 0.7 + sc_height / 1080 * 0.3
        utils.update_setting("DEVICE_SCALE_FACTOR", scale_factor)

        self.db_service = DatabaseService()

    def initialize_boards(self):
        # TODO:
        #   open_boards = db_service.get_open_boards()
        #   self._all_boards_ids = db_service.get_all_board_ids()

        # TEMP
        # Get all board IDs from database and create list of objects
        all_boards = utils._create_mock_data()

        # Create sublist for boards that are OPEN
        open_boards = [board for board in all_boards if board.open]
        self._all_boards_ids = [board.board_id for board in all_boards]

        return open_boards

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
        else:
            raise ValueError(f"Board with id '{id}' not found amongst currently open boards")

    def new_board(self):
        new_board_id = self.generate_new_board_id()
        new_board = Board(new_board_id, "", date.today(), True, [])
        new_board.saved = False
        self._open_boards[new_board_id] = new_board
        self._open_canvases[new_board_id] = BoardCanvas(self._canvas_parent)
        self._all_boards_ids.append(new_board_id)
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
                board_id = self._current_board.board_id
            else:
                raise ValueError(f"No current board set - Please specify a board id for the board to close.")
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
        return self._open_canvases[self._current_board.board_id]

    def generate_new_board_id(self):
        for i in range(1, len(self._all_boards_ids) + 2):
            if i not in self._all_boards_ids:
                return i
        raise Exception("New board ID could not be generated. All IDs within range already taken")


# Singleton class for TABS and BOARDS with related utility methods


class TabHandler:
    _instance = None
    _bh = None  # Local board handler
    _tab_list: "TabHandler.TabList" = None
    window = None
    current_tab: "TabHandler.Tab" = None

    @staticmethod
    def get_instance(window: tk.Tk = None):
        if TabHandler._instance is None:
            if window:
                TabHandler(window)
            else:
                raise Exception("TabHandler has not been initialized - 'window' argument must be passed.")
        return TabHandler._instance

    def __init__(self, window: tk.Tk):
        if TabHandler._instance is not None:
            raise Exception("TabHandler class is a singleton. An instance already exists")
        else:
            TabHandler._instance = self
            self.window = window

    class TabList(tk.Frame):
        def __init__(self, parent):
            super().__init__(parent, bg=PRIMARY_COLOUR, height=utils.get_setting("TAB_LIST_HEIGHT"))

            # create lists for each tab list object
            self.tabs: List[TabHandler.Tab] = []

            self.pack_propagate(False)

            self.add_tab_button = TabHandler.AddTabButton(self)

            # Set binding for context menu
            cm = ContextMenu.get_instance()
            buttons = self.tab_list_cm_buttons(cm, TabHandler.get_instance())
            cm.register(self, buttons)
            self.bind("<Button-3>", lambda event: cm.open_menu(self, event))

        def PlaceAddTabButton(self, side="west"):
            if self.add_tab_button:
                self.add_tab_button.pack_forget()
            if side == "east":
                self.add_tab_button.pack(side="right", padx=(0, 5))
            else:
                self.add_tab_button.pack(side="left", padx=(5, 0))

        def AddTab(self, tab: "TabHandler.Tab"):
            if len(self.tabs) >= 10:
                print("maximum tabs reached")
                return False
            self.tabs.append(tab)
            tab.pack(side="left")
            self.PlaceAddTabButton()
            self.AdjustTabs(False)
            return True

        def RemoveTab(self, tab: "TabHandler.Tab"):
            if len(self.tabs) > 0:
                tab.destroy()
                self.tabs.remove(tab)
                self.add_tab_button.disabled = False
                self.AdjustTabs(True)

        def AdjustTabs(self, remove: bool):
            # Method to rearrange tabs and add button in correct order
            def repack_tabs(tablist: "TabHandler.TabList", new_tab_width):
                for tab in tablist.tabs:
                    tab.pack_forget()
                    tab.inner_tab.configure(width=new_tab_width)
                    tab.pack(side="left", anchor="s")

                if new_tab_width != utils.get_setting("TAB_WIDTH"):
                    # Tab list full
                    self.PlaceAddTabButton("east")
                else:
                    # Tab list still has space for another tab
                    self.PlaceAddTabButton()

            tab_list_width = self.winfo_width()
            add_button_width = utils.get_setting("TAB_HEIGHT")
            space_for_tabs = tab_list_width - (add_button_width + 15)
            not_enough_space = space_for_tabs <= ((utils.get_setting("TAB_WIDTH") + 10) * len(self.tabs))
            new_tab_width = utils.get_setting("TAB_WIDTH")
            # If ADDING a tab
            if not remove:
                # If there is not enough space for new tab:
                if not_enough_space:
                    # Calculate new tab width
                    usable_space_per_tab = space_for_tabs / len(self.tabs)
                    new_tab_width = int(usable_space_per_tab) - 10
                repack_tabs(self, new_tab_width)

            # if REMOVING a tab
            elif not_enough_space:
                # Calculate new tab width
                usable_space_per_tab = space_for_tabs / len(self.tabs)
                new_tab_width = int(usable_space_per_tab) - 10
            repack_tabs(self, new_tab_width)

        def tab_list_cm_buttons(self, cm: ContextMenu, th: "TabHandler"):
            # Prepare all context menu buttons for a Tab

            close_all = cm.button("Close All Tabs", lambda event: th.close_all_tabs())
            open = cm.button("Open New Tab", lambda event: th.add_new_tab())

            return (close_all, open)

    class AddTabButton(tk.Frame):
        def __init__(self, parent: "TabHandler.TabList"):
            super().__init__(
                parent,
                bg=PRIMARY_COLOUR,
                width=utils.get_setting("TAB_HEIGHT"),
                height=utils.get_setting("TAB_HEIGHT"),
            )
            self.pack(side="left", padx=(5, 0))
            self.pack_propagate(False)

            self.tab_list = parent
            self.disabled = False

            self.label = tk.Label(self, bg=PRIMARY_COLOUR, text="+", font=("", 34), fg=BLACK)
            self.label.pack(fill="both", expand=True, padx=5, pady=5)
            self.label.bind("<Button-1>", self.add_tab)

            utils.add_bg_colour_hover_effect(self, self.label)

        def add_tab(self, event):
            if (not self.disabled) and (len(self.tab_list.tabs) < 10):
                th = TabHandler.get_instance()
                th.add_new_tab()

    class Tab(tk.Frame):
        def __init__(self, parent: "TabHandler.TabList", board_id, title):
            super().__init__(parent, background=PRIMARY_COLOUR, highlightthickness=0)

            tab_width = utils.get_setting("TAB_WIDTH")
            tab_height = utils.get_setting("TAB_HEIGHT")

            self.inner_tab = tk.Canvas(
                self,
                bg=PRIMARY_COLOUR,
                height=tab_height,
                width=tab_width,
                highlightthickness=0,
            )

            # ========== Instance and local variables ==========
            self.board_id = board_id
            self.title = title
            self.button_size = tab_height - 25
            th = TabHandler.get_instance()
            font = ctk.CTkFont(family="Helvetica", size=16, weight="bold")
            updated_colour = tk.StringVar(value=PRIMARY_COLOUR)

            # ============= Setup grid =============
            self.inner_tab.rowconfigure(0, weight=1)
            self.inner_tab.columnconfigure(0, weight=1)
            self.inner_tab.columnconfigure(1, weight=0)
            self.inner_tab.grid_propagate(False)
            self.inner_tab.pack(padx=5, pady=(4, 3), expand=True)

            # ============= Child widgets =============
            label_text = self.title or "New Tab"
            self.label = ctk.CTkLabel(
                self.inner_tab,
                text=label_text,
                font=font,
                bg_color=PRIMARY_COLOUR,
                text_color=BLACK,
                anchor="w",
            )
            self.label.grid(row=0, column=0, sticky="ew", padx=(10, 2), pady=(3, 0))

            self.close_button = TabHandler.CloseTabButton(
                parent=self.inner_tab, tab_to_close=self, colourVar=updated_colour
            )

            self.placeholder_button = tk.Frame(
                self.inner_tab,
                width=self.button_size,
                height=self.button_size,
                bg=PRIMARY_COLOUR,
                highlightthickness=0,
            )
            self.placeholder_button.grid(row=0, column=1, padx=(3, 5))

            self.bind_tab("<Button-1>", lambda event: th.swap_tabs(self))

            # ============= Context Menu setup + binding =============
            cm = ContextMenu.get_instance()
            buttons = self.tab_cm_buttons(cm, th)
            cm.register(self, buttons)
            self.bind_tab("<Button-3>", lambda event: cm.open_menu(self, event))

            # ============= Add hover effect to tabs =============
            utils.add_hover_effect(
                widget=self,
                target_widget=self.inner_tab,
                rounding=0.4,
                shape="rectangle",
                margin=5,
                restore_foreground_command=self.restore_text_and_close_button,
                partners=(self.label, self.close_button, self.placeholder_button),
            )
            utils.add_hover_commands(
                self.inner_tab,
                lambda: self.show_close_button(True),
                lambda: self.show_close_button(False),
            )

            # ============= Renaming feature =============
            self.entry = ctk.CTkEntry(
                self.inner_tab,
                width=tab_width,
                height=tab_height,
                fg_color=utils.adjust_brightness(PRIMARY_COLOUR, -0.2),
                border_width=0,
                corner_radius=8,
                font=font,
            )

            self.label.bind("<Double-1>", self.start_rename)
            self.entry.bind("<Return>", lambda event: self.process_rename(th, event))
            self.entry.bind("<Escape>", self.end_rename)
            self.close_after_rename = False
            self.tooltip = self.create_tooltip(label_text)
            utils.set_defocus_on(
                th.window, self.entry, [self.entry, self.close_button], lambda: self.process_rename(th)
            )

        def create_tooltip(self, text):
            return ToolTip(
                self.label,
                msg=text,
                delay=0.5,
                persist=False,
                follow=False,
                bg=PRIMARY_COLOUR,
                relief=tk.RAISED,
            )

        def start_rename(self, event=None, close_after=False):
            self.entry.delete(0, "end")
            self.entry.insert(0, self.title)
            self.label.grid_forget()
            self.entry.grid(row=0, column=0, sticky="EW", padx=(2, 0), pady=(1, 0))
            self.entry.focus()
            self.entry.select_range(0, "end")
            self.close_after_rename = close_after

        def process_rename(self, th: "TabHandler" = None, event=None):
            async def save_board(th_):
                if th == None:
                    raise ValueError("TabHandler instance must be provided when renaming a board before closing")
                if self.close_after_rename:
                    await th_.save_and_close_tab(self)
                    self.close_after_rename = False
                else:
                    await th_.save_tab(self)

            if not self.entry.winfo_exists():
                return

            self.title = self.entry.get().strip()
            if self.title != "":
                if re.match(r"^[a-zA-Z0-9_ ]+$", self.title):
                    if re.search(r"[a-zA-Z].*[a-zA-Z].*[a-zA-Z]", self.title):
                        self.label.configure(text=self.title)
                        self.tooltip = self.create_tooltip(self.title)
                    else:
                        messagebox.showerror(
                            "Invalid Name",
                            "Please ensure your board name contains at least 3 letters. Numbers and underscores '_' are optional.",
                        )
                        self.entry.focus()
                        return
                else:
                    messagebox.showerror("Invalid Name", "Please do not use special characters in your board name.")
                    self.entry.focus()
                    return
            else:
                self.end_rename()
                return

            self.end_rename()

            asyncio.run(save_board(th))

        def end_rename(self, event=None):
            self.entry.grid_forget()
            self.label.grid(row=0, column=0, sticky="EW", padx=(10, 0), pady=(3, 0))
            self.focus()

        def tab_cm_buttons(self, cm: ContextMenu, th: "TabHandler"):
            # Prepare all context menu buttons for a Tab

            close = cm.button("Close Tab", lambda event: th.close_tab(self))
            delete = cm.button("Delete Board", lambda event: th.delete_board(self))
            rename = cm.button("Rename Tab", lambda event: self.start_rename())

            return (close, rename)

        def bind_tab(self, command, handler):
            self.bind(command, handler)
            self.inner_tab.bind(command, handler)
            self.label.bind(command, handler)

        def restore_text_and_close_button(self):
            self.label.grid_forget()
            self.close_button.grid_forget()
            self.label.grid(row=0, column=0, sticky="EW", padx=(10, 2), pady=(3, 0))
            self.close_button.grid(row=0, column=1, padx=(3, 5))

        def show_close_button(self, flag: bool = True):
            self.placeholder_button.grid_forget()
            self.close_button.grid_forget()

            if flag:
                self.close_button.grid(row=0, column=1, padx=(3, 7))
            else:
                self.placeholder_button.grid(row=0, column=1, padx=(3, 7))

        def truncate_label(self, max_width):
            # TODO: This method is currently not in use. Delete if not necessary in future

            temp_label = ctk.CTkLabel(
                self.label,
                text=self.title,
                font=ctk.CTkFont(family="Helvetica", size=16, weight="bold"),
            )
            temp_label.update_idletasks()
            text_width = temp_label.winfo_reqwidth()
            if text_width > max_width:
                truncated_text = self.title
                while text_width > max_width:
                    truncated_text = truncated_text[:-1]
                    temp_label.configure(text=truncated_text + "...")
                    temp_label.update_idletasks()
                    text_width = temp_label.winfo_reqwidth()

                self.label.configure(text=truncated_text + "...")

    class CloseTabButton(CloseButton):
        def __init__(self, parent, tab_to_close, colourVar: tk.StringVar = None):
            button_size = tab_to_close.button_size
            cross_size = button_size * 0.6
            th = TabHandler.get_instance()

            def command():
                return th.close_tab(tab_to_close)

            super().__init__(
                parent,
                button_size,
                cross_size,
                command,
                hover_effect=False,
                colour=GRAY,
                rounding=1,
                colourVar=colourVar,
            )

            utils.add_hover_commands(
                self,
                enter_commands=lambda: self.draw_x(OFF_WHITE),
                leave_commands=lambda: self.draw_x(GRAY),
            )

    def create_tab_list(self, tabs_and_board):
        self._tab_list = TabHandler.TabList(tabs_and_board)
        self._tab_list.pack(side="top", fill="x")

    def initialize_tab_list(self):
        self._bh = BoardHandler.get_instance()
        # Create all the tab objects and populate th.tab_list.tabs
        open_boards = self._bh.initialize_boards()
        for board in open_boards:
            # Create and update list of tabs
            self.open_tab(board)

        # Check if there was a tab open when app was stopped previously
        initial_tab_id = utils.get_setting("LAST_OPEN_TAB")
        if initial_tab_id == -1:
            # select first tab by default
            self.swap_tabs(self._tab_list.tabs[0])
        else:
            # otherwise, select last-opened tab
            tab = self.find_tab_by_id(initial_tab_id)
            if tab != None:
                self.swap_tabs(tab)

    def tab_from_board(self, board: Board):
        return TabHandler.Tab(self._tab_list, board.board_id, board.name)

    def swap_tabs(self, tab_to_swap_to: "Tab"):
        #  Swapping tabs involves:
        #    removing highlight effect from current tab
        #    call swap_boards() in board handler passing tab's board_id
        #    set current_tab to tab passed as argument
        #    add highlight effect to new tab

        tab = tab_to_swap_to

        if self.current_tab is None:
            self.change_tab_hover_effect(tab)
            self._bh.show_board(tab.board_id)
            self.highlight(tab)
            self.current_tab = tab

        elif self.current_tab.board_id != tab.board_id:
            self.change_tab_hover_effect(tab, self.current_tab)
            self.remove_highlight(self.current_tab)
            self._bh.swap_boards(tab.board_id)
            self.highlight(tab)
            self.current_tab = tab

    def change_tab_hover_effect(self, to_tab: "Tab", from_tab: "Tab" = None):
        tab = to_tab

        if from_tab != None:
            if from_tab.board_id != tab.board_id:
                # Apply normal hover effect to deselected tab
                utils.remove_hover_effect(from_tab)
                utils.add_hover_effect(
                    widget=from_tab,
                    target_widget=from_tab.inner_tab,
                    rounding=0.4,
                    shape="rectangle",
                    margin=5,
                    restore_foreground_command=from_tab.restore_text_and_close_button,
                    partners=(
                        from_tab.label,
                        from_tab.close_button,
                        from_tab.placeholder_button,
                    ),
                )
                # Apply DIFFERENT hover effect to newly-selected tab
                utils.remove_hover_effect(tab)
                utils.add_hover_effect(
                    tab,
                    target_widget=tab.inner_tab,
                    shape="rectangle",
                    partners=(
                        tab.inner_tab,
                        tab.label,
                        tab.close_button,
                        tab.placeholder_button,
                    ),
                )
                tab.event_generate("<Enter>")
                tab.event_generate("<Leave>")
        else:
            # Apply DIFFERENT hover effect to newly selected tab
            utils.remove_hover_effect(tab)
            utils.add_hover_effect(
                tab,
                target_widget=tab.inner_tab,
                shape="rectangle",
                partners=(
                    tab.inner_tab,
                    tab.label,
                    tab.close_button,
                    tab.placeholder_button,
                ),
            )

    def add_new_tab(self):
        # Create new tab and board objects
        new_board = self._bh.new_board()
        new_tab = self.tab_from_board(new_board)
        self._tab_list.AddTab(new_tab)
        self.swap_tabs(new_tab)

        if len(self._tab_list.tabs) >= 10:
            # Change colour to disabled colour
            self._tab_list.add_tab_button.disabled = True

    def open_tab(self, board: Board):
        tab = self.tab_from_board(board)
        if self._tab_list.AddTab(tab):
            self._bh.open_board(board.board_id)
            return True
        return False

    def close_tab(self, tab: "TabHandler.Tab"):
        """
        Prompts user to close the board and initiates the board naming process if user wants to save new board
        """
        board = self._bh.get_board(tab.board_id)
        if not board.saved:
            res = messagebox.askyesnocancel("Save Board", "Do you want to save this board?")
            if res:
                # Save board
                if board.name == "":
                    # Rename board before saving
                    tab.start_rename(close_after=True)
            elif res == False:
                # Close board without saving
                self._finalize_close(tab)
        else:
            self._finalize_close(tab)

    async def save_and_close_tab(self, tab):
        task = await self.save_tab(tab)
        if task == True:
            self._finalize_close(tab)

    def save_tab(self, tab: "TabHandler.Tab"):
        return asyncio.to_thread(self._bh.save_board, tab.board_id, tab.title)

    def _finalize_close(self, tab):
        tabs = self._tab_list.tabs
        tab_index = -1

        # get index of tab if it exists
        try:
            tab_index = tabs.index(tab)
        except ValueError:
            raise Exception("Tab does not exist")

        if tab == self.current_tab:
            # Tab being closed is the current tab
            if len(tabs) > 1:
                # but not the only tab
                if tab_index - 1 == -1:
                    adjacent_tab = tabs[tab_index + 1]
                else:
                    adjacent_tab = tabs[tab_index - 1]

                self.swap_tabs(adjacent_tab)
                self._bh.close_board(tab.board_id)
            else:
                # and the only tab
                self._bh.close_board(tab.board_id)
                self.current_tab = None

        # Remove TabWidget in the main tab list, which will call self.detroy() to delete the tab
        self._tab_list.RemoveTab(tab)

    def close_all_tabs(self):
        tabs = self._tab_list.tabs[:]
        for tab in tabs:
            self.close_tab(tab)
        self.add_new_tab()

    def highlight(self, tab: "Tab"):
        tab.config(bg=OLIVE_GREEN)

    def remove_highlight(self, tab: "Tab"):
        tab.config(bg=PRIMARY_COLOUR)

    def find_tab_by_id(self, board_id):
        return next((tab for tab in self._tab_list.tabs if tab.board_id == board_id), None)

    def save_last_opened_tab(tab_id):
        utils.update_setting("LAST_TAB", tab_id)

    def delete_board(self, tab: "Tab"):
        self.close_tab(tab)
        # self._bh.delete_board(tab.board_id)


# Class for simple logic for handling a board item's tags


class TagList:

    list = []
    text_set = set()  # set

    def __init__(self, tags=List[str]):
        self.add_tags(tags)

    def add(self, text):
        if len(text) > 15:
            # TODO: popup -> tag is too long
            print("Tag can only have a maximum of 15 characters")
            return False
        if len(self.list) > 10:
            # TODO: popup -> too many tags
            print("too many tags")
            return False
        if text in self.text_set:
            # TODO: popup -> tag already exists
            print("tag already exists")
            return False

        # Update instance variables
        self.list.append(text)
        self.text_set.add(text)

        return True

    def remove(self, text):
        self.list.remove(text)
        self.text_set.remove(text)

    def add_tags(self, tags):
        for tag in tags:
            self.add(tag)
