from Pieces import *


class Game:
    def __init__(self, UItype):
        self._EMPTY = "_"
        self._SIZE = 8
        self.__UI = UItype(self)
        self._players = [Player(self), Player(self)]
        self.__toPlay = 0
        self._board = self.__reset_board()
        self.__settings = self.__get_settings()
        for player in self._players:
            player._2nd_init()

    def __get_settings(self):
        return None

    def __reset_board(self):  # only return empty board currently
        b = [[self._EMPTY for _ in range(self._SIZE)] for _ in range(self._SIZE)]
        b[0] = [
            Rook([0, 0], self._players[0], self),
            Knight([0, 1], self._players[0], self),
            Bishop([0, 2], self._players[0], self),
            Queen([0, 3], self._players[0], self),
            King([0, 4], self._players[0], self),
            Bishop([0, 5], self._players[0], self),
            Knight([0, 6], self._players[0], self),
            Rook([0, 7], self._players[0], self),
        ]
        b[1] = [
            Pawn([1, 0], self._players[0], self),
            Pawn([1, 1], self._players[0], self),
            Pawn([1, 2], self._players[0], self),
            Pawn([1, 3], self._players[0], self),
            Pawn([1, 4], self._players[0], self),
            Pawn([1, 5], self._players[0], self),
            Pawn([1, 6], self._players[0], self),
            Pawn([1, 7], self._players[0], self),
        ]

        b[7] = [
            Rook([7, 0], self._players[1], self),
            Knight([7, 1], self._players[1], self),
            Bishop([7, 2], self._players[1], self),
            Queen([7, 3], self._players[1], self),
            King([7, 4], self._players[1], self),
            Bishop([7, 5], self._players[1], self),
            Knight([7, 6], self._players[1], self),
            Rook([7, 7], self._players[1], self),
        ]
        b[6] = [
            Pawn([6, 0], self._players[1], self),
            Pawn([6, 1], self._players[1], self),
            Pawn([6, 2], self._players[1], self),
            Pawn([6, 3], self._players[1], self),
            Pawn([6, 4], self._players[1], self),
            Pawn([6, 5], self._players[1], self),
            Pawn([6, 6], self._players[1], self),
            Pawn([6, 7], self._players[1], self),
        ]
        return b

    def __do_turn(self):
        pass

    def play_game(self):
        pass

    def _display_board(self):
        self.__UI._display_board()

    def __is_move_legal(self, move):
        return None


class Player:
    def __init__(self, game):
        self._pieces = []
        self._game = game


    def _2nd_init(self):
        for row in self._game._board:
            for p in row:
                if p != self._game._EMPTY:
                    if p._player == self:
                        self._pieces.append(p)

    def _avail_moves(self):
        moves = []
        for piece in self._pieces:
            p_moves = piece._avail_moves()
            for move in p_moves:
                moves.append([piece._pos, move])
        return moves


if __name__ == "__main__":
    print("This file just contains the Game and Player classes")
    #usage()
