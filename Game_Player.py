from Pieces import Piece


class Game:
    def __init__(self, UItype):
        self._EMPTY = "_"
        self._SIZE = 8
        self.__UI = UItype(self)
        self._board = self.__reset_board()
        self.__players = [Player(self), Player(self)]
        self.__toPlay = 0
        self.__settings = self.__get_settings()

    def __get_settings(self):
        return None

    def __reset_board(self):  # only return empty board currently
        return [[self._EMPTY for _ in range(self._SIZE)] for _ in range(self._SIZE)]

    def __do_turn(self):
        pass

    def play_game(self):
        pass

    def __display_board(self):
        self.__UI._display_board()

    def __is_move_legal(self, move):
        return None


class Player:
    def __init__(self, game):
        self.__pieces = []
        self.__game = game

    def _avail_moves(self):
        moves = []
        for piece in self.__pieces:
            moves.append(piece._avail_moves())
        return moves


if __name__ == "__main__":
    print("This file just contains the Game and Player classes")
    #usage()
