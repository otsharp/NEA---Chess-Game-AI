from abc import ABC, abstractmethod
import os
#from Chess import usage
from ttkthemes import themed_tk as t_tk
import tkinter as tk
from PIL import Image, ImageTk
from functools import partial
import random
import time


class UI(ABC):
    def __init__(self, game):
        self._game = game

    @abstractmethod
    def _display_board(self):
        raise NotImplementedError

    @abstractmethod
    def _get_move(self):
        raise NotImplementedError

    @abstractmethod
    def _get_settings(self):
        raise NotImplementedError

    @abstractmethod
    def _get_draw_decision(self, player):
        raise NotImplementedError


class GUI(UI):
    def __init__(self, game):
        super().__init__(game)
        self._root = t_tk.ThemedTk()
        self._root.title("Chess")
        self._root.geometry("600x600")

        self.start = []
        self.finish = []

        self._pos_buttons = []
        self._root.sprites = {}
        self._root.sprites["None"] = ImageTk.PhotoImage(Image.open("Sprites/None.png"))
        for colour in ["White", "Black"]:
            for piece in ["Rook", "Knight", "Bishop", "Queen", "King", "Pawn"]:
                for i in range(2):
                    self._root.sprites[f"{piece} - {colour} - {['Normal', 'Big'][i]}"] = ImageTk.PhotoImage(Image.open(f"Sprites/{piece} - {colour}.png").resize([(60, 60), (80, 80)][i], Image.ANTIALIAS))

        self._board_frame = tk.Frame(self._root)
        self._board_frame.grid(row=0, column=0, sticky="nesw")
        tk.Grid.rowconfigure(self._root, 0, weight=1)
        tk.Grid.columnconfigure(self._root, 0, weight=1)

        tk.Grid.columnconfigure(self._board_frame, 0, weight=1)
        for r in range(self._game._SIZE):
            row_frame = tk.Frame(self._board_frame)
            row_frame.grid(row=r, column=0, sticky="nesw")
            tk.Grid.rowconfigure(self._board_frame, r, weight=1)
            tk.Grid.rowconfigure(row_frame, 0, weight=1)
            self._pos_buttons.append([])
            for c in range(self._game._SIZE):
                image = ""
                button = tk.Button(row_frame, image=image, bg=["#B88658", "#F0D2AD"][(r + c + 1) % 2], height=100, width=100, relief="flat", command=partial(self.select_piece, r, c))
                self._pos_buttons[r].append(button)
                button.grid(row=0, column=c, sticky="nesw")
                tk.Grid.columnconfigure(row_frame, c, weight=1)

    def select_piece(self, r, c):
        if self.start:
            if self.finish:
                self.start = []
                self.finish = []
            self.finish = [self._game._SIZE - r - 1, c]
            self._display_board()
        else:
            self.start = [self._game._SIZE - r - 1, c]
            self._change_sprite_size(r, c)

    def _change_sprite_size(self, r, c):
        piece = self._game._board[self._game._SIZE - r - 1][c]
        if piece == self._game._EMPTY:
            image_name = "None"
        else:
            image_name = f"{piece.__class__.__name__} - {['White', 'Black'][self._game._players.index(piece._player)]} - Big"
        button = self._pos_buttons[r][c]
        img = self._root.sprites[image_name]
        button.configure(image=img)

    def _display_board(self):
        for r in range(self._game._SIZE):
            for c in range(self._game._SIZE):
                piece = self._game._board[self._game._SIZE - r - 1][c]
                if piece == self._game._EMPTY:
                    image_name = "None"
                else:
                    image_name = f"{piece.__class__.__name__} - {['White', 'Black'][self._game._players.index(piece._player)]} - Normal"
                button = self._pos_buttons[r][c]
                button.configure(image=self._root.sprites[image_name])

    def _get_move(self):
        while True:
            if self.start and self.finish:
                break
            else:
                time.sleep(0.1)
        x = [[chr(self.start[1] + 97), self.start[0] + 1], [chr(self.finish[1] + 97), self.finish[0] + 1]]
        self.start = []
        self.finish = []
        return x

    def _get_settings(self):
        return [False, True]

    def _get_draw_decision(self, player):
        return True


class Terminal(UI):
    def __init__(self, game):
        super().__init__(game)

    def _display_board(self):
        os.system("cls")
        board = self._game._board
        x = "  "
        for i in range(len(board)):
            x += chr(65 + i) + " "
        x += "\n"
        for i, row in enumerate(board[::-1]):
            y = ""
            for element in row:
                if element == self._game._EMPTY:
                    y += element + " "
                else:
                    y += element._symbol + " "
            x += str(len(board) - i) + " " + y +str(len(board) - i) + "\n"
        x += "  "
        for i in range(len(board)):
            x += chr(65 + i) + " "
        x += "\n"
        print(x)

    def _get_move(self):
        return input("Enter your move, old position then new position: ").split(" ")

    def _get_settings(self):
        s = []
        for i in range(2):
            x = ""
            while x not in ["Y", "N"]:
                x = input(f"Is {['White', 'Black'][i]} an AI? (Y/N): ").upper()
            s.append(x == "Y")
        return s

    def _get_draw_decision(self, player):
        x = ""
        while x not in ['Y', 'N']:
            x = input(f"{['White', 'Black'][player]}, would you like to draw? (Y/N): ").upper()
        return x == "Y"


if __name__ == "__main__":
    print("This file just contains the UI classes")
    #usage()
