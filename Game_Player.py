from Pieces import *
import os
from copy import deepcopy
import time
import random
from statistics import mean
from collections import Counter
import chess # to read polyglot opening book
import chess.polyglot


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
        # heuristic constants
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

        self._EMPTY = "_"
        self._opening_board = chess.Board()
        self._AI_TYPES = 3
        self._SIZE = 8
        self._UI = UItype(self)
        self._settings = self.__get_settings()
        self._undo_stack = []
        self._played = []
        self._mutual = False
        self._repetitions = []
        self._move_count = 0
        self._toPlay = 0
        if self._settings[0] == 0:
            player_1 = Player(self)
        else:
            player_1 = AI(self, ["Random", "MiniMax", "MCTS"][self._settings[0] - 1])
        if self._settings[1] == 0:
            player_2 = Player(self)
        else:
            player_2 = AI(self, ["Random", "MiniMax", "MCTS"][self._settings[1] - 1])
        self._players = [player_1, player_2]
        self._board = self.__reset_board()
        for player in self._players:
            player._2nd_init()

    def __get_settings(self):
        return self._UI._settings_choice

    def __reset_board(self):
        b = [[self._EMPTY for _ in range(self._SIZE)] for __ in range(self._SIZE)]
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

    def _is_draw(self, p_moves, in_ai_moves=False):
        stalemate = p_moves == [] and not self._players[self._toPlay]._in_check()# or (self._players[1 - self._toPlay]._avail_moves() == [] and not self._players[1 - self._toPlay]._in_check())

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
        elif x >= 3 and not in_ai_moves:
                if self._UI._get_draw_decision(self._toPlay):
                    repetition = self._UI._get_draw_decision(1 - self._toPlay)
        move_limit = False
        if self._move_count >= 75:
            move_limit = True
        elif self._move_count >= 50 and not in_ai_moves:
            if self._UI._get_draw_decision(self._toPlay):
                move_limit = self._UI._get_draw_decision(1 - self._toPlay)
        agreement = self._mutual
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
        if self._players[self._toPlay]._in_checkmate(p_moves):
            return f"{['White', 'Black'][1 - self._toPlay]} wins"
        if self._players[1 - self._toPlay]._in_checkmate(p_moves):
            return f"{['White', 'Black'][self._toPlay]} wins"
        x = self._is_draw(p_moves, in_ai_moves)
        if x:
            return x
        return None

    def _make_move(self, move, main=False):
        if main:
            x = ""
            if len(move[1]) == 3:
                x = move[1][2]
            self._opening_board.push_san(f"{chr(move[0][1] + 97)}{move[0][0]+1}{chr(move[1][1] + 97)}{move[1][0]+1}{x}")
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
                if prom.__class__.__name__ == "Rook":
                    prom._moved = True
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
            old_pos = deepcopy(piece._pos)
            piece._pos = move[1][:2]
        for p in piece._player._pieces:
            if p.__class__.__name__ == "Pawn":
                p._just_double = False
        if piece.__class__.__name__ == "Pawn":
            if abs(old_pos[0] - move[1][0]) == 2:
                piece._just_double = True
        self._move_count += 1
        self._toPlay = (self._toPlay + 1) % 2

    def _undo_move(self, main=False):
        if main:
            self._opening_board.pop()
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
            self._undo_move(main=True)
        elif move == "draw":
            if self._UI._get_draw_decision(1 - self._toPlay):
                self._mutual = True
        else:
            self._make_move(move, main=True)
            if self._UI.__class__.__name__ == "GUI":
                self._UI._green_last(move)

    def play_game(self):
        global time_pieces, time_pawn
        time_pieces = {"Pawn": 0, "King": 0, "Queen": 0, "Rook": 0, "Knight": 0, "Bishop": 0}##########################################################
        time_pawn = {"Standard": 0, "Double": 0, "Diagonal": 0, "Promotion": 0, "Check": 0, "Removing": 0}
        times = []
        over = None
        p_moves = self._players[self._toPlay]._avail_moves()
        self._display_board()
        # self._UI._notify(f"{['White', 'Black'][self._toPlay]} to play")
        while over is None:
            t0 = time.time()
            bn = [[p if type(p) == str else p._symbol for p in row] for row in self._board]
            self._repetitions.append(StringList([bn, deepcopy(p_moves)]))
            self.__do_turn(p_moves)
            #print(self._played)
            if self._UI.__class__.__name__ == "GUI":
                self._UI._text_vars["to play"].set(f"{['White', 'Black'][self._toPlay]} to play")
            self._display_board()
            print(f"Score = {round(self._get_score(), 2)}")
            # self._UI._notify(f"{['White', 'Black'][self._toPlay]} to play")
            p_moves = self._players[self._toPlay]._avail_moves()
            over = self._is_over(p_moves)
            times.append(time.time() - t0)
            # print(f"Curr.: {round(time.time() - t0, 3)}s\nAvg.: {round(mean(times), 3)}s\nTot.: {round(sum(times), 3)}s")
        self._UI._notify(over)
        self._UI._end()

    def _display_board(self):
        self._UI._display_board()

    def __is_move_legal(self, move):
        return move in self._players[self._toPlay]._avail_moves()

    def _get_score(self, moves=[]):
        score = 0
        #vals = {"Pawn": 1, "Bishop": 3, "Knight": 3, "Rook": 5, "Queen": 9, "King": 999}
        for i in range(2):
            #moves = self._players[(self._toPlay + i) % 2]._avail_moves(careifcheck=True)
            for piece in self._players[i]._pieces:
                if not piece._taken:
                    name = piece.__class__.__name__
                    if name == "Pawn":
                        dis = abs(piece._pos[0] - piece._start_row) + 1
                        val = 1 * self.__pawn_value_adjustments[dis][piece._pos[1]]
                    if name == "King":
                        val = 999
                    if name == "Bishop":
                        dis = abs(piece._pos[0] - [0, 7][i])
                        #num = sum([1 for move in moves if move[0] == piece._pos])
                        val = 3# + self.__rook_covering_adjustments[int(num)]
                    if name == "Knight":
                        dis = abs(piece._pos[0] - [0, 7][i])
                        val = 3# * self.__knight_value_adjustments[dis][piece._pos[1]]
                    if name == "Rook":
                        dis = abs(piece._pos[0] - [0, 7][i])
                        #num = sum([1 for move in moves if move[0] == piece._pos and move[1][0] != [0, 7][i]])
                        val = 5# + self.__rook_covering_adjustments[int(num)]
                    if name == "Queen":
                        dis = abs(piece._pos[0] - [0, 7][i])
                        #self.__knight_value_adjustments[move[1][0]][move[1][1]]
                        #num = sum([1 for move in moves if move[0] == piece._pos and move[1][0] != [0, 7][i]])
                        val = 9# + self.__queen_covering_adjustments[int(num)]
                    if i == 0:
                        score += val
                    else:
                        score -= val
        return score


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
        global time_pieces  # Timing code
        moves = []
        for piece in self._pieces:
            t = time.time()  # Timing code
            p_moves = piece._avail_moves(careifcheck)
            time_pieces[piece.__class__.__name__] += time.time() - t  # Timing code
            for move in p_moves:
                moves.append([piece._pos, move])
        return moves

    def _get_move(self, moves):
        move = self._game._UI._get_move(moves)
        if move[0] in ["undo", "draw"]:
            return move[0]
        move1 = []
        for pos in move[:2]:
            try:
                move1.append([int(pos[1]) - 1, ord(pos[0].lower()) - 97])
            except (ValueError, IndexError) as e:
                self._game._UI._notify(f"Value / Index Error, {e}")
                return self._get_move(moves)
        for pos in move1:
            for coord in pos:
                if coord > 7 or coord < 0:
                    self._game._UI._notify("Out of bounds")
                    return self._get_move(moves)
        if len(move) == 3:
            move1[1].append(move[2].upper())
        if move1 not in moves:
            #self._game._UI._notify("Invalid move")
            return self._get_move(moves)
        return move1

    def _in_check(self):
        king_pos = self._pieces[[p.__class__.__name__ for p in self._pieces].index("King")]._pos
        opponent_pieces = self._game._players[1-self._game._players.index(self)]._pieces
        for piece in opponent_pieces:
            if not piece._taken:
                if piece._is_takeable(king_pos):
                    return True
        return False
        #return self._pieces[[p.__class__.__name__ for p in self._pieces].index("King")]._pos in [m[1][:2] for m in self._game._players[1 - self._game._players.index(self)]._avail_moves(False)]

    def _in_checkmate(self, p_moves=None):
        if p_moves is None:
            p_moves = self._avail_moves()
        return p_moves == [] and self._in_check()

    def __notify(self, message):
        self._UI._notify(message)


class AI(Player):
    def __init__(self, game, ai_type="Random"):
        super().__init__(game)
        #self._type = ["Random", "MiniMax", "MCTS"][3-1]
        self._type = ai_type
        self._max_depth = 3
        self._playouts = 2

    def _get_move(self, moves):
        if self._game._UI.__class__.__name__ == "GUI":
            self._game._UI._disable()
        try:
            with chess.polyglot.open_reader("C:/Local Stuff/poly16/books/elo2500.bin") as reader:
                for entry in reader.find_all(self._game._opening_board):
                    move = str(entry.move)
                    break
            x = [[int(move[1])-1, ord(move[0])-97], [int(move[3])-1, ord(move[2])-97]]
            if self._game._UI.__class__.__name__ == "GUI":
                self._game._UI._enable()
            return x
        except:
            global time_minmax, time_pieces, time_pawn
            time_minmax = {"Start check": 0, "Making moves": 0, "Getting moves": 0, "Checking over": 0,
                            "Undoing moves": 0, "ab pruning": 0, "Getting score": 0, "Sub total": 0}
            time_pieces = {"Pawn": 0, "King": 0, "Queen": 0, "Rook": 0, "Knight": 0, "Bishop": 0}
            time_pawn = {"Standard": 0, "Double": 0, "Diagonal": 0,
                        "Promotion": 0, "Check": 0, "Removing": 0}
            if self._type == "MiniMax":
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
                move = self.__MCTS(moves, self._game._players.index(self) == 0)
                time_total = time.time() - t0
            else:
                move = random.choice(moves)
            try:  
                if self._type == "MiniMax":
                    print()
                    print(f"AI move took {time_total}s")
                    print(f"Best score = {round(best_score, 2)}")
                    """
                    s = sum(time_minmax.values()) - time_minmax["Sub total"]
                    p_sum = sum(time_pieces.values())
                    pawn_sum = sum(time_pawn.values())
                    for section, s_t in time_minmax.items():
                        print(f"- {section}: {round(s_t, 4)}s = {round((s_t / time_total) * 100, 3)}% = {round((s_t / s) * 100, 3)}%")
                        if section == "Getting moves":
                            for piece_type, t in time_pieces.items():
                                print(f"- - {piece_type}: {round(t, 4)}s = {round((t / p_sum) * 100, 3)}%")
                                if piece_type == "Pawn":
                                    for pawn_part, pawn_t in time_pawn.items():
                                        print(f"- - - {pawn_part}: {round(pawn_t, 4)}s = {round((pawn_t / pawn_sum) * 100, 3)}%")          
                        #print(f"- - All: {round(p_sum, 4)}s = {round((p_sum / (2 * time_getting_moves)) * 100, 3)}%")
                        """
                if self._type == "MCTS":
                    print()
                    print(f"AI move took {time_total}s") 
            except:
                print("Timing crashed")
            if self._game._settings[3]:
                pass
                """
                totype = f"{chr(move[0][1] + 97)}{move[0][0]+1}{chr(move[1][1] + 97)}{move[1][0]+1}"
                print(totype)
                typewrite(totype)
                """
            if self._game._UI.__class__.__name__ == "GUI":
                self._game._UI._enable()
            return move

    def _get_prom_choice(self):
        return 3

    def __playout(self):
        count = 0
        moves = self._game._players[self._game._toPlay]._avail_moves()
        x = self._game._is_over(moves, True)
        while x is None:
            move = random.choice(moves)
            self._game._make_move(move)
            moves = self._game._players[self._game._toPlay]._avail_moves()
            count += 1
            x = self._game._is_over(moves, True)
        if x == "White wins":
            y = 1
        elif x == "Black wins":
            y = -1
        else:
            y = 0
        for i in range(count):
            self._game._undo_move()
        return y

    def __MCTS(self, moves, maximise):
        scores = []
        for move in moves:
            total = 0
            self._game._make_move(move)
            for i in range(self._playouts):
                total += self.__playout()
            scores.append(total)
            self._game._undo_move()
        print(scores)
        return moves[scores.index([min(scores), max(scores)][maximise])]

    def __max_move(self, moves, a=-9999, b=9999, depth=0):
        global time_minmax  # Timing code
        t0 = time.time()  # Timing code
        Ts = []  # Timing code
        t = time.time()  # Timing code
        depth += 1
        if depth > self._max_depth:
            ts = time.time()  # Timing code
            s = self._game._get_score(moves=moves)
            time_minmax["Getting score"] += (time.time() - ts)  # Timing code
            return s, None
        best_score = -9999
        time_minmax["Start check"] += (time.time() - t)  # Timing code
        for move in moves:
            t = time.time()  # Timing code
            self._game._make_move(move)
            time_minmax["Making moves"] += (time.time() - t)  # Timing code
            t = time.time()  # Timing code
            new_moves = self._game._players[self._game._toPlay]._avail_moves()
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
                score, _ = self.__min_move(new_moves, a, b, depth)
                Ts.append(time.time() - Tsi)  # Timing code
            t = time.time()  # Timing code
            self._game._undo_move()
            time_minmax["Undoing moves"] += (time.time() - t)  # Timing code
            t = time.time()  # Timing code
            if score > best_score:
                best_score = score
                best_move = move
            if best_score >= b:
                break
            if best_score > a:
                a = best_score
            time_minmax["ab pruning"] += (time.time() - t)  # Timing code
        time_minmax["Sub total"] += time.time() - t0 - (sum(Ts))  # Timing code
        return best_score, best_move

    def __min_move(self, moves, a=-9999, b=9999, depth=0):
        global time_minmax  # Timing code
        t0 = time.time()  # Timing code
        Ts = []  # Timing code
        t = time.time()  # Timing code
        depth += 1
        if depth > self._max_depth:
            ts = time.time()  # Timing code
            s = self._game._get_score()
            time_minmax["Getting score"] += (time.time() - ts)  # Timing code
            return s, None
        best_score = 9999
        time_minmax["Start check"] += (time.time() - t)  # Timing code
        for move in moves:
            t = time.time()  # Timing code
            self._game._make_move(move)
            time_minmax["Making moves"] += (time.time() - t)  # Timing code
            t = time.time()  # Timing code
            new_moves = self._game._players[self._game._toPlay]._avail_moves()
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
                score, _ = self.__max_move(new_moves, a, b, depth)
                Ts.append(time.time() - Tsi)  # Timing code
            t = time.time()  # Timing code
            self._game._undo_move()
            time_minmax["Undoing moves"] += (time.time() - t)  # Timing code
            t = time.time()  # Timing code
            if score < best_score:
                best_score = score
                best_move = move
            if best_score <= a:
                break
            if best_score < b:
                b = best_score
            time_minmax["ab pruning"] += (time.time() - t)  # Timing code
        time_minmax["Sub total"] += time.time() - t0 - (sum(Ts))  # Timing code
        return best_score, best_move


if __name__ == "__main__":
    print("This file just contains the Game and Player classes")
    #usage()
