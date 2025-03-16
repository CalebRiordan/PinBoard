import tkinter as tk
from widgets import (
    TabsAndBoard,
    BoardArea,
    RestoreButton,
    MinimizeButton,
)
from shared_widgets import CloseButton, ContextMenu, MainSidePanelFrame
from components import TabHandler, BoardHandler
from colours import *
from window_manager import WindowManager
from PIL import Image, ImageTk
from utilities import get_display_size, update_setting
from service_locator import Services
from database_service import DatabaseService


class App(tk.Tk):

    def __init__(self, title):
        super().__init__()

        # ======== Create and Register Global Services ==========
        
        # Window Manager
        self.wm = WindowManager(self, title)
        self.after(10, self.wm.set_resize_grips)
        Services.register("WindowManager", self.wm)
        
        # Context Menu
        context_menu = ContextMenu(self.wm.root)
        Services.register("ContextMenu", context_menu)
        
        # Database Service
        database_service = DatabaseService()
        Services.register("DatabaseService", database_service)

        # Title bar
        self.logo = None
        title_bar = self.custom_title_bar(self)
        self.wm.set_grip(title_bar)
        self.after(100, self.wm.set_taskbar_icon)

        # The working area describes the whole application UI underneath the title bar
        working_area = tk.Frame(self)
        working_area.pack(fill="both", expand=True)

        # UI components on the working area
        side_panel = MainSidePanelFrame(working_area, self, self.wm.width * 0.25)
        tabs_and_board = TabsAndBoard(working_area)
        board_area = BoardArea(tabs_and_board)

        
        # Tab Handler and Board Handler
        bh = BoardHandler(board_area, side_panel)
        th = TabHandler(self, bh)
        Services.register("TabHandler", th)
        th.create_tab_list_on(parent=tabs_and_board)

        # Bring window up from minimized state
        self.attributes("-topmost", 1)
        self.attributes("-topmost", 0)

    def save_and_close(self):
        # perform logic such as saving unsaved boards
        self.wm.close()
        
    def custom_title_bar(self, window: tk.Tk):
        window.overrideredirect(1)
        title_bar = tk.Frame(self, bg=PRIMARY_COLOUR, height=45)
        title_bar.pack(side="top", fill="x")
        title_bar.pack_propagate(False)

        # Buttons
        close_app_button = CloseButton(
            title_bar, 30, 15, window.save_and_close, colour=OFF_WHITE, thickness=4, rounding=0.3
        )
        close_app_button.pack(side="right", padx=(0, 5))

        restore_app_button = RestoreButton(title_bar, 30, 15, self.wm.maximize, colour=OFF_WHITE, thickness=4, rounding=0.3)
        restore_app_button.pack(side="right", padx=(0, 5))

        minimize_app_button = MinimizeButton(title_bar, 30, 15, self.wm.minimize, colour=OFF_WHITE, thickness=4, rounding=0.3)
        minimize_app_button.pack(side="right", padx=(0, 5))

        # Create and pack logo in title bar
        img = Image.open("assets/images/pinboard_icon.png")
        img_width = img.width
        factor = img_width / 26
        img = img.resize((26, int(img.height / factor)))
        self.logo = ImageTk.PhotoImage(img)
        pinboard_icon = tk.Canvas(title_bar, width=36, height=36, bg=PRIMARY_COLOUR, highlightthickness=0)
        pinboard_icon.create_image(15, 18, image=window.logo)
        pinboard_icon.pack(side="left", padx=(15, 0))
        
        return title_bar


if __name__ == "__main__":
    root = App("Pinboard")

    root.mainloop()
