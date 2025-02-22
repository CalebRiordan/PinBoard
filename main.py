import tkinter as tk
from widgets import (
    MainSidePanelFrame,
    TabsAndBoard,
    BoardArea,
    RestoreButton,
    MinimizeButton,
)
from shared_widgets import CloseButton, ContextMenu
from components import TabHandler, BoardHandler
from database_service import DatabaseService
from colours import *
from window_manager import WindowManager
from PIL import Image, ImageTk
from board_canvas import BoardCanvas


class App(tk.Tk):

    def __init__(self, title):
        super().__init__()

        # Instantiate custom window manager
        self.wm = WindowManager(self)
        self.context_menu = ContextMenu()
        self.context_menu.set_window(self)
        self.logo = None
        self.app_title = title

        configure_main_window(self, self.wm)

        # The working area describes the whole application UI underneath the title bar
        working_area = tk.Frame(self)
        working_area.pack(fill="both", expand=True)

        # Create side panel and board frame
        MainSidePanelFrame(working_area, self, self.wm.width * 0.25)
        tabs_and_board = TabsAndBoard(working_area)

        # get component instances
        th = TabHandler.get_instance(self)
        th.create_tab_list(tabs_and_board)
        th._tab_list.after(300, th.initialize_tab_list)

        board_area = BoardArea(tabs_and_board)
        BoardHandler(board_area)

        # fill canvas with repeatable texture images
        self.after(100, self.wm.set_resize_grips)

        # Bring window up from minimized state
        self.attributes("-topmost", 1)
        self.attributes("-topmost", 0)

    def save_and_close(self):
        # perform logic such as saving unsaved boards
        self.wm.close()


def configure_main_window(window: App, wm: WindowManager):
    window.title(window.app_title)
    wm.set_initial_geometry()

    window.minsize(750, 450)
    wm.minsize(750, 450)

    # Custom title bar
    window.overrideredirect(1)
    title_bar = tk.Frame(window, bg=PRIMARY_COLOUR, height=45)

    # Pack title bar and working area
    title_bar.pack(side="top", fill="x")
    title_bar.pack_propagate(False)

    wm.set_grip(title_bar)

    # Buttons
    close_app_button = CloseButton(
        title_bar, 30, 15, window.save_and_close, colour=OFF_WHITE, thickness=4, rounding=0.3
    )
    close_app_button.pack(side="right", padx=(0, 5))

    restore_app_button = RestoreButton(title_bar, 30, 15, wm.maximize, colour=OFF_WHITE, thickness=4, rounding=0.3)
    restore_app_button.pack(side="right", padx=(0, 5))

    minimize_app_button = MinimizeButton(title_bar, 30, 15, wm.minimize, colour=OFF_WHITE, thickness=4, rounding=0.3)
    minimize_app_button.pack(side="right", padx=(0, 5))

    # Create and pack logo in title bar
    img = Image.open("assets/images/pinboard_icon.png")
    img_width = img.width
    factor = img_width / 26
    img = img.resize((26, int(img.height / factor)))
    window.logo = ImageTk.PhotoImage(img)
    pinboard_icon = tk.Canvas(title_bar, width=36, height=36, bg=PRIMARY_COLOUR, highlightthickness=0)
    pinboard_icon.create_image(15, 18, image=window.logo)
    pinboard_icon.pack(side="left", padx=(15, 0))

    window.after(100, wm.set_taskbar_icon)


if __name__ == "__main__":
    root = App("Pinboard")

    root.mainloop()
