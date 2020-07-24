from abc import ABC, abstractmethod
import os
#from Chess import usage


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


class GUI(UI):
    def __init__(self, game):
        super().__init__(game)

    def _display_board(self):
        pass

    def _get_move(self):
        return None

    def _get_settings(self):
        return ["N"]


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
        x = ""
        while x not in ["Y", "N"]:
            x = input("Do you want to play an AI? (Y/N): ").upper()
        s.append(x)
        if x == "Y":
            y = ""
            while y not in ["Y", "N"]:
                y = input("Do you want to go first? (Y/N): ").upper()
        else:
            y = None
        s.append(y)
        return s


if __name__ == "__main__":
    print("This file just contains the UI classes")
    #usage()
