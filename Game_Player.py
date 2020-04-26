from Pieces import *
import os


class Game:
    def __init__(self, UItype):
        self._EMPTY = "_"
        self._SIZE = 8
        self.__UI = UItype(self)
        self.__settings = self.__get_settings()
        if self.__settings[0] == "Y":
            self._players = [Player(self), AI(self)]
            if self.__settings[1] == "Y":
                self.__toPlay = 0
            else:
                self.__toPlay = 1
        else:
            self._players = [Player(self), Player(self)]
            self.__toPlay = 0
        self._board = self.__reset_board()
        for player in self._players:
            player._2nd_init()

    def __get_settings(self):
        s = []
        x = ""
        while x not in ["Y", "N"]:
            x = input("Do you want to play an AI? (Y/N): ").upper()
        s.append(x)
        if x == "Y":
            while x not in ["Y", "N"]:
                x = input("Do you want to go first? (Y/N): ").upper()
            else:
                x = None
        s.append(x)
        return s

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

    def __is_over(self):
        return False

    def __do_turn(self):
        moves = self._players[self.__toPlay]._avail_moves()
        move = (input("Enter your move, old position then new position: ")).split(" ")
        move1 = []
        for pos in move:
            try:
                move1.append([int(pos[1]) - 1, ord(pos[0].lower()) - 97])
            except (ValueError, IndexError):
                self.__do_turn()
                return
        flag = True
        for pos in move1:
            for coord in pos:
                if coord > 7 or coord < 0:
                    self.__do_turn()
                    return
        if move1 not in moves:
            self.__do_turn()
            return
        piece = self._board[move1[0][0]][move1[0][1]]
        self._board[move1[0][0]][move1[0][1]] = self._EMPTY
        piece._pos = move1[1]
        self._board[move1[1][0]][move1[1][1]] = piece

    def play_game(self):
        os.system("cls")
        self._display_board()
        print("White to play")
        while not self.__is_over():
            self.__do_turn()
            os.system("cls")
            self._display_board()
            self.__toPlay = (self.__toPlay + 1) % 2
            print(f"{['White', 'Black'][self.__toPlay]} to play")

    def _display_board(self):
        self.__UI._display_board()

    def __is_move_legal(self, move):
        return move in self._players[self.__toPlay]._avail_moves()


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
