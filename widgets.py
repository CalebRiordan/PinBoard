import tkinter as tk
import customtkinter as ctk
import utilities as utils
from colours import *
from enum import Enum


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
        utils.add_hover_effect(
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
        utils.add_hover_effect(
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
