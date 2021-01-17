from Pieces import *
import os
from copy import deepcopy
import time
import random
from statistics import mean
from collections import Counter
import chess # to read polyglot opening book

class OutOfOpeningError(Exception):
    pass

class StringList(object):
    # Used for checking game state repetition as it allows lists to be keys in dictionaries (i.e Counter)
    # Does this by converting the list to the string representation of the list
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

        # Constants used in heuristic calculations
        self.__pawn_value_adjustments = [
                                        [9, 9, 9, 9, 9, 9, 9, 9],
                                        [3, 3, 3.1, 3.25, 3.25, 3.1, 3, 3],
                                        [2.2, 2.3, 2.4, 2.7, 2.7, 2.4, 2.3, 2.2],
                                        [2, 2.1, 2.2, 2.4, 2.4, 2.2, 2.1, 2],
                                        [1.3, 1.3, 1.3, 1.5, 1.5, 1.3, 1.3, 1.3],
                                        [1, 1.05, 1.1, 1.2, 1.2, 1.1, 1.05, 1],
                                        [1, 1, 1, 1, 1, 1, 1, 1],
                                        [1, 1, 1, 1, 1, 1, 1, 1]
                                        ]
        self.__knight_value_adjustments = [
                                        [1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1],
                                        [1.05, 1.2, 1.2, 1.25, 1.25, 1.2, 1.2, 1.05],
                                        [1.1, 1.2, 1.25, 1.35, 1.35, 1.25, 1.2, 1.1],
                                        [1.1, 1.25, 1.35, 1.5, 1.5, 1.35, 1.25, 1.1],
                                        [1.1, 1.25, 1.35, 1.5, 1.5, 1.35, 1.25, 1.1],
                                        [1.05, 1.1, 1.2, 1.25, 1.25, 1.2, 1.1, 1.05],
                                        [1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1],
                                        [1, 1, 1, 1, 1, 1, 1, 1]
                                        ]
        self.__pawn_value_adjustments = self.__pawn_value_adjustments[::-1]
        self.__knight_value_adjustments = self.__knight_value_adjustments[::-1]

        # Pre-calculates the adjustments tables for the knights, queens and bishop/rooks for use in heuristics
        a = 1

        self.__knight_value_adjustments = [[((i-1)/a)+1 for i in row] for row in self.__knight_value_adjustments]

        q_a = 0.2285
        q_b = -4.0589
        q_c = 2
        q_d = -0.06
        self.__queen_covering_adjustments = [q_c**((q_a * x) + q_b) + q_d for x in range(30)]

        r_a = 0.4489
        r_b = -6.2653
        r_c = 2
        r_d = -0.013
        self.__rook_covering_adjustments = [r_c**((r_a * x) + r_b) + r_d for x in range(15)]

        # Constants used, such as the board size being and 8x8
        self._EMPTY = "_"
        self._AI_TYPES = 3
        self._SIZE = 8
        self._UI = UItype(self)

    def __get_settings(self):
        # Returns the game settings from the UI, as that's where they are inputted by the user
        return self._UI._settings_choice

    def _reset_game(self):
        # Before a new game is played, the board and other variables, such as who's to play, are reset
        self._board = self.__reset_board()
        self._opening_board = chess.Board()
        self._undo_stack = []
        self._played = []
        self._mutual = False
        self._repetitions = []
        self._move_count = 0
        self._to_play = 0
        self._just_undone = False

    def __reset_board(self):
        # Resets the board, either according to normal chess rules, or using Fischer random chess rules if that setting is selected
        fischer = self._settings[4]
        b = [[self._EMPTY for _ in range(self._SIZE)] for __ in range(self._SIZE)]
        if fischer:
            backline = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
            random.shuffle(backline)
        if fischer:
            b[0] = [backline[i]([0, i], self._players[0], self) for i in range(len(backline))]
            rooks = [piece for piece in b[0] if piece.__class__.__name__ == "Rook"]
            for rook in rooks:
                rook._moved = True
        else:
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
        if fischer:
            b[7] = [backline[i]([7, i], self._players[1], self) for i in range(len(backline))]
            rooks = [piece for piece in b[7] if piece.__class__.__name__ == "Rook"]
            for rook in rooks:
                rook._moved = True
        else:
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

    def _sort(self, l):
    # Performs a recursive mergesort on list l
        if len(l) > 1: # Checks if the list is only 1 element, in which case it is already "sorted"
            new = []
            mid = len(l) // 2
            left_half = l[:mid]
            right_half = l[mid:]

            left_half = self._sort(left_half)
            right_half = self._sort(right_half)

            i = 0
            j = 0
            while i < len(left_half) and j < len(right_half):
                if left_half[i] < right_half[j]:
                    new.append(left_half[i])
                    i += 1
                else:
                    new.append(right_half[j])
                    j += 1

            while i < len(left_half):
                new.append(left_half[i])
                i += 1

            while j < len(right_half):
                new.append(right_half[j])
                j += 1

            return new
        return l

    def _is_draw(self, p_moves, in_ai_moves=False):
        # This function returns whether the current game state is a draw according to FIDE rules, and if so, what type

        # Stalemate occurs if the player is not in check and has no legal moves
        stalemate = p_moves == [] and not self._players[self._to_play]._in_check()

        # This checks for the impossibility of checkmate, e.g. King vs King
        player1_pieces = self._sort([p.__class__.__name__ for p in self._players[0]._pieces if p._taken == False])
        player2_pieces = self._sort([p.__class__.__name__ for p in self._players[1]._pieces if p._taken == False])
        pieces = sorted([player1_pieces, player2_pieces], key=len)
        impossibility = pieces in [[["King"], ["King"]], [["King"], ["Bishop", "King"]], [["King"], ["King", "Knight"]]] # These are the combinations of pieces
        if pieces == [["Bishop", "King"], ["Bishop", "King"]]: # For bishop vs bishop, must be different colours for impossibility to be true
            if [p._colour for p in self._players[0]._pieces if (p._taken == False and p.__class__.__name__ == "Bishop")][0] != [p._colour for p in self._players[1]._pieces if (p._taken == False and p.__class__.__name__ == "Bishop")][0]:
                impossibility = True

        # This checks in a certain board state has already appeared 5 times
        repetition = False
        if self._repetitions:
            c = Counter(self._repetitions)
            x = max(c.values())
            if x >= 5:
                repetition = True

        # This checks if there hasn't been a capture in the last 75 moves
        move_limit = False
        if self._move_count >= 75:
            move_limit = True

        # This checks if the players agree to draw
        agreement = self._mutual

        # Returning the type of draw, or if it's not a draw
        if stalemate:
            return "Stalemate"
        if impossibility:
            return "Impossibility"
        if repetition:
            return "Repetition"
        if move_limit:
            return "Move limit"
        if agreement:
            return "Agreement"
        return False

    def _is_over(self, p_moves, in_ai_moves=False):
        # Checks whether a game is over, either by checkmate, or by a draw
        if self._players[self._to_play]._in_checkmate(p_moves):
            # Returns who won if there is a checkmate
            return f"{['White', 'Black'][1 - self._to_play]} wins"
        if self._players[1 - self._to_play]._in_checkmate(p_moves):
            return f"{['White', 'Black'][self._to_play]} wins"
        x = self._is_draw(p_moves, in_ai_moves)
        if x:
            return x
        return None

    def _make_move(self, move, main=False, p_moves=[]):
        # Moves and takes the appropriate pieces for the move, and switches the player to play
        # Main means it is a proper move, i.e. not one made by the AI when it is trying lots of moves to determine what's good
        if main:
            # Only add to repetitions if the move is a main move
            bn = [[p if type(p) == str else p._symbol for p in row] for row in self._board]
            self._repetitions.append(StringList([bn, deepcopy(p_moves)]))
            x = ""
            if len(move[1]) == 3: # Checks if the move is a promotion as it then parses it slightly differently
                x = move[1][2]
            if not self._settings[4]: # Checks if the game is fischer random chess, if so, the openings cannot be used
                self._opening_board.push_san(f"{chr(move[0][1] + 97)}{move[0][0]+1}{chr(move[1][1] + 97)}{move[1][0]+1}{x}")
        mc = deepcopy(self._move_count)
        if len(move[1]) == 3: # Again checks if the move is a promotion as it then parses it slightly differently
            # Add the move to the stack of played moves
            self._played.append([[chr(move[0][1] + 97), move[0][0]+1], [chr(move[1][1] + 97), move[1][0]+1, move[1][2]]])
        else:
            self._played.append([[chr(move[0][1] + 97), move[0][0]+1], [chr(move[1][1] + 97), move[1][0]+1]])
        piece = self._board[move[0][0]][move[0][1]] # Selects the piece to move
        if piece.__class__.__name__ == "Pawn": # Keeping track of if the piece has just double moved, for en passent, if this move is later undone
            x = deepcopy(piece._just_double)
            self._move_count = -1
        else:
            x = None
        if piece.__class__.__name__ == "King" and abs(move[0][1] - move[1][1]) == 2: # Checks if the move is castling
            king = self._board[move[0][0]][move[0][1]]
            if move[1][1] > move[0][1]: # Checks which way the king is castling and selects the appropriate rook
                rook = self._board[move[0][0]][7]
            else:
                rook = self._board[move[0][0]][0]
            self._undo_stack.append([king, deepcopy(king._pos), None, None, None, None, False, rook, mc]) # Adds state to undo stack
            # Moving the king and rook
            self._board[king._pos[0]][king._pos[1]] = self._EMPTY
            self._board[rook._pos[0]][rook._pos[1]] = self._EMPTY
            king._pos = move[1]
            rook._pos = [move[1][0], move[1][1] + [1, -1][move[1][1] > move[0][1]]]
            self._board[king._pos[0]][king._pos[1]] = king
            self._board[rook._pos[0]][rook._pos[1]] = rook
            # Update the pieces so they can't castle again
            king._moved = True
            rook._moved = True
        else:
            if len(move[1]) == 3:  # Checks if the move is a promotion
                new = self._board[move[1][0]][move[1][1]]
                if type(new) != str: # Checking if the move is taking a piece, and updating the piece if it is, whilst recording the current state (for undoing)
                    n = deepcopy(new._taken)
                    new._taken = True
                    self._move_count = -1 # Resets move count for draw conditions
                    h = new
                else:
                    n = None
                    h = None
                p = deepcopy(piece._pos) # Keeping track of the old position of the piece incase the move is undone
                self._board[move[1][0]][move[1][1]] = piece # Moves pawn to new position
                piece._taken = True # As pawn is being replaced, it must go
                prom = [Bishop, Knight, Rook, Queen][['B', 'N', 'R', 'Q'].index(move[1][2].upper())](move[1][:2], self._players[self._to_play], self)
                if prom.__class__.__name__ == "Rook":
                    prom._moved = True # To prevent new rooks being used in castling
                self._players[self._to_play]._pieces.append(prom) # Add the new piece to the player
                self._undo_stack.append([piece, p, h, n, x, prom, None, None, mc]) # For undoing moves
                piece = prom # Update piece to be the replacement piece
            else:
                new = self._board[move[1][0]][move[1][1]]
                y = False
                if type(new) == str and piece.__class__.__name__ == "Pawn":
                    if move[1][1] != piece._pos[1]: # Checking for en passent captures
                        y = True
                if type(new) != str:
                    self._move_count = -1 # Resets move count for draw conditions
                    if piece.__class__.__name__ in ['King', 'Rook']:
                        has_moved = deepcopy(piece._moved) # Potentially allows castling if this move is undone
                        piece._moved = True # So the piece can't castle in the future
                    else:
                        has_moved = None
                    self._undo_stack.append([piece, deepcopy(piece._pos), new, deepcopy(new._taken), x, None, has_moved, None, mc])
                    new._taken = True
                else:
                    if y: # If en passent
                        t = self._board[move[1][0] - piece._dir[0]][move[1][1]] # Captured pawn
                        t._taken = True
                        self._board[move[1][0] - piece._dir[0]][move[1][1]] = self._EMPTY # Remove captured pawn from the board
                        self._undo_stack.append([piece, deepcopy(piece._pos), t, deepcopy(t._taken), x, None, None, None, mc])
                    else:
                        if piece.__class__.__name__ in ['King', 'Rook']:
                            has_moved = deepcopy(piece._moved) # Same as above but for when the move is not a capture
                            piece._moved = True
                        else:
                            has_moved = None
                        self._undo_stack.append([piece, deepcopy(piece._pos), None, None, x, None, has_moved, None, mc])
            self._board[move[0][0]][move[0][1]] = self._EMPTY # Removes the piece from its current position
            self._board[move[1][0]][move[1][1]] = piece # Puts the piece in its new position
            old_pos = deepcopy(piece._pos)
            piece._pos = move[1][:2] # Updates the piece's position
        for p in piece._player._pieces: # Loop through the player's pawns, resetting the just_double flag
            if p.__class__.__name__ == "Pawn":
                p._just_double = False
        if piece.__class__.__name__ == "Pawn":
            if abs(old_pos[0] - move[1][0]) == 2:
                piece._just_double = True # If a pawn has just double moved, set the flag to true
        self._move_count += 1 # Increment the moves without capture
        self._to_play = (self._to_play + 1) % 2 # Switch the player to play

    def _undo_move(self, main=False):
        # Undoes the last move
        self._played.pop() # Remove the last move from the stack
        if main:
            self._repetitions.pop() # Remove the last board state from draw checks, if it is a main move
            if not self._settings[4]:
                self._opening_board.pop() # Does the same for the opening board
        b = [[self._EMPTY for _ in range(self._SIZE)] for _ in range(self._SIZE)] # Creates an empty board
        piece, piece_dest, old, taken, double, prom, has_moved, rook, mc = self._undo_stack.pop() # Get previous board state values
        # Restoring values
        self._move_count = mc
        if has_moved is not None:
            piece._moved = has_moved
        if rook is not None:
            rook._moved = False
            self._board[rook._pos[0]][rook._pos[1]] = self._EMPTY
            rook._pos = deepcopy(rook._start_pos)
            self._board[rook._pos[0]][rook._pos[1]] = rook
        if prom is not None: # If the last move was a promotion, switch out the new piece for the pawn
            piece._taken = False
            self._players[1 - self._to_play]._pieces.remove(prom)
        piece._pos = piece_dest
        if piece.__class__.__name__ == "Pawn":
            piece._just_double = double # Keeping track of if a piece just double moved
        if old is not None:
            old._taken = False
        for i in range(2):
            for piece in self._players[i]._pieces:
                if not piece._taken:
                    b[piece._pos[0]][piece._pos[1]] = piece # Insert all the pieces into the empty board
        self._board = b # Update the board
        self._to_play = (self._to_play + 1) % 2 # Switch the player to play

    def __do_turn(self, moves):
        # Carries out a turn for the player, whether it is making a move, undoing, drawing or quiting
        double = False
        if self._just_undone and (self._players[self._to_play].__class__.__name__ == "AI"):
            move = "undo" # If the player just undid a move, and it is the AI's turn, i automatically undoes again
            double = True
        else:
            move = self._players[self._to_play]._get_move(moves) # If not automatically undoing, get the player's move
        self._just_undone = False
        if move == "undo": # Checks if the player wishes to undo
            if not double:
                self._just_undone = True # Used for check above
            self._undo_move(main=True) # Undoes the move
            if self._UI.__class__.__name__ == "GUI":
                self._do_GUI_func(f"_green_last('Undo')") # If using a GUI, updates the colour of the squares for the "last move"
        elif move == "draw": # Checks if the player wishes to draw
            if self._players[1 - self._to_play].__class__.__name__ != "AI":
                if self._do_GUI_func(f"_get_draw_decision({str(1 - self._to_play)})"): # If both players agree
                    self._mutual = True # Then draw
        elif move == "quit": # If the move is quit, do nothing, as it is handled somewhere else
            pass
        else:
            self._make_move(move, main=True, p_moves=moves) # If not a special move, make the move
            if self._UI.__class__.__name__ == "GUI":
                self._do_GUI_func(f"_green_last({str(move)})") # Update the GUI's green squares

    def wait_until_ready_then_play(self):
        # Called at the beginning, and everytime a game is over
        self._ready = None
        self.over = None
        while self._UI._ready is None: # Waits until the GUI is ready to play, if Terminal, then UI._ready is always "New"
            time.sleep(0.2)

        self._settings = self.__get_settings() # Gets the settings for the game
        if self._settings[0] == 0: # Checks if white is a Player or an AI
            player_1 = Player(self)
        else:
            player_1 = AI(self, ["Random", "MiniMax", "MCTS"][self._settings[0] - 1]) # If an AI, which type
        # Does the same for black
        if self._settings[1] == 0:
            player_2 = Player(self)
        else:
            player_2 = AI(self, ["Random", "MiniMax", "MCTS"][self._settings[1] - 1])
        self._players = [player_1, player_2]
        self._reset_game() # Resets the board etc. as above
        for player in self._players:
            player._2nd_init() # Since the players have a list of their pieces, but the pieces refrence the players,
                               # they need to be updated after the pieces are created

        self._ready = "Yes" # Indicates to the UI that the game is ready
        while self._UI._ready == "Load": # If a game is being loaded, waits until the GUI has the moves ready
            time.sleep(0.2)

        global time_pieces, time_pawn # timing code
        time_pieces = {"Pawn": 0, "King": 0, "Queen": 0, "Rook": 0, "Knight": 0, "Bishop": 0} # timing code
        time_pawn = {"Standard": 0, "Double": 0, "Diagonal": 0, "Promotion": 0, "Check": 0, "Removing": 0} # timing code
        times = [] # timing code
        p_moves = self._players[self._to_play]._avail_moves() # Gets the moves available for the current player
        self._display_board() # Updates the board for the user
        while self.over is None: # Does this loop whilst the game is not over
            t0 = time.time() # timing code
            self.__do_turn(p_moves) # Above
            if self.over == "Quit": # If the user wishes to quit, break the loop
                break
            self._display_board() # Update the board
            if self._UI.__class__.__name__ == "GUI":
                self._do_GUI_func("_update_eval()") # Updates the game evaluation label if it is a GUI
            else:
                print(f"Score = {round(self._get_score(), 2)}") # If not GUI, print the evaluation
            p_moves = self._players[self._to_play]._avail_moves() # Updates the available moves for the player
            self.over = self._is_over(p_moves) # Checks if the game is now over
            times.append(time.time() - t0) # timing code
        if self._UI.__class__.__name__ == "GUI": # Checks if the UI is a GUI
            if self.over != "Quit":
                if not self._settings[4]:
                    self._do_GUI_func(f"_finished_save('{str(self.over)}')") # If the game is won or drawn, ask the user if they want to save the game
                self._do_GUI_func(f"_notify('{str(self.over)}')") # Notify the user of the result
            self._do_GUI_func("_end()") # Close the game screen and go back to the menu
            self.wait_until_ready_then_play() # Call this function for when a new game might be played
        else:
            self._UI._notify(self.over) # Notify the user of the result
            self._UI._end() # Quit out of the program

    def _do_GUI_func(self, func):
        # As all Tkinter functions must be executed in the main-thread, not this thread, this function 
        # sets a flag for the main-thread to do the requested function, and waits for it to be executed
        self._UI._func = func
        while not self._UI._done_func:
            time.sleep(0.1)
        self._UI._done_func = False
        r = self._UI._func_return
        self._UI._func_return = None
        return r

    def _display_board(self):
        # Updates the game board by calling the UI functions
        if self._UI.__class__.__name__ == "GUI":
            self._do_GUI_func("_display_board()")
        else:
            self._UI._display_board()

    def __is_move_legal(self, move):
        # Returns if a move is legal
        return move in self._players[self._to_play]._avail_moves()

    def _get_score(self, moves=[]):
        # Returns the evaluation for the current board state
        score = 0
        for i in range(2): # Iterates through playes
            for piece in self._players[i]._pieces: # Iterates through player's pieces
                if not piece._taken:
                    name = piece.__class__.__name__
                    if name == "Pawn":
                        dis = abs(piece._pos[0] - piece._start_row) + 1
                        val = 1 * self.__pawn_value_adjustments[dis][piece._pos[1]]
                    elif name == "King":
                        val = 999
                    elif name == "Bishop":
                        num = len(piece._avail_moves(careifcheck=False))
                        val = 3 + self.__rook_covering_adjustments[int(num)]
                    elif name == "Knight":
                        dis = abs(piece._pos[0] - [0, 7][i])
                        val = 3 * self.__knight_value_adjustments[dis][piece._pos[1]]
                    elif name == "Rook":
                        num = len(piece._avail_moves(careifcheck=False))
                        val = 5 + self.__rook_covering_adjustments[int(num)]
                    elif name == "Queen":
                        num = len(piece._avail_moves(careifcheck=False))
                        val = 9 + self.__queen_covering_adjustments[int(num)]
                    if i == 0: # Positive for white, negative for black
                        score += val
                    else:
                        score -= val
        return score


class Player:
    def __init__(self, game):
        self._pieces = []
        self._game = game

    def _2nd_init(self):
        # Adds all of its pieces to a list for easy access
        for row in self._game._board:
            for p in row:
                if p != self._game._EMPTY:
                    if p._player == self:
                        self._pieces.append(p)

    def _avail_moves(self, careifcheck=True):
        # Returns all of the legal moves for the player, by combining the legal moves for all of its pieces
        global time_pieces  # Timing code
        moves = []
        for piece in self._pieces:
            t = time.time()  # Timing code
            p_moves = piece._avail_moves(careifcheck)
            time_pieces[piece.__class__.__name__] += time.time() - t  # Timing code
            for move in p_moves:
                moves.append([piece._pos, move]) # As it must know the starting position of the move
        return moves

    def _get_move(self, moves):
        # Returns a move chosen by the user
        move = self._game._UI._get_move(moves) # Gets the move from the UI
        if self._game._UI.__class__.__name__ == "GUI": # Initialising flags used to determine if the move is special
                self._game._UI._undoing = False
                self._game._UI._drawing = False
                self._game._UI._quiting = False
        if (move[0] in ["draw", "quit"]) or (move[0] == "undo" and self._game._played): # Checks if move is special
            return move[0]
        move1 = []
        for pos in move[:2]:
            try: # Checks the move is in the correct format
                move1.append([int(pos[1]) - 1, ord(pos[0].lower()) - 97])
            except (ValueError, IndexError) as e:
                if self._game._UI.__class__.__name__ == "Terminal":
                    self.__notify(f"Value / Index Error, {e}")
                return self._get_move(moves) # If not, try again
        for pos in move1:
            for coord in pos:
                if coord > 7 or coord < 0: # Checks the move is within the board
                    if self._game._UI.__class__.__name__ == "Terminal":
                        self.__notify("Out of bounds")
                    return self._get_move(moves) # If not, try again
        if len(move) == 3: # If it is a promotion
            move1[1].append(move[2].upper()) # Add promotion choice to the end of the move
        if move1 not in moves: # Checks if the move is legal
            return self._get_move(moves) # If not, try again
        return move1

    def _in_check(self):
        # Returns if the player is in check by iterating through the opponent's pieces
        king_pos = self._pieces[[p.__class__.__name__ for p in self._pieces].index("King")]._pos
        opponent_pieces = self._game._players[1-self._game._players.index(self)]._pieces
        for piece in opponent_pieces:
            if not piece._taken:
                if piece._is_takeable(king_pos):
                    return True
        return False

    def _in_checkmate(self, p_moves=None):
        # Returns if the player is in checkmate, i.e it is in check and can't move
        if p_moves is None:
            p_moves = self._avail_moves()
        return p_moves == [] and self._in_check()

    def __notify(self, message):
        # Sends a messaage to the UI
        if self._game._UI.__class__.__name__ == "GUI":
            self._game._do_GUI_func(f"_notify(\"{str(message)}\")")
        else:
            self._game._UI._notify(message)


class AI(Player):
    def __init__(self, game, ai_type="Random"):
        super().__init__(game)
        # Variables for the AI
        self._type = ai_type
        self._max_depth = 2
        self._playouts = 2
        self._in_open = True
        self.__threshold = 12
        self.__max_depth_reached = 0
        self._custom_difficulty = -1

    def _get_move(self, moves):
        # Overrides the Player function
        self._difficulty = self._game._settings[3]
        if self._custom_difficulty != -1:
            self._difficulty = self._custom_difficulty
        if self._game._UI.__class__.__name__ == "GUI": # If a GUI, disable all of the buttons so the user can't mess up the AI move
            self._game._do_GUI_func("_disable()")
        try:
            if self._in_open == False or len(self._game._played) > [4, 6, 8, 12, 999][self._difficulty - 1]: # Is better at openings depending on the difficulty
                raise OutOfOpeningError
            with chess.polyglot.open_reader("opening_book.bin") as reader:
                for entry in reader.find_all(self._game._opening_board):
                    move = str(entry.move)
                    break
            x = [[int(move[1])-1, ord(move[0])-97], [int(move[3])-1, ord(move[2])-97]]
            if self._game._UI.__class__.__name__ == "GUI":
                self._game._do_GUI_func("_enable()")
            return x
        except: # Raises an error once no more opening moves
            self._in_open = False
            global time_minmax, time_pieces, time_pawn # timing code
            time_minmax = {"Start check": 0, "Making moves": 0, "Getting moves": 0, "Checking over": 0, # timing code
                            "Undoing moves": 0, "ab pruning": 0, "Getting score": 0, "Sub total": 0}
            time_pieces = {"Pawn": 0, "King": 0, "Queen": 0, "Rook": 0, "Knight": 0, "Bishop": 0} # timing code
            time_pawn = {"Standard": 0, "Double": 0, "Diagonal": 0, # timing code
                        "Promotion": 0, "Check": 0, "Removing": 0}
            if self._type == "MiniMax":
                self.__current_score = self._game._get_score()
                if self._game._players.index(self) == 0:  # Is it white?
                    t0 = time.time()
                    best_score, move = self.__max_move(moves)  # Maximise score
                    time_total = time.time() - t0
                else:
                    t0 = time.time()
                    best_score, move = self.__min_move(moves)  # Minimise score
                    time_total = time.time() - t0
            elif self._type == "MCTS":
                t0 = time.time()
                move = self.__MCTS(moves, self._game._players.index(self) == 0) # Passes in which player to do better for
                time_total = time.time() - t0
            else:
                move = random.choice(moves)
            if self._game._UI.__class__.__name__ == "GUI":
                self._game._do_GUI_func("_enable()") # Re enable all the buttons that were disabled
            return move

    def _get_prom_choice(self):
        # Always promotes to a queen as it is the best piece
        return 3

    def __playout(self):
        # Used in MCTS, it is a simulated random game
        count = 0
        moves = self._game._players[self._game._to_play]._avail_moves()
        x = self._game._is_over(moves, True)
        while x is None:
            move = random.choice(moves)
            self._game._make_move(move) # Make a random move
            moves = self._game._players[self._game._to_play]._avail_moves()
            count += 1
            x = self._game._is_over(moves, True)
        if x == "White wins":
            y = 1
        elif x == "Black wins":
            y = -1
        else:
            y = 0
        for i in range(count):
            self._game._undo_move() # Go back to pre-playout state
        return y # Return the result

    def __MCTS(self, moves, maximise):
        # Runs many playouts, and returns the move with the best total score
        scores = []
        for move in moves: # Make a move
            total = 0
            self._game._make_move(move)
            for i in range(self._playouts):
                total += self.__playout() # Then do a playout from that move
            scores.append(total)
            self._game._undo_move()
        return moves[scores.index([min(scores), max(scores)][maximise])]

    def __max_move(self, moves, a=-9999, b=9999, depth=0, just_captured=False, biggest_depth=[0]):
        # Minimax maximising function as in analysis section
        global time_minmax  # Timing code
        t0 = time.time()  # Timing code
        results = []
        Ts = []  # Timing code
        t = time.time()  # Timing code
        depth += 1
        if depth > self._max_depth and not just_captured:
            ts = time.time()  # Timing code
            s = self._game._get_score(moves=moves)
            time_minmax["Getting score"] += (time.time() - ts)  # Timing code
            return s, None
        best_score = -9999
        time_minmax["Start check"] += (time.time() - t)  # Timing code
        for move in moves:
            t = time.time()  # Timing code
            new_just_captured = False
            if self._game._board[move[1][0]][move[1][1]] != self._game._EMPTY:
                new_just_captured = True
            self._game._make_move(move)
            time_minmax["Making moves"] += (time.time() - t)  # Timing code
            t = time.time()  # Timing code
            new_moves = self._game._players[self._game._to_play]._avail_moves()
            time_minmax["Getting moves"] += (time.time() - t)  # Timing code
            t = time.time()  # Timing code
            x = self._game._is_over(new_moves, in_ai_moves=True)
            if x is not None:
                time_minmax["Checking over"] += (time.time() - t)  # Timing code
                t = time.time()  # Timing code
                score = 0
                if x == "White wins":
                    score = 999
                if x == "Black wins":
                    score = -999
                time_minmax["Getting score"] += (time.time() - t)  # Timing code
            else:
                Tsi = time.time()  # Timing code
                score, _ = self.__min_move(new_moves, a, b, depth, new_just_captured, biggest_depth)
                Ts.append(time.time() - Tsi)  # Timing code
            t = time.time()  # Timing code
            self._game._undo_move()
            results.append([move, score])
            time_minmax["Undoing moves"] += (time.time() - t)  # Timing code
            t = time.time()  # Timing code
            if score > best_score:
                best_score = score
                best_move = move
            if best_score >= b or score - self.__current_score > self.__threshold:
                break
            if best_score > a:
                a = best_score
            time_minmax["ab pruning"] += (time.time() - t)  # Timing code
        time_minmax["Sub total"] += time.time() - t0 - (sum(Ts))  # Timing code
        results.sort(key=lambda x: x[1], reverse=True)
        choice = random.randint(0, min(self._game._UI._MAXDIFFICULTY - self._difficulty, len(results) - 1))
        if self._difficulty == 4:
            return best_score, best_move
        return results[choice][1], results[choice][0]

    def __min_move(self, moves, a=-9999, b=9999, depth=0, just_captured=False, biggest_depth=[0]):
        # Minimax minimising function as in analysis section
        global time_minmax  # Timing code
        t0 = time.time()  # Timing code
        Ts = []  # Timing code
        results = []
        t = time.time()  # Timing code
        depth += 1
        if depth > self._max_depth and not just_captured:
            ts = time.time()  # Timing code
            s = self._game._get_score()
            time_minmax["Getting score"] += (time.time() - ts)  # Timing code
            return s, None
        best_score = 9999
        time_minmax["Start check"] += (time.time() - t)  # Timing code
        for move in moves:
            new_just_captured = False
            if self._game._board[move[1][0]][move[1][1]] != self._game._EMPTY:
                new_just_captured = True
            t = time.time()  # Timing code
            self._game._make_move(move)
            time_minmax["Making moves"] += (time.time() - t)  # Timing code
            t = time.time()  # Timing code
            new_moves = self._game._players[self._game._to_play]._avail_moves()
            time_minmax["Getting moves"] += (time.time() - t)  # Timing code
            t = time.time()  # Timing code
            x = self._game._is_over(new_moves, in_ai_moves=True)
            if x is not None:
                time_minmax["Checking over"] += (time.time() - t)  # Timing code
                t = time.time()  # Timing code
                if x == "White wins":
                    score = 999
                if x == "Black wins":
                    score = -999
                else:
                    score = 0
                time_minmax["Getting score"] += (time.time() - t)  # Timing code
            else:
                Tsi = time.time()  # Timing code
                score, _ = self.__max_move(new_moves, a, b, depth, new_just_captured, biggest_depth)
                Ts.append(time.time() - Tsi)  # Timing code
            t = time.time()  # Timing code
            self._game._undo_move()
            results.append([move, score])
            time_minmax["Undoing moves"] += (time.time() - t)  # Timing code
            t = time.time()  # Timing code
            if score < best_score:
                best_score = score
                best_move = move
            if best_score <= a or self.__current_score - score > self.__threshold:
                break
            if best_score < b:
                b = best_score
            time_minmax["ab pruning"] += (time.time() - t)  # Timing code
        time_minmax["Sub total"] += time.time() - t0 - (sum(Ts))  # Timing code
        results.sort(key=lambda x: x[1])
        choice = random.randint(0, min(self._game._UI._MAXDIFFICULTY - self._difficulty, len(results) - 1))
        if self._difficulty == 4:
            return best_score, best_move
        return results[choice][1], results[choice][0]


if __name__ == "__main__":
    print("This file just contains the Game and Player classes")
