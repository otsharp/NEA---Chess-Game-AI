from abc import ABC, abstractmethod
#from Chess import usage

symbols = {"Rw": "♜", "Nw": "♞", "Bw": "♝", "Kw": "♚", "Qw": "♛", "Pw": "♟",
           "Rb": "♖", "Nb": "♘", "Bb": "♗", "Kb": "♔", "Qb": "♕", "Pb": "♙"}


class Piece(ABC):
    def __init__(self, pos, player, game):
        self._player = player
        self._pos = pos
        self._game = game
        #self._dirs = []
        #self._max_dis = -1

    def _avail_moves(self):
        moves = []
        for dir in self._dirs:
            i = 1
            while i < self._max_dis and -1 < self._pos[0] + dir[0] * i < self._game._SIZE and -1 < self._pos[1] + dir[
                1] * i < self._game._SIZE and (
                    self._game._board[self._pos[0] + dir[0] * i][self._pos[1] + dir[1] * i] == self._game._EMPTY or
                    self._game._board[self._pos[0] + dir[0] * i][self._pos[1] + dir[1] * i]._player != self._player):
                moves.append([self._pos[0] + dir[0] * i, self._pos[1] + dir[1] * i])
                if self._game._board[self._pos[0] + dir[0] * i][self._pos[1] + dir[1] * i] != self._game._EMPTY:
                    break
                i += 1
        return moves


class Rook(Piece):
    def __init__(self, pos, player, game):
        super().__init__(pos, player, game)
        if self._player == self._game._players[0]:
            self._symbol = symbols["Rw"]
        else:
            self._symbol = symbols["Rb"]
        self._dirs = [[0, 1], [0, -1], [1, 0], [-1, 0]]
        self._max_dis = 999


class Knight(Piece):
    def __init__(self, pos, player, game):
        super().__init__(pos, player, game)
        if self._player == self._game._players[0]:
            self._symbol = symbols["Kw"]
        else:
            self._symbol = symbols["Kb"]
        self._dirs = [[1, 2], [1, -2], [-1, 2], [-1, -2], [2, 1], [2, -1], [-2, 1], [-2, -1]]
        self._max_dis = 2


class Bishop(Piece):
    def __init__(self, pos, player, game):
        super().__init__(pos, player, game)
        if self._player == self._game._players[0]:
            self._symbol = symbols["Bw"]
        else:
            self._symbol = symbols["Bb"]
        self._dirs = [[1, 1], [-1, -1], [1, -1], [-1, 1]]
        self._max_dis = 999


class King(Piece):
    def __init__(self, pos, player, game):
        super().__init__(pos, player, game)
        if self._player == self._game._players[0]:
            self._symbol = symbols["Kw"]
        else:
            self._symbol = symbols["Kb"]
        self._dirs = [[1, 1], [-1, -1], [1, -1], [-1, 1], [0, 1], [0, -1], [1, 0], [-1, 0]]
        self._max_dis = 2


class Queen(Piece):
    def __init__(self, pos, player, game):
        super().__init__(pos, player, game)
        if self._player == self._game._players[0]:
            self._symbol = symbols["Qw"]
        else:
            self._symbol = symbols["Qb"]
        self._dirs = [[1, 1], [-1, -1], [1, -1], [-1, 1], [0, 1], [0, -1], [1, 0], [-1, 0]]
        self._max_dis = 999


class Pawn(Piece):
    def __init__(self, pos, player, game):
        super().__init__(pos, player, game)
        if self._player == self._game._players[0]:
            self._symbol = symbols["Pw"]
            self._dirs = [[1, 0]]
        else:
            self._symbol = symbols["Pb"]
            self._dirs = [[-1, 0]]
        self._max_dis = 2


if __name__ == "__main__":
    print("This file just contains the Piece classes")
    #usage()
