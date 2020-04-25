from abc import ABC, abstractmethod
#from Chess import usage

symbols = {"Kw": "♔"}  # etc.


class Piece(ABC):
    def __init__(self, pos, piece_type, player):
        self.__player = player
        self.__pos = pos
        self.__symbol = symbols[piece_type]

    def _avail_moves(self):
        return None


if __name__ == "__main__":
    print("This file just contains the Piece classes")
    #usage()
