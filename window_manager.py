import tkinter as tk
import ctypes
from utilities import set_opacity, get_display_size
from colours import *


class WindowManager:
    root = None

    # Application dimensions
    width = 0
    height = 0
    min_width = 0
    min_height = 0

    rel_x = 0
    rel_y = 0

    # Positions of sides of application:
    north = 0
    east = 0
    south = 0
    west = 0

    def __init__(self, window: tk.Tk):
        self.root = window
        self.maximized = False
        self.deiconified = True

        # Bind the event that triggers when the window is shown to remove default title bar
        self.root.bind("<Map>", self.restore)

    def set_initial_geometry(self):
        sc_width, sc_height = get_display_size()
        self.width, self.height = int(sc_width * 0.75), int(sc_height * 0.75)

        self.west = (sc_width - self.width) // 2
        self.north = (sc_height - self.height) // 3
        # Using wm_geometry() instead of geometry(). Tk still adjusts window size after geometry() is called for some reason
        self.root.wm_geometry(f"{self.width}x{self.height}+{self.west}+{self.north}")

    def minsize(self, width, height):
        self.min_width = width
        self.min_height = height

    def set_grip(self, widget: tk.Widget):
        def move_window(e):
            x = e.x_root - self.rel_x
            y = e.y_root - self.rel_y
            self.root.geometry(f"+{x}+{y}")

        def hold(e):
            self.rel_x = e.x
            self.rel_y = e.y

        widget.bind("<1>", hold)
        widget.bind("<B1-Motion>", move_window)

    def close(self):
        # perform logic such as saving unsaved boards
        self.root.destroy()

    def maximize(self):
        def get_fullscreen_geometry():
            rect = ctypes.wintypes.RECT()
            SPI_GETWORKAREA = 0x0030
            ctypes.windll.user32.SystemParametersInfoW(
                SPI_GETWORKAREA, 0, ctypes.byref(rect), 0
            )
            width = rect.right
            height = rect.bottom
            return f"{width}x{height}+0+0"

        root = self.root
        if self.maximized == False:
            dimensions = get_fullscreen_geometry()
            root.geometry(dimensions)

            self.maximized = True
        else:
            root.wm_geometry(f"{self.width}x{self.height}+{self.west}+{self.north}")
            self.maximized = False

    def minimize(self):
        self.root.state("withdrawn")
        self.root.overrideredirect(False)
        self.root.state("iconic")
        self.deiconified = False

    def restore(self, e: tk.Event):
        if e.widget == self.root:
            self.root.overrideredirect(1)
            if not self.deiconified:
                self.set_taskbar_icon()

    def set_taskbar_icon(self):
        GWL_EXSTYLE = -20
        WS_EX_APPWINDOW = 0x00040000
        WS_EX_TOOLWINDOW = 0x00000080

        hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
        # Get extended styles information
        style = ctypes.windll.user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        # remove WS_EX_TOOLWINDOW flag
        style = style & ~WS_EX_TOOLWINDOW
        # ensure WS_EX_APPWINDOW flag for taskbar icon
        style = style | WS_EX_APPWINDOW
        # ============================ ^^ VERY IMPORTANT ^^ ============================
        ctypes.windll.user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, style)
        self.root.withdraw()
        self.deiconified = True
        self.root.after(10, self.root.deiconify)

    def set_resize_grips(self):
        try:
            # set positions of sides
            self.root.update_idletasks()
            self.north = self.root.winfo_rooty()
            self.west = self.root.winfo_rootx()
            self.east = self.root.winfo_rootx() + self.root.winfo_width()
            self.south = self.root.winfo_rooty() + self.root.winfo_height()

            def OnMotion(event: tk.Event, mode):
                x_pointer = event.x_root
                y_pointer = event.y_root
                print("OnMotion")

                new_width_e = x_pointer - self.west
                new_width_w = self.east - x_pointer
                new_height_n = self.south - y_pointer
                new_height_s = y_pointer - self.north

                def update_geometry():
                    self.root.geometry(
                        f"{self.width}x{self.height}+{self.west}+{self.north}"
                    )

                    # Update grip sizes
                    grip_n.place_configure(width=self.width - self.corners)
                    grip_e.place_configure(height=self.height - self.corners)
                    grip_s.place_configure(width=self.width - self.corners)
                    grip_w.place_configure(height=self.height - self.corners)

                if mode == "n" and new_height_n >= self.min_height:
                    self.height = new_height_n
                    self.north = y_pointer
                    update_geometry()
                    return

                if (
                    mode == "ne"
                    and new_height_n >= self.min_height
                    and new_width_e >= self.min_width
                ):
                    self.height = new_height_n
                    self.width = new_width_e
                    self.north = y_pointer
                    self.east = x_pointer
                    update_geometry()
                    return

                if mode == "e" and new_width_e >= self.min_width:
                    self.width = new_width_e
                    self.east = x_pointer
                    update_geometry()
                    return

                if (
                    mode == "se"
                    and new_height_s >= self.min_height
                    and new_width_e >= self.min_width
                ):
                    self.height = new_height_s
                    self.width = new_width_e
                    self.south = y_pointer
                    self.east = x_pointer
                    update_geometry()
                    return

                if mode == "s" and new_height_s >= self.min_height:
                    self.height = new_height_s
                    self.south = y_pointer
                    update_geometry()
                    return

                if (
                    mode == "sw"
                    and new_height_s >= self.min_height
                    and new_width_w >= self.min_width
                ):
                    self.height = new_height_s
                    self.width = new_width_w
                    self.south = y_pointer
                    self.west = x_pointer
                    update_geometry()
                    return

                if mode == "w" and new_width_w >= self.min_width:
                    self.width = new_width_w
                    self.west = x_pointer
                    update_geometry()
                    return

                if (
                    mode == "nw"
                    and new_height_n >= self.min_height
                    and new_width_w >= self.min_width
                ):
                    self.height = new_height_n
                    self.width = new_width_w
                    self.north = y_pointer
                    self.west = x_pointer
                    update_geometry()
                    return

            grip_thickness = 10
            self.corners = 2 * grip_thickness
            grip_width = self.width - self.corners
            grip_height = self.height - self.corners

            grip_n = tk.Label(self.root, bg=PRIMARY_COLOUR, cursor="sb_v_double_arrow")
            grip_n.place(
                relx=0.5, rely=0, width=grip_width, height=grip_thickness, anchor="n"
            )
            grip_n.bind("<B1-Motion>", lambda e: OnMotion(e, "n"))
            set_opacity(grip_n, 0)

            grip_ne = tk.Label(self.root, bg=PRIMARY_COLOUR, cursor="size_ne_sw")
            grip_ne.place(
                relx=1.0, rely=0, width=grip_thickness, height=grip_thickness, anchor="ne"
            )
            grip_ne.bind("<B1-Motion>", lambda e: OnMotion(e, "ne"))
            set_opacity(grip_ne, 0)

            grip_e = tk.Label(self.root, bg=PRIMARY_COLOUR, cursor="sb_h_double_arrow")
            grip_e.place(
                relx=1.0, rely=0.5, anchor="e", width=grip_thickness, height=grip_height
            )
            grip_e.bind("<B1-Motion>", lambda e: OnMotion(e, "e"))
            set_opacity(grip_e, 0)

            grip_se = tk.Label(self.root, bg=PRIMARY_COLOUR, cursor="size_nw_se")
            grip_se.place(
                relx=1.0, rely=1.0, width=grip_thickness, height=grip_thickness, anchor="se"
            )
            grip_se.bind("<B1-Motion>", lambda e: OnMotion(e, "se"))
            set_opacity(grip_se, 0)

            grip_s = tk.Label(self.root, bg=PRIMARY_COLOUR, cursor="sb_v_double_arrow")
            grip_s.place(
                relx=0.5, rely=1, width=grip_width, height=grip_thickness, anchor="s"
            )
            grip_s.bind("<B1-Motion>", lambda e: OnMotion(e, "s"))
            set_opacity(grip_s, 0)

            grip_sw = tk.Label(self.root, bg=PRIMARY_COLOUR, cursor="size_ne_sw")
            grip_sw.place(
                relx=0, rely=1, width=grip_thickness, height=grip_thickness, anchor="sw"
            )
            grip_sw.bind("<B1-Motion>", lambda e: OnMotion(e, "sw"))
            set_opacity(grip_sw, 0)

            grip_w = tk.Label(self.root, bg=PRIMARY_COLOUR, cursor="sb_h_double_arrow")
            grip_w.place(
                relx=0, rely=0.5, width=grip_thickness, height=grip_height, anchor="w"
            )
            grip_w.bind("<B1-Motion>", lambda e: OnMotion(e, "w"))
            set_opacity(grip_w, 0)

            grip_nw = tk.Label(self.root, bg=PRIMARY_COLOUR, cursor="size_nw_se")
            grip_nw.place(
                relx=0, rely=0, width=grip_thickness, height=grip_thickness, anchor="nw"
            )
            grip_nw.bind("<B1-Motion>", lambda e: OnMotion(e, "nw"))
            set_opacity(grip_nw, 0)
        except Exception as e:
            print(e)
