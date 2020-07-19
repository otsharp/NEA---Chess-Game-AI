from Pieces import *
import os
from copy import deepcopy
import time


class Game:
    def __init__(self, UItype):
        self._EMPTY = "_"
        self._SIZE = 8
        self.__UI = UItype(self)
        self.__settings = self.__get_settings()
        self._undo_stack = []
        if self.__settings[0] == "Y":
            self._players = [Player(self), AI(self)]
            if self.__settings[1] == "Y":
                selfself._toPlay = 0
            else:
                selfself._toPlay = 1
        else:
            self._players = [Player(self), Player(self)]
            self._toPlay = 0
        self._board = self.__reset_board()
        for player in self._players:
            player._2nd_init()

    def __get_settings(self):
        return self.__UI._get_settings()

    def __reset_board(self):
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

    def __is_over(self, p_moves):
        return self._players[self._toPlay]._in_checkmate(p_moves) or self._players[self._toPlay]._in_stalemate(p_moves) or self._players[1 - self._toPlay]._in_checkmate() or self._players[1 - self._toPlay]._in_stalemate()

    def _make_move(self, move):
        piece = self._board[move[0][0]][move[0][1]]
        new = self._board[move[1][0]][move[1][1]]
        if type(new) != str:
            self._undo_stack.append([piece, piece._pos, new, new._taken])
            new._taken = True
        else:
            self._undo_stack.append([piece, piece._pos, None, None])
        self._board[move[0][0]][move[0][1]] = self._EMPTY
        piece._pos = move[1]
        self._board[move[1][0]][move[1][1]] = piece
        self._toPlay = (self._toPlay + 1) % 2

    def _undo_move(self):
        b = [[self._EMPTY for _ in range(self._SIZE)] for _ in range(self._SIZE)]
        piece, piece_dest, old, taken = self._undo_stack.pop()
        piece._pos = piece_dest
        if old is not None:
            old._taken = False
        for i in range(2):
            for piece in self._players[i]._pieces:
                if not piece._taken:
                    b[piece._pos[0]][piece._pos[1]] = piece
        self._board = b
        self._toPlay = (self._toPlay + 1) % 2

    def __do_turn(self, moves):
        move = input("Enter your move, old position then new position: ")
        if move == "undo":
            self._undo_move()
            os.system("cls")
            self._display_board()
            self.__do_turn(moves)
            return
        move = move.split(" ")
        move1 = []
        for pos in move:
            try:
                move1.append([int(pos[1]) - 1, ord(pos[0].lower()) - 97])
            except (ValueError, IndexError):
                self.__do_turn(moves)
                return
        for pos in move1:
            for coord in pos:
                if coord > 7 or coord < 0:
                    self.__do_turn(moves)
                    return
        if move1 not in moves:
            self.__do_turn(moves)
            return
        self._make_move(move1)

    def play_game(self):
        os.system("cls")
        self._display_board()
        print("White to play")
        while True:
            p_moves = self._players[self._toPlay]._avail_moves()
            if self.__is_over(p_moves):
                break
            self.__do_turn(p_moves)
            os.system("cls")
            self._display_board()
            print(f"{['White', 'Black'][self._toPlay]} to play")

    def _display_board(self):
        self.__UI._display_board()

    def __is_move_legal(self, move):
        return move in self._players[self._toPlay]._avail_moves()


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

    def _avail_moves(self, careifcheck=True):
        moves = []
        for piece in self._pieces:
            p_moves = piece._avail_moves(careifcheck)
            for move in p_moves:
                moves.append([piece._pos, move])
        return moves

    def _in_check(self):
        return self._pieces[[p.__class__.__name__ for p in self._pieces].index("King")]._pos in [m[1] for m in self._game._players[1 - self._game._players.index(self)]._avail_moves(False)]

    def _in_checkmate(self, p_moves=[]):
        if not p_moves:
            p_moves = self._avail_moves()
        return p_moves == [] and self._in_check()

    def _in_stalemate(self, p_moves=[]):
        if not p_moves:
            p_moves = self._avail_moves()
        return p_moves == [] and not self._in_check()


if __name__ == "__main__":
    print("This file just contains the Game and Player classes")
    #usage()
