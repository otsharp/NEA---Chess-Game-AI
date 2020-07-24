from Pieces import *
import os
from copy import deepcopy
import time
import random
from statistics import mean


class Game:
    def __init__(self, UItype):
        self._EMPTY = "_"
        self._SIZE = 8
        self._UI = UItype(self)
        self.__settings = self.__get_settings()
        self._undo_stack = []
        if self.__settings[0] == "Y":
            self._players = [Player(self), AI(self)]
            if self.__settings[1] == "Y":
                self._toPlay = 0
            else:
                self._toPlay = 1
        else:
            self._players = [Player(self), Player(self)]
            self._toPlay = 0
        self._board = self.__reset_board()
        for player in self._players:
            player._2nd_init()

    def __get_settings(self):
        return self._UI._get_settings()

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

    def _is_draw(self, p_moves):
        player1_cant_move = p_moves == [] and not self._players[self._toPlay]._in_check()
        player2_cant_move = (self._players[1 - self._toPlay]._avail_moves() == [] and not self._players[1 - self._toPlay]._in_check())
        only_kings = all([p.__class__.__name__ == "King" for p in self._players[0]._pieces if p._taken == False]) and all([p.__class__.__name__ == "King" for p in self._players[1]._pieces if p._taken == False])
        return any([player1_cant_move, player2_cant_move, only_kings])

    def __is_over(self, p_moves):
        return self._players[self._toPlay]._in_checkmate(p_moves) or self._players[1 - self._toPlay]._in_checkmate() or self._is_draw(p_moves)

    def _make_move(self, move):
        piece = self._board[move[0][0]][move[0][1]]
        if piece.__class__.__name__ == "Pawn":
            x = deepcopy(piece._just_double)
        else:
            x = None
        if len(move[1]) == 3:  # promotion
            new = self._board[move[1][0]][move[1][1]]
            if type(new) != str:
                n = deepcopy(new._taken)
                new._taken = True
                h = new
            else:
                n = None
                h = None
            p = deepcopy(piece._pos)
            piece._pos = move[1][:2]
            self._board[move[1][0]][move[1][1]] = piece
            piece._taken = True
            prom = [Bishop, Knight, Rook, Queen][['B', 'K', 'R', 'Q'].index(move[1][2].upper())](move[1][:2], self._players[self._toPlay], self)
            self._players[self._toPlay]._pieces.append(prom)
            self._undo_stack.append([piece, p, h, n, x, prom])
            self._board[move[0][0]][move[0][1]] = self._EMPTY
            self._board[move[1][0]][move[1][1]] = prom
        else:
            if type(piece) == str:
                print(piece)
                print(move[0])
            new = self._board[move[1][0]][move[1][1]]
            y = False
            if type(new) == str and piece.__class__.__name__ == "Pawn":
                if move[1][1] != piece._pos[1]:
                    y = True
            if type(new) != str:
                self._undo_stack.append([piece, deepcopy(piece._pos), new, deepcopy(new._taken), x, None])
                new._taken = True
            else:
                if y:
                    t = self._board[move[1][0] - piece._dir[0]][move[1][1]]
                    t._taken = True
                    self._board[move[1][0] - piece._dir[0]][move[1][1]] = self._EMPTY
                    self._undo_stack.append([piece, deepcopy(piece._pos), t, deepcopy(t._taken), x, None])
                else:
                    self._undo_stack.append([piece, deepcopy(piece._pos), None, None, x, None])
            for p in piece._player._pieces:
                if p.__class__.__name__ == "Pawn":
                    p._just_double = False
            if piece.__class__.__name__ == "Pawn":
                if abs(piece._pos[0] - move[1][0]) == 2:
                    piece._just_double = True
            self._board[move[0][0]][move[0][1]] = self._EMPTY
            self._board[move[1][0]][move[1][1]] = piece
            piece._pos = move[1][:2]
        self._toPlay = (self._toPlay + 1) % 2

    def _undo_move(self):
        b = [[self._EMPTY for _ in range(self._SIZE)] for _ in range(self._SIZE)]
        piece, piece_dest, old, taken, double, prom = self._undo_stack.pop()
        if prom is not None:
            piece._taken = False
            self._players[1 - self._toPlay]._pieces.remove(prom)
        piece._pos = piece_dest
        if piece.__class__.__name__ == "Pawn":
            piece._just_double = double
        if old is not None:
            old._taken = False
        for i in range(2):
            for piece in self._players[i]._pieces:
                if not piece._taken:
                    b[piece._pos[0]][piece._pos[1]] = piece
        self._board = b
        self._toPlay = (self._toPlay + 1) % 2

    def __do_turn(self, moves):
        move = self._players[self._toPlay]._get_move(moves)
        if move == "undo":
            self._undo_move()
            self._display_board()
            self.__do_turn(moves)
            return
        self._make_move(move)

    def play_game(self):
        times = []
        self._display_board()
        print("White to play")
        while True:
            t0 = time.time()
            p_moves = self._players[self._toPlay]._avail_moves()
            if self.__is_over(p_moves):
                break
            self.__do_turn(p_moves)
            self._display_board()
            print(f"{['White', 'Black'][self._toPlay]} to play")
            times.append(time.time() - t0)
            print(f"Curr.: {round(time.time() - t0, 3)}s\nAvg.: {round(mean(times), 3)}s\nTot.: {round(sum(times), 3)}s")
        if self._is_draw(p_moves):
            print("Draw")
        else:
            print(f"{['White', 'Black'][1 - self._toPlay]} wins")

    def _display_board(self):
        self._UI._display_board()

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

    def _get_move(self, moves):
        move = self._game._UI._get_move()
        move1 = []
        for pos in move[:2]:
            try:
                move1.append([int(pos[1]) - 1, ord(pos[0].lower()) - 97])
            except (ValueError, IndexError) as e:
                print("Value / Index Error", e)
                return self._get_move(moves)
        for pos in move1:
            for coord in pos:
                if coord > 7 or coord < 0:
                    print("Out of bounds")
                    return self._get_move(moves)
        if len(move) == 3:
            move1[1].append(move[2].upper())
        if move1 not in moves:
            print("Not valid move")
            return self._get_move(moves)
        return move1

    def _in_check(self):
        return self._pieces[[p.__class__.__name__ for p in self._pieces].index("King")]._pos in [m[1][:2] for m in self._game._players[1 - self._game._players.index(self)]._avail_moves(False)]

    def _in_checkmate(self, p_moves=[]):
        if not p_moves:
            p_moves = self._avail_moves()
        return p_moves == [] and self._in_check()


class AI(Player):
    def __init__(self, game):
        super().__init__(game)

    def _get_move(self, moves):
        print(moves)
        return random.choice(moves)

    def _get_prom_choice(self):
        return 3


if __name__ == "__main__":
    print("This file just contains the Game and Player classes")
    #usage()
