from abc import ABC, abstractmethod
from copy import deepcopy
import Game_Player
import time
import math

# This dictionary is used to map strings to the Unicode chess characters
symbols = {"Rw": "♜", "Nw": "♞", "Bw": "♝", "Kw": "♚", "Qw": "♛", "Pw": "♟",
           "Rb": "♖", "Nb": "♘", "Bb": "♗", "Kb": "♔", "Qb": "♕", "Pb": "♙"}

# This dictionary is used to map the full name of the piece to it's shortened, 1 letter, name
contractions = {"Rook": "R", "Queen": "Q", "Bishop": "B", "Knight": "N", "King": "K", "Pawn": "P"}

# This class is the base class for all pieces, some will modify it more than others, depending on how unique they are
class Piece(ABC):
    def __init__(self, pos, player, game):
        self._player = player
        self._pos = pos
        self._game = game
        self._taken = False
        self._symbol = symbols[f"{contractions[self.__class__.__name__]}{['b', 'w'][self._player==self._game._players[0]]}"]

    def _avail_moves(self, careifcheck):
        # Returns the available moves for this piece to play according to FIDE rules
        # careifcheck is used to determine if the piece needs to worry about checking its own king
        moves = []
        if not self._taken:
            for dir in self._dirs:
                i = 1
                newx = self._pos[0] + dir[0] * i
                newy = self._pos[1] + dir[1] * i
                try:
                    new_piece = self._game._board[newx][newy]
                except:
                    pass
                while i < self._max_dis + 1 and -1 < newx < self._game._SIZE and -1 < newy < self._game._SIZE and (
                        new_piece == self._game._EMPTY or
                        new_piece._player != self._player):
                    moves.append([newx, newy])
                    if new_piece != self._game._EMPTY: # Can't go through other pieces by default
                        break
                    i += 1
                    newx = self._pos[0] + dir[0] * i
                    newy = self._pos[1] + dir[1] * i
                    try:
                        new_piece = self._game._board[newx][newy]
                    except:
                        pass
            if careifcheck:
                # Loop through moves, ensuring they don't result in the king being in check, if so, remove it
                pops = []
                for i in range(len(moves)):
                    move = moves[i]
                    self._game._make_move([self._pos, move])
                    if self._game._players[1 - self._game._to_play]._in_check():
                        pops.append(i)
                    self._game._undo_move()
                moves = [move for i, move in enumerate(moves) if i not in pops]
        return moves

    @abstractmethod
    def _is_takeable(self, pos):
        # This function returns if this piece can take the position, pos
        # It is unique to each piece as some how optimisations that can be made, such as the rook
        raise NotImplementedError


class Rook(Piece):
    def __init__(self, pos, player, game):
        super().__init__(pos, player, game)
        self._dirs = [[0, 1], [0, -1], [1, 0], [-1, 0]] # Directions a rook can move in (left, right, up and down)
        self._max_dis = 999 # Rooks can move as far as they like (within the board etc.)
        self._moved = False # Used to check if a rook can castle
        self._start_pos = deepcopy(self._pos)

    def _is_takeable(self, pos):
        # First checks if the position is inline with it, if not, it can't take it
        if pos[0] != self._pos[0] and pos[1] != self._pos[1]:
            return False
        # If it is inline, it has to check it isn't behind other pieces
        if pos[1] == self._pos[1]: # Checks if it is up or down
            flag = True
            direction = [-1, 1][pos[0] > self._pos[0]] # Finding which way it is
            for diff in range(1, abs(pos[0] - self._pos[0])): # Iterate through making sure there's nothing in the way
                if self._game._board[self._pos[0] + (diff*direction)][self._pos[1]] != self._game._EMPTY:
                    flag = False
                    break
            if flag:
                return flag
        if pos[0] == self._pos[0]: # Checks if it is right or left
            flag = True
            direction = [-1, 1][pos[1] > self._pos[1]]
            for diff in range(1, abs(pos[1] - self._pos[1])):
                if self._game._board[self._pos[0]][self._pos[1] + (diff*direction)] != self._game._EMPTY:
                    flag = False
                    break
        return flag


class Knight(Piece):
    def __init__(self, pos, player, game):
        super().__init__(pos, player, game)
        # The knight can move in any L shape, but only one at a time
        self._dirs = [[1, 2], [1, -2], [-1, 2], [-1, -2], [2, 1], [2, -1], [-2, 1], [-2, -1]]
        self._max_dis = 1

    def _is_takeable(self, pos):
        # Simply checks if the position is one in which it can move to
        return pos in self._avail_moves(careifcheck=False)


class Bishop(Piece):
    def __init__(self, pos, player, game):
        super().__init__(pos, player, game)
        self._dirs = [[1, 1], [-1, -1], [1, -1], [-1, 1]] # Can move diagonally
        self._max_dis = 999
        self._colour = deepcopy((self._pos[0] + self._pos[1] + 1) % 2) # Used in checking for draws

    def _is_takeable(self, pos):
        # Same method as knight
        return pos in self._avail_moves(careifcheck=False)


class King(Piece):
    def __init__(self, pos, player, game):
        super().__init__(pos, player, game)
        self._dirs = [[1, 1], [-1, -1], [1, -1], [-1, 1], [0, 1], [0, -1], [1, 0], [-1, 0]]
        self._max_dis = 1
        self._moved = False # Same use as rook, for castling rights

    def _is_takeable(self, pos):
        # Instead of looping through possible positions, since the king can only move 1 square, it checks if the distance is 1
        dis = math.floor(math.sqrt((pos[0] - self._pos[0])**2 + (pos[1] - self._pos[1])**2))
        return dis == 1

    def _avail_moves(self, careifcheck):
        moves = super()._avail_moves(careifcheck) # Gets moves as a standard piece
        new_moves = []
        # Now checking for if it can castle
        rooks = [p for p in self._player._pieces if p.__class__.__name__ == "Rook"]
        if self._moved == False:
            for rook in rooks:
                # Neither the king or rook in question can have moved
                if rook._moved == False and rook._taken == False:
                    empty_flag = True
                    dest_col = rook._pos[1]
                    col = self._pos[1]
                    diff = abs(dest_col - col)
                    dir = [-1, 1][dest_col > col]
                    # The spaces beteen the rook and the king must be empty
                    for i in range(1, diff):
                        new = [self._pos[0], self._pos[1] + i*dir]
                        if self._game._board[new[0]][new[1]] != self._game._EMPTY:
                            empty_flag = False
                            break
                    if empty_flag:
                        check_flag = True
                        # The king cannot be in check or "move through check" when castling
                        for i in range(0, 3):
                            new = [self._pos[0], self._pos[1] + (i * dir)]
                            self._game._make_move([self._pos, new])
                            if self._game._players[1 - self._game._to_play]._in_check():
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
        self._dirs = [[1, 1], [-1, -1], [1, -1], [-1, 1], [0, 1], [0, -1], [1, 0], [-1, 0]]
        self._max_dis = 999

    def _is_takeable(self, pos):
        return pos in self._avail_moves(careifcheck=False)


class Pawn(Piece):
    def __init__(self, pos, player, game):
        super().__init__(pos, player, game)
        self._start_row = self._pos[0] # Used to check if it can move forwards twice (only on first move)
        # Also used when getting the distance it has moved when evaluating the score of the board
        self._just_double = False
        self._dir = [[-1, 1][self._player == self._game._players[0]], 0] # Depending on the colour, the pawn moves in a different direction
        self._max_dis = 1

    def _avail_moves(self, careifcheck):
        moves = []
        if not self._taken:
            t = time.time()  # Timing code
            if self._game._board[self._pos[0] + self._dir[0]][self._pos[1]] == self._game._EMPTY:  # Standard moving forwards
                moves.append([self._pos[0] + self._dir[0], self._pos[1]])
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
            for pos, dir in poses2:  # Check if en passent is valid
                if pos != self._game._EMPTY:
                    if pos._player != self._player and pos.__class__.__name__ == "Pawn":
                        if pos._just_double:
                            moves.append([self._pos[0] + self._dir[0], self._pos[1] + dir])
            Game_Player.time_pawn["Diagonal"] += time.time() - t  # Timing code
            t = time.time()  # Timing code
            pops = set()
            for i, move in enumerate(moves):
                if move[0] in [0, 7] and len(move) == 2:  # Check if the move is a promotion
                    pops.add(i)
                    for prom in [['Q'], ['B', 'N', 'R', 'Q']][careifcheck]:
                        moves.append([move[0], move[1], prom])
            Game_Player.time_pawn["Promotion"] += time.time() - t  # Timing code
            t = time.time()  # Timing code
            if careifcheck:
                for i in range(len(moves)):
                    move = moves[i]
                    self._game._make_move([self._pos, move])
                    if self._game._players[1 - self._game._to_play]._in_check():
                        pops.add(i)
                    self._game._undo_move()
            Game_Player.time_pawn["Check"] += time.time() - t  # Timing code
            t = time.time()  # Timing code
            moves = [move for i, move in enumerate(moves) if i not in pops]
            Game_Player.time_pawn["Removing"] += time.time() - t  # Timing code
        return moves

    def _is_takeable(self, pos):
        # Heavily optimised as pawns can only take diagonally and as this function is
        # only ever called with a king's position, it doesn't need to check for en passent either
        x = False
        y = False
        if self._pos[1] < 7:  # Right Diagonal
            x = pos == [self._pos[0] + self._dir[0], self._pos[1] + 1]
        if self._pos[1] > 0:  # Left Diagonal
            y = pos == [self._pos[0] + self._dir[0], self._pos[1] - 1]
        return x or y


if __name__ == "__main__":
    print("This file just contains the Piece classes")
