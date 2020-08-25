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
    def _get_move(self, moves):
        raise NotImplementedError

    @abstractmethod
    def _get_settings(self):
        raise NotImplementedError

    @abstractmethod
    def _get_draw_decision(self, player):
        raise NotImplementedError

    @abstractmethod
    def _notify(self, message):
        raise NotImplementedError

    @abstractmethod
    def _end(self):
        raise NotImplementedError


class GUI(UI):
    def __init__(self, game):
        super().__init__(game)
        self._root = t_tk.ThemedTk()
        self._root.title("Chess")
        self._size = 1000
        self._win_size = 80
        self._black_square = "#B88658"
        self._white_sqaure = "#F0D2AD"
        self._green_square = "#8AE678"
        self._prom_choice = None
        self._sprite_normal_percent = 65 / 100
        self._sprite_big_percent = 85 / 100
        self._root.geometry(f"{self._size}x{self._size}")
        self._accept_settings = False
        self._settings_choice = [False, False, True]
        self._text_vars = {}
        self._text_vars["settings white"] = tk.StringVar()
        self._text_vars["settings white"].set("White: Player")
        self._text_vars["settings black"] = tk.StringVar()
        self._text_vars["settings black"].set("Black: Player")
        self._text_vars["settings flip"] = tk.StringVar()
        self._text_vars["settings flip"].set("Flip?: Yes")
        self._text_vars["to play"] = tk.StringVar()
        self._text_vars["to play"].set("White to play")

        self.start = []
        self.finish = []

        self._pos_buttons = []
        self._root.sprites = {}
        self._root.sprites["None"] = ImageTk.PhotoImage(Image.open("Sprites/None.png"))
        for orientation in ['Normal', 'Flipped']:
            for colour in ["White", "Black"]:
                for piece in ["Rook", "Knight", "Bishop", "Queen", "King", "Pawn"]:
                    for i in range(3):
                        s = [self._sprite_normal_percent, self._sprite_big_percent, self._win_size / (self._size / (8 + 0)) * self._sprite_big_percent][i]
                        s1 = (int(self._size / (self._game._SIZE + 0) * s))
                        self._root.sprites[f"{piece} - {colour} - {['Normal', 'Big', 'Prom'][i]} - {orientation}"] = ImageTk.PhotoImage([Image.open(f"Sprites/{piece} - {colour}.png").resize((s1, s1), Image.ANTIALIAS), Image.open(f"Sprites/{piece} - {colour}.png").resize((s1, s1), Image.ANTIALIAS).transpose(Image.FLIP_TOP_BOTTOM)][orientation == "Flipped"])

        self._board_frame = tk.Frame(self._root)
        self._board_frame.grid(row=0, column=0, sticky="nesw")
        tk.Grid.rowconfigure(self._root, 0, weight=1)
        tk.Grid.columnconfigure(self._root, 0, weight=1)

        tk.Grid.columnconfigure(self._board_frame, 0, weight=1)
        for r in range(self._game._SIZE):
            row_frame = tk.Frame(self._board_frame)
            row_frame.grid(row=r, column=0, sticky="nesw")
            tk.Grid.rowconfigure(self._board_frame, r, weight=5)
            tk.Grid.rowconfigure(row_frame, 0, weight=1)
            self._pos_buttons.append([])
            for c in range(self._game._SIZE):
                image = ""
                button = tk.Button(row_frame, image=image, bg=[self._black_square, self._white_sqaure][(r + c + 1) % 2], height=1, width=1, relief="flat", command=partial(self.select_piece, r, c))
                self._pos_buttons[r].append(button)
                button.grid(row=0, column=c, sticky="nesw")
                tk.Grid.columnconfigure(row_frame, c, weight=1)

        self._get_settings()

        if not self._settings_choice[2]:
            turn_label = tk.Label(self._board_frame, textvariable=self._text_vars["to play"])
            turn_label.grid(row=9, column=0, sticky="nesw")
            tk.Grid.rowconfigure(self._board_frame, 9, weight=1)

    def select_piece(self, r, c):
        if self.start:
            if self.finish:
                self.start = []
                self.finish = []
            self.finish = [self._game._SIZE - r - 1, c]
            self._display_board()
        else:
            #print(self._game._board[r][c])
            #if self._game._board[r][c] != self._game._EMPTY:
            self.start = [self._game._SIZE - r - 1, c]
            self._change_sprite_size(r, c)
            #self._pos_buttons[r][c].configure(bg="green")

    def _change_sprite_size(self, r, c):
        piece = self._game._board[self._game._SIZE - r - 1][c]
        if piece == self._game._EMPTY:
            image_name = "None"
        else:
            image_name = f"{piece.__class__.__name__} - {['White', 'Black'][self._game._players.index(piece._player)]} - Big - {['Normal', 'Flipped'][self._game._settings[2] and self._game._toPlay == 1]}"
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
                    image_name = f"{piece.__class__.__name__} - {['White', 'Black'][self._game._players.index(piece._player)]} - Normal - {['Normal', 'Flipped'][self._game._settings[2] and self._game._toPlay == 1]}"
                button = self._pos_buttons[r][c]
                button.configure(image=self._root.sprites[image_name], bg=[self._black_square, self._white_sqaure][(r + c + 1) % 2])

    def _get_move(self, moves):
        while True:
            if self.start and self.finish:
                break
            else:
                time.sleep(0.1)
        x = [[chr(self.start[1] + 97), self.start[0] + 1], [chr(self.finish[1] + 97), self.finish[0] + 1]]
        if [self.start, self.finish] in [[m[0], m[1][:2]] for m in moves]:
            i = [[m[0], m[1][:2]] for m in moves].index([self.start, self.finish])
            if len(moves[i][1]) == 3:
                x.append(self._get_prom_choice())
        self.start = []
        self.finish = []
        return x

    def __set_prom_choice(self, choice):
        self._prom_choice = choice

    def _get_prom_choice(self):
        win = tk.Toplevel()
        win.overrideredirect(True)
        win.grab_set()
        win.attributes("-topmost", True)
        win.title("Promotion choice")
        win.geometry(f"{self._win_size}x{4*self._win_size}")
        frame = tk.Frame(win)
        frame.grid(row=0, column=0, sticky="nesw")
        tk.Grid.rowconfigure(win, 0, weight=1)
        tk.Grid.columnconfigure(win, 0, weight=1)
        tk.Grid.columnconfigure(frame, 0, weight=1)
        for i in range(4):
            button = tk.Button(
                frame, height=self._win_size, width=self._win_size,
                image=self._root.sprites[f"{['Queen', 'Rook', 'Bishop', 'Knight'][i]} - {['White', 'Black'][self._game._toPlay]} - Prom - {['Normal', 'Flipped'][self._game._settings[2] and self._game._toPlay == 1]}"], command=partial(self.__set_prom_choice, ['Q', 'R', 'B', 'K'][i]))
            button.grid(row=i, column=0, sticky="nesw")
            tk.Grid.rowconfigure(frame, i, weight=1)
        while self._prom_choice is None:
            time.sleep(0.1)
        choice = self._prom_choice
        self._prom_choice = None
        win.grab_release()
        win.destroy()
        return choice

    def __flip_setting(self, i):
        self._settings_choice[i] = not self._settings_choice[i]
        if 0 <= i <= 1:
            self._text_vars[f"settings {['white', 'black'][i]}"].set(f"{['White', 'Black'][i]}: {['Player', 'AI'][self._settings_choice[i]]}")
        elif i == 2:
            self._text_vars["settings flip"].set(f"Flip?: {['No', 'Yes'][self._settings_choice[i]]}")
        else:
            print("Flip setting error")
            quit()

    def __settings_okay(self, win):
        self._accept_settings = True
        win.grab_release()
        win.destroy()
        self._root.quit()

    def _get_settings(self):
        win = tk.Toplevel()
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.title("Player choice")
        win.grab_set()
        num_options = 3
        win.geometry(f"{2 * self._win_size}x{int((num_options * self._win_size) + (self._win_size * 1/3))}")
        frame = tk.Frame(win)
        frame.grid(row=0, column=0, sticky="nesw")
        tk.Grid.rowconfigure(win, 0, weight=1)
        tk.Grid.columnconfigure(win, 0, weight=1)
        tk.Grid.columnconfigure(frame, 0, weight=1)
        for i in range(2):
            button = tk.Button(
                frame, relief="flat", height=self._win_size, width=2*self._win_size, textvariable=self._text_vars[f"settings {['white', 'black'][i]}"], command=partial(self.__flip_setting, i))
            button.grid(row=i, column=0, sticky="nesw")
            tk.Grid.rowconfigure(frame, i, weight=3)
        button1 = tk.Button(frame, relief="flat", height=self._win_size, width=2*self._win_size, textvariable=self._text_vars["settings flip"], command=partial(self.__flip_setting, 2))
        button1.grid(row=2, column=0, sticky="nesw")
        tk.Grid.rowconfigure(frame, 2, weight=3)
        okay_button = tk.Button(frame, height=int(self._win_size / 3), width=2*self._win_size, text="Done", command=partial(self.__settings_okay, win))
        okay_button.grid(row=num_options, column=0, sticky="nesw")
        tk.Grid.rowconfigure(frame, num_options, weight=1)
        win.mainloop()
        return self._settings_choice

    def __popup(self, message):
        pad_y_size = 5
        pad_inbetween_size = 5
        pad_x_size = 20
        self.__popup_done_var = False
        win = tk.Toplevel()
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.grab_set()
        #win.geometry(f"{2 * self._win_size}x{int(self._win_size + (self._win_size * 1 / 3))}")
        frame = tk.Frame(win)
        frame.grid(row=0, column=0, sticky="nesw")
        tk.Grid.rowconfigure(win, 0, weight=1)
        tk.Grid.columnconfigure(win, 0, weight=1)
        tk.Grid.columnconfigure(frame, 0, weight=1)
        label = tk.Label(frame, text=message)  # height=self._win_size, width=2*self._win_size,
        label.grid(row=0, column=0, sticky="nesw", padx=(0, 0), pady=(pad_y_size, pad_inbetween_size))
        tk.Grid.rowconfigure(frame, 0, weight=3)
        okay_button = tk.Button(frame, text="Done", command=partial(self.__popup_done))  # height=int(self._win_size / 3), width=2 * self._win_size,
        okay_button.grid(row=1, column=0, sticky="nesw", padx=(pad_x_size, pad_x_size), pady=(pad_inbetween_size, 0))
        tk.Grid.rowconfigure(frame, 1, weight=1)
        while not self.__popup_done_var:
            time.sleep(0.1)
        win.grab_release()
        win.destroy()

    def __popup_done(self):
        self.__popup_done_var = True

    def _notify(self, message):
        self.__popup(message)

    def _get_draw_decision(self, player):
        self._draw_dec = None
        if self._game._players[player].__class__.__name__ == "AI":
            return False
        win = tk.Toplevel()
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.grab_set()
        frame = tk.Frame(win)
        frame.grid(row=0, column=0, sticky="nesw")
        tk.Grid.rowconfigure(win, 0, weight=1)
        tk.Grid.columnconfigure(win, 0, weight=1)
        label = tk.Label(frame, text=f"{['White', 'Black'][player]}, would you like to draw?")
        label.grid(row=0, column=0, sticky="nesw")
        yes_button = tk.Button(frame, text="Yes", command=partial(self._draw_decider, True))
        yes_button.grid(row=1, column=0, sticky="nesw")
        no_button = tk.Button(frame, text="No", command=partial(self._draw_decider, False))
        no_button.grid(row=2, column=0, sticky="nesw")

        tk.Grid.rowconfigure(frame, 0, weight=1)
        tk.Grid.rowconfigure(frame, 1, weight=1)
        tk.Grid.rowconfigure(frame, 2, weight=1)
        tk.Grid.columnconfigure(frame, 0, weight=1)

        while self._draw_dec is None:
            time.sleep(0.1)
        win.grab_release()
        win.destroy()
        return self._draw_dec

    def _draw_decider(self, val):
        self._draw_dec = val

    def _end(self):
        self._root.destroy()


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

    def _get_move(self, moves):
        return input("Enter your move, old position then new position: ").split(" ")

    def _get_settings(self):
        s = []
        for i in range(2):
            x = ""
            while x not in ["Y", "N"]:
                x = input(f"Is {['White', 'Black'][i]} an AI? (Y/N): ").upper()
            s.append(x == "Y")
        s.append(False)  # flip
        return s

    def _notify(self, message):
        print(message)

    def _get_draw_decision(self, player):
        x = ""
        while x not in ['Y', 'N']:
            x = input(f"{['White', 'Black'][player]}, would you like to draw? (Y/N): ").upper()
        return x == "Y"

    def _end(self):
        pass


if __name__ == "__main__":
    print("This file just contains the UI classes")
    #usage()
