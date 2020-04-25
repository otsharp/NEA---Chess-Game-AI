from abc import ABC, abstractmethod
#from Chess import usage


class UI(ABC):
    def __init__(self, game):
        self._game = game

    @abstractmethod
    def _display_board(self):
        raise NotImplementedError

    @abstractmethod
    def _get_move(self):
        return None


class GUI(UI):
    def __init__(self, game):
        super().__init__(game)

    def _display_board(self):
        pass

    def _get_move(self):
        return None


class Terminal(UI):
    def __init__(self, game):
        super().__init__(game)

    def _display_board(self):
        board = self._game._board
        x = "  "
        for i in range(len(board)):
            x += chr(65 + i) + " "
        x += "\n"
        for i, row in enumerate(board):
            y = ""
            for element in row:
                y += element + " "
            x += str(len(board) - i) + " " + y + "\n"
        print(x)

    def _get_move(self):
        return None


if __name__ == "__main__":
    print("This file just contains the UI classes")
    #usage()
