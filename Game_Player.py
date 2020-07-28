from Pieces import *
import os
from copy import deepcopy
import time
import random
from statistics import mean
from collections import Counter


class StringList(object):

    def __init__(self, val):
        self.val = val

    def __hash__(self):
        return hash(str(self.val))

    def __repr__(self):
        return str(self.val)

    def __eq__(self, other):
        return str(self.val) == str(other.val)


class Game:
    def __init__(self, UItype):
        self._EMPTY = "_"
        self._SIZE = 8
        self._UI = UItype(self)
        self.__settings = self.__get_settings()
        self._undo_stack = []
        self._played = []
        self._mutual = False
        self._repetitions = []
        self._move_count = 0
        self._toPlay = 0
        self._players = [[Player, AI][self.__settings[0]](self), [Player, AI][self.__settings[1]](self)]
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
        stalemate = p_moves == [] and not self._players[self._toPlay]._in_check() or (self._players[1 - self._toPlay]._avail_moves() == [] and not self._players[1 - self._toPlay]._in_check())

        player1_pieces = sorted([p.__class__.__name__ for p in self._players[0]._pieces if p._taken == False])
        player2_pieces = sorted([p.__class__.__name__ for p in self._players[1]._pieces if p._taken == False])
        pieces = sorted([player1_pieces, player2_pieces], key=len)
        impossibility = pieces in [[["King"], ["King"]], [["King"], ["Bishop", "King"]], [["King"], ["King", "Knight"]]]
        if pieces == [["Bishop", "King"], ["Bishop", "King"]]:
            if [p._colour for p in self._players[0]._pieces if (p._taken == False and p.__class__.__name__ == "Bishop")][0] != [p._colour for p in self._players[1]._pieces if (p._taken == False and p.__class__.__name__ == "Bishop")][0]:
                impossibility = True

        c = Counter(self._repetitions)
        x = max(c.values())
        repetition = False
        if x >= 5:
            repetition = True
        elif x >= 3:
            if self._UI._get_draw_decision(self._toPlay):
                repetition = self._UI._get_draw_decision(1 - self._toPlay)
        move_limit = False
        if self._move_count >= 75:
            move_limit = True
        elif self._move_count >= 50:
            if self._UI._get_draw_decision(self._toPlay):
                move_limit = self._UI._get_draw_decision(1 - self._toPlay)
        agreement = self._mutual
        return stalemate or impossibility or repetition or move_limit or agreement

    def __is_over(self, p_moves):
        if self._players[self._toPlay]._in_checkmate(p_moves):
            return f"{['White', 'Black'][1 - self._toPlay]} wins"
        if self._players[1 - self._toPlay]._in_checkmate(p_moves):
            return f"{['White', 'Black'][self._toPlay]} wins"
        if  self._is_draw(p_moves):
            return "Draw"
        return None

    def _make_move(self, move):
        mc = deepcopy(self._move_count)
        self._played.append([[chr(move[0][1] + 97), move[0][0]+1], [chr(move[1][1] + 97), move[1][0]+1]])
        piece = self._board[move[0][0]][move[0][1]]
        if piece.__class__.__name__ == "Pawn":
            x = deepcopy(piece._just_double)
            self._move_count = -1
        else:
            x = None
        if piece.__class__.__name__ == "King" and abs(move[0][1] - move[1][1]) == 2:  # castling
            king = self._board[move[0][0]][move[0][1]]
            if move[1][1] > move[0][1]:
                rook = self._board[move[0][0]][7]
            else:
                rook = self._board[move[0][0]][0]
            self._undo_stack.append([king, deepcopy(king._pos), None, None, None, None, False, rook, mc])
            self._board[king._pos[0]][king._pos[1]] = self._EMPTY
            self._board[rook._pos[0]][rook._pos[1]] = self._EMPTY
            king._pos = move[1]
            rook._pos = [move[1][0], move[1][1] + [1, -1][move[1][1] > move[0][1]]]
            self._board[king._pos[0]][king._pos[1]] = king
            self._board[rook._pos[0]][rook._pos[1]] = rook
            king._moved = True
            rook._moved = True
        else:
            if len(move[1]) == 3:  # promotion
                new = self._board[move[1][0]][move[1][1]]
                if type(new) != str:
                    n = deepcopy(new._taken)
                    new._taken = True
                    self._move_count = -1
                    h = new
                else:
                    n = None
                    h = None
                p = deepcopy(piece._pos)
                self._board[move[1][0]][move[1][1]] = piece
                piece._taken = True
                prom = [Bishop, Knight, Rook, Queen][['B', 'K', 'R', 'Q'].index(move[1][2].upper())](move[1][:2], self._players[self._toPlay], self)
                self._players[self._toPlay]._pieces.append(prom)
                self._undo_stack.append([piece, p, h, n, x, prom, None, None, mc])
                piece = prom
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
                    self._move_count = -1
                    if piece.__class__.__name__ in ['King', 'Rook']:
                        has_moved = deepcopy(piece._moved)
                        piece._moved = True
                    else:
                        has_moved = None
                    self._undo_stack.append([piece, deepcopy(piece._pos), new, deepcopy(new._taken), x, None, has_moved, None, mc])
                    new._taken = True
                else:
                    if y:
                        t = self._board[move[1][0] - piece._dir[0]][move[1][1]]
                        t._taken = True
                        self._board[move[1][0] - piece._dir[0]][move[1][1]] = self._EMPTY
                        self._undo_stack.append([piece, deepcopy(piece._pos), t, deepcopy(t._taken), x, None, None, None, mc])
                    else:
                        if piece.__class__.__name__ in ['King', 'Rook']:
                            has_moved = deepcopy(piece._moved)
                            piece._moved = True
                        else:
                            has_moved = None
                        self._undo_stack.append([piece, deepcopy(piece._pos), None, None, x, None, has_moved, None, mc])
            self._board[move[0][0]][move[0][1]] = self._EMPTY
            self._board[move[1][0]][move[1][1]] = piece
            piece._pos = move[1][:2]
        for p in piece._player._pieces:
            if p.__class__.__name__ == "Pawn":
                p._just_double = False
        if piece.__class__.__name__ == "Pawn":
            if abs(piece._pos[0] - move[1][0]) == 2:
                piece._just_double = True
        self._move_count += 1
        self._toPlay = (self._toPlay + 1) % 2

    def _undo_move(self, main=False):
        self._played.pop()
        if main:
            self._repetitions.pop()
        b = [[self._EMPTY for _ in range(self._SIZE)] for _ in range(self._SIZE)]
        piece, piece_dest, old, taken, double, prom, has_moved, rook, mc = self._undo_stack.pop()
        self._move_count = mc
        if has_moved is not None:
            piece._moved = has_moved
        if rook is not None:
            rook._moved = False
            self._board[rook._pos[0]][rook._pos[1]] = self._EMPTY
            rook._pos = deepcopy(rook._start_pos)
            self._board[rook._pos[0]][rook._pos[1]] = rook
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
            self._undo_move(True)
        elif move == "draw":
            if self._UI._get_draw_decision(1 - self._toPlay):
                self._mutual = True
        else:
            self._make_move(move)

    def play_game(self):
        times = []
        self._display_board()
        print("White to play")
        while True:
            t0 = time.time()
            p_moves = self._players[self._toPlay]._avail_moves()
            bn = [[p if type(p) == str else p._symbol for p in row] for row in self._board]
            self._repetitions.append(StringList([bn, deepcopy(p_moves)]))
            over = self.__is_over(p_moves)
            if over is not None:
                break
            self.__do_turn(p_moves)
            self._display_board()
            #print(f"Move count = {self._move_count}")
            print(f"{['White', 'Black'][self._toPlay]} to play")
            times.append(time.time() - t0)
            #print(f"Curr.: {round(time.time() - t0, 3)}s\nAvg.: {round(mean(times), 3)}s\nTot.: {round(sum(times), 3)}s")
        print(over)

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
        if move[0] in ["undo", "draw"]:
            return move[0]
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
        return random.choice(moves)

    def _get_prom_choice(self):
        return 3


if __name__ == "__main__":
    print("This file just contains the Game and Player classes")
    #usage()
