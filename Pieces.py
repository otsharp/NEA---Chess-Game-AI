from abc import ABC, abstractmethod
#from Chess import usage
from copy import deepcopy
import Game_Player
import time
import math

symbols = {"Rw": "♜", "Nw": "♞", "Bw": "♝", "Kw": "♚", "Qw": "♛", "Pw": "♟",
           "Rb": "♖", "Nb": "♘", "Bb": "♗", "Kb": "♔", "Qb": "♕", "Pb": "♙"}


class Piece(ABC):
    def __init__(self, pos, player, game):
        self._player = player
        self._pos = pos
        self._game = game
        self._taken = False
        #self._dirs = []
        #self._max_dis = -1

    def _avail_moves(self, careifcheck):
        moves = []
        if not self._taken:
            for dir in self._dirs:
                i = 1
                while i < self._max_dis + 1 and -1 < self._pos[0] + dir[0] * i < self._game._SIZE and -1 < self._pos[1] + dir[
                    1] * i < self._game._SIZE and (
                        self._game._board[self._pos[0] + dir[0] * i][self._pos[1] + dir[1] * i] == self._game._EMPTY or
                        self._game._board[self._pos[0] + dir[0] * i][self._pos[1] + dir[1] * i]._player != self._player):
                    moves.append([self._pos[0] + dir[0] * i, self._pos[1] + dir[1] * i])
                    if self._game._board[self._pos[0] + dir[0] * i][self._pos[1] + dir[1] * i] != self._game._EMPTY:
                        break
                    i += 1
            if careifcheck:
                pops = []
                for i in range(len(moves)):
                    move = moves[i]
                    self._game._make_move([self._pos, move])
                    if self._game._players[1 - self._game._toPlay]._in_check():
                        pops.append(i)
                    self._game._undo_move()
                moves = [move for i, move in enumerate(moves) if i not in pops]
        return moves

    @abstractmethod
    def _is_takeable(self, pos):
        raise NotImplementedError


class Rook(Piece):
    def __init__(self, pos, player, game):
        super().__init__(pos, player, game)
        if self._player == self._game._players[0]:
            self._symbol = symbols["Rw"]
        else:
            self._symbol = symbols["Rb"]
        self._dirs = [[0, 1], [0, -1], [1, 0], [-1, 0]]
        self._max_dis = 999
        self._moved = False
        self._start_pos = deepcopy(self._pos)

    def _is_takeable(self, pos):
        if pos[0] != self._pos[0] and pos[1] != self._pos[1]:
            return False
        if pos[1] == self._pos[1]:
            flag = True
            direction = [-1, 1][pos[0] > self._pos[0]]
            for diff in range(1, abs(pos[0] - self._pos[0])):
                if self._game._board[pos[0] + (diff*direction)][pos[1]] != self._game._EMPTY:
                    flag = False
                    break
            if flag:
                return flag
        if pos[0] == self._pos[0]:
            flag = True
            direction = [-1, 1][pos[1] > self._pos[1]]
            for diff in range(1, abs(pos[1] - self._pos[1])):
                if self._game._board[pos[0]][pos[1] + (diff*direction)] != self._game._EMPTY:
                    flag = False
                    break
        return flag


class Knight(Piece):
    def __init__(self, pos, player, game):
        super().__init__(pos, player, game)
        if self._player == self._game._players[0]:
            self._symbol = symbols["Nw"]
        else:
            self._symbol = symbols["Nb"]
        self._dirs = [[1, 2], [1, -2], [-1, 2], [-1, -2], [2, 1], [2, -1], [-2, 1], [-2, -1]]
        self._max_dis = 1

    def _is_takeable(self, pos):
        return pos in self._avail_moves(careifcheck=False)


class Bishop(Piece):
    def __init__(self, pos, player, game):
        super().__init__(pos, player, game)
        if self._player == self._game._players[0]:
            self._symbol = symbols["Bw"]
        else:
            self._symbol = symbols["Bb"]
        self._dirs = [[1, 1], [-1, -1], [1, -1], [-1, 1]]
        self._max_dis = 999
        self._colour = deepcopy((self._pos[0] + self._pos[1] + 1) % 2)

    def _is_takeable(self, pos):
        return pos in self._avail_moves(careifcheck=False)


class King(Piece):
    def __init__(self, pos, player, game):
        super().__init__(pos, player, game)
        if self._player == self._game._players[0]:
            self._symbol = symbols["Kw"]
        else:
            self._symbol = symbols["Kb"]
        self._dirs = [[1, 1], [-1, -1], [1, -1], [-1, 1], [0, 1], [0, -1], [1, 0], [-1, 0]]
        self._max_dis = 1
        self._moved = False

    def _is_takeable(self, pos):
        dis = math.floor(math.sqrt((pos[0] - self._pos[0])**2 + (pos[1] - self._pos[1])**2))
        return dis == 1

    def _avail_moves(self, careifcheck):
        moves = super()._avail_moves(careifcheck)
        new_moves = []
        rooks = [p for p in self._player._pieces if p.__class__.__name__ == "Rook"]
        if self._moved == False:
            #print("Can castle step 1")
            for rook in rooks:
                if rook._moved == False and rook._taken == False:
                    empty_flag = True
                    dest_col = rook._pos[1]
                    col = self._pos[1]
                    diff = abs(dest_col - col)
                    dir = [-1, 1][dest_col > col]
                    for i in range(1, diff):
                        #print(i)
                        new = [self._pos[0], self._pos[1] + i*dir]
                        if self._game._board[new[0]][new[1]] != self._game._EMPTY:
                            empty_flag = False
                            break
                    if empty_flag:
                        check_flag = True
                        for i in range(1, 3):
                            new = [self._pos[0], self._pos[1] + (i * dir)]
                            self._game._make_move([self._pos, new])
                            if self._game._players[1 - self._game._toPlay]._in_check():
                                check_flag = False
                            self._game._undo_move()
                            if not check_flag:
                                break
                        if check_flag:
                            new_moves.append([self._pos[0], self._pos[1] + dir*2])
        for m in new_moves:
            moves.append(m)
        return moves



class Queen(Piece):
    def __init__(self, pos, player, game):
        super().__init__(pos, player, game)
        if self._player == self._game._players[0]:
            self._symbol = symbols["Qw"]
        else:
            self._symbol = symbols["Qb"]
        self._dirs = [[1, 1], [-1, -1], [1, -1], [-1, 1], [0, 1], [0, -1], [1, 0], [-1, 0]]
        self._max_dis = 999

    def _is_takeable(self, pos):
        return pos in self._avail_moves(careifcheck=False)


class Pawn(Piece):
    def __init__(self, pos, player, game):
        super().__init__(pos, player, game)
        self._start_row = self._pos[0]
        self._just_double = False
        if self._player == self._game._players[0]:
            self._symbol = symbols["Pw"]
            self._dir = [1, 0]
        else:
            self._symbol = symbols["Pb"]
            self._dir = [-1, 0]
        self._max_dis = 1

    def _avail_moves(self, careifcheck):
        moves = []
        if not self._taken:
            t = time.time()  # Timing code
            try:
                if self._game._board[self._pos[0] + self._dir[0]][self._pos[1]] == self._game._EMPTY:  # Standard moving forwards
                    moves.append([self._pos[0] + self._dir[0], self._pos[1]])
            except:
                print("Quitting")
                print(self._pos, self._dir)
                quit()
            Game_Player.time_pawn["Standard"] += time.time() - t  # Timing code
            t = time.time()  # Timing code
            if self._pos[0] == self._start_row:  # Move forward twice first move
                if self._game._board[self._pos[0] + 2*self._dir[0]][self._pos[1]] == self._game._EMPTY and self._game._board[self._pos[0] + self._dir[0]][self._pos[1]] == self._game._EMPTY:
                    moves.append([self._pos[0] + 2*self._dir[0], self._pos[1]])
            Game_Player.time_pawn["Double"] += time.time() - t  # Timing code
            t = time.time()  # Timing code
            poses1 = []  # diagonal taking
            poses2 = []  # en passant
            if self._pos[1] < 7:  # Right Diagonal
                poses1.append([self._game._board[self._pos[0] + self._dir[0]][self._pos[1] + 1], 1])
                poses2.append([self._game._board[self._pos[0]][self._pos[1] + 1], 1])
            if self._pos[1] > 0:  # Left Diagonal
                poses1.append([self._game._board[self._pos[0] + self._dir[0]][self._pos[1] - 1], -1])
                poses2.append([self._game._board[self._pos[0]][self._pos[1] - 1], -1])
            for pos, dir in poses1:  # Check diagonal is enemy for standard taking
                if pos != self._game._EMPTY:
                    if pos._player != self._player:
                        moves.append([self._pos[0] + self._dir[0], self._pos[1] + dir])
            for pos, dir in poses2:  # Check en passent is valid
                if pos != self._game._EMPTY:
                    if pos._player != self._player and pos.__class__.__name__ == "Pawn":
                        if pos._just_double:
                            moves.append([self._pos[0] + self._dir[0], self._pos[1] + dir])
            Game_Player.time_pawn["Diagonal"] += time.time() - t  # Timing code
            t = time.time()  # Timing code
            pops = set()
            for i, move in enumerate(moves):
                if move[0] in [0, 7]:  # promotion
                    pops.add(i)
                    for prom in [['Q'], ['B', 'K', 'R', 'Q']][careifcheck]:
                        moves.append([move[0], move[1], prom])
            Game_Player.time_pawn["Promotion"] += time.time() - t  # Timing code
            t = time.time()  # Timing code
            if careifcheck:
                for i in range(len(moves)):
                    move = moves[i]
                    self._game._make_move([self._pos, move])
                    if self._game._players[1 - self._game._toPlay]._in_check():
                        pops.add(i)
                    self._game._undo_move()
            Game_Player.time_pawn["Check"] += time.time() - t  # Timing code
            t = time.time()  # Timing code
            moves = [move for i, move in enumerate(moves) if i not in pops]
            Game_Player.time_pawn["Removing"] += time.time() - t  # Timing code
        return moves

    def _is_takeable(self, pos):
        if self._pos[1] < 7:  # Right Diagonal
            return pos == [self._pos[0] + self._dir[0], self._pos[1] + 1]
        if self._pos[1] > 0:  # Left Diagonal
            return pos == [self._pos[0] + self._dir[0], self._pos[1] - 1]
        return False


if __name__ == "__main__":
    print("This file just contains the Piece classes")
    #usage()
