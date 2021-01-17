from abc import ABC, abstractmethod
import os
from functools import partial
import itertools
import random
import time
from copy import deepcopy

from ttkthemes import themed_tk as t_tk
import tkinter as tk
from tkinter import font as tkfont
from PIL import Image, ImageTk

from threading import Thread

from database import Database

import chess
import chess.pgn
import io



class UI(ABC):
    # UI base class
    # Every implementation is unique to either GUI or Terminal
    def __init__(self, game):
        self._game = game

    @abstractmethod
    def _display_board(self):
        raise NotImplementedError

    @abstractmethod
    def _get_move(self, moves):
        raise NotImplementedError

    @abstractmethod
    def _get_game_settings(self):
        raise NotImplementedError

    @abstractmethod
    def _get_draw_decision(self, player):
        raise NotImplementedError

    @abstractmethod
    def _notify(self, message):
        raise NotImplementedError

    @abstractmethod
    def _end(self):
        raise NotImplementedError


class GUI(UI):
    def __init__(self, game):
        super().__init__(game)
        # Create GUI root
        self._root = t_tk.ThemedTk()
        self._root.resizable(False, False)
        self._root.title("Chess") # Title GUI
        self._size = 800 # Size of GUI in game
        self._win_size = 80 # Popup sizes
        self._black_square = "#B58863"
        self._white_sqaure = "#F0D9B5" # Hex colour codes for squares
        self._green_square = "#8AE678"
        self._black_purple_square = "#64535C"
        self._white_purple_square = "#827C85"
        self._prom_choice = None
        self._sprite_normal_percent = 65 / 100 # How big a sprite is compared to it's square
        self._sprite_big_percent = 85 / 100
        self._root.geometry(f"{self._win_size*6}x{self._win_size*4}")

        self._ready = None

        self._db = Database() # Database for games / accounts

        self._default_font = tkfont.Font(family="Calibri", size=18)

        # Initialise values
        self._accept_settings = False
        initial_difficulty = 3
        self._MAXDIFFICULTY = 5
        self._settings_choice = [0, 0, False, initial_difficulty, False]

        # Initialise dictionary containing the strings for all the different buttons and entries that have changing strings
        self._text_vars = {}
        self._text_vars["settings white"] = tk.StringVar()
        self._text_vars["settings white"].set("White: Player")
        self._text_vars["settings black"] = tk.StringVar()
        self._text_vars["settings black"].set("Black: Player")
        self._text_vars["settings flip"] = tk.StringVar()
        self._text_vars["settings flip"].set("Flip?: No")
        self._text_vars["settings difficulty"] = tk.StringVar()
        self._text_vars["settings difficulty"].set(f"AI difficulty: {initial_difficulty}/{self._MAXDIFFICULTY}")
        self._text_vars["settings fischer"] = tk.StringVar()
        self._text_vars["settings fischer"].set("Normal Chess")
        self._text_vars["to play"] = tk.StringVar()
        self._text_vars["to play"].set("White to play")
        self._text_vars["eval"] = tk.StringVar()
        self._text_vars["eval"].set(f"Evaluation: 0")

        self._text_vars["pgn name"] = tk.StringVar()

        self._text_vars["create username"] = tk.StringVar()
        self._text_vars["create pw"] = tk.StringVar()

        self._text_vars["delete username"] = tk.StringVar()
        self._text_vars["delete pw"] = tk.StringVar()

        self._text_vars["sign in username"] = tk.StringVar()
        self._text_vars["sign in pw"] = tk.StringVar()

        self._text_vars["player 1"] = tk.StringVar()
        self._text_vars["player 1"].set("Player 1: Not signed in")
        self._text_vars["player 1 option"] = tk.StringVar()
        self._text_vars["player 1 option"].set("Sign in")

        self._text_vars["player 2"] = tk.StringVar()
        self._text_vars["player 2"].set("Player 2: Not signed in")
        self._text_vars["player 2 option"] = tk.StringVar()
        self._text_vars["player 2 option"].set("Sign in")

        # Signed in players, not game._players objects
        self._player_1 = None
        self._player_2 = None

        # Create the images for the pieces for the buttons, for black and white, all the sizes etc. and store them in a dictionary
        self._root.sprites = {}
        self._root.sprites["None"] = ImageTk.PhotoImage(Image.open("Sprites/None.png"))
        for orientation in ['Normal', 'Flipped']:
            for colour in ["White", "Black"]:
                for piece in ["Rook", "Knight", "Bishop", "Queen", "King", "Pawn"]:
                    for i in range(3):
                        s = [self._sprite_normal_percent, self._sprite_big_percent, self._win_size / (self._size / (8 + 0)) * self._sprite_big_percent][i]
                        s1 = (int(self._size / (self._game._SIZE + 0) * s))
                        self._root.sprites[f"{piece} - {colour} - {['Normal', 'Big', 'Prom'][i]} - {orientation}"] = ImageTk.PhotoImage([Image.open(f"Sprites/{piece} - {colour}.png").resize((s1, s1), Image.ANTIALIAS), Image.open(f"Sprites/{piece} - {colour}.png").resize((s1, s1), Image.ANTIALIAS).transpose(Image.ROTATE_180)][orientation == "Flipped"])


        bg_colour = "#F2F2F2" # Hex code for background
        button_font = tkfont.Font(family="Calibri", size=36)

        # Creating buttons for the 3 main options
        self._initial_screen_frame = tk.Frame(self._root)
        tk.Grid.rowconfigure(self._root, 0, weight=1)
        tk.Grid.columnconfigure(self._root, 0, weight=1)
        self._initial_screen_frame.grid(row=0, column=0, sticky="nesw")
        self._current_frame = self._initial_screen_frame
        self._create_game_button = tk.Button(self._initial_screen_frame, text="Create Game", bg=bg_colour, font=button_font, command=self._start_game)
        tk.Grid.rowconfigure(self._initial_screen_frame, 0, weight=1)
        tk.Grid.columnconfigure(self._initial_screen_frame, 0, weight=1)
        self._create_game_button.grid(row=0, column=0, sticky="nesw")
        self._load_game_button = tk.Button(self._initial_screen_frame, text="Load Unfinished Game", bg=bg_colour, font=button_font, command=self._load_game_screen)
        tk.Grid.rowconfigure(self._initial_screen_frame, 1, weight=1)
        self._load_game_button.grid(row=1, column=0, sticky="nesw")
        self._accounts_button = tk.Button(self._initial_screen_frame, text="Accounts", bg=bg_colour, font=button_font, command=self._accounts_screen)
        tk.Grid.rowconfigure(self._initial_screen_frame, 2, weight=1)
        self._accounts_button.grid(row=2, column=0, sticky="nesw")

        # Initialising values for doing GUI functions from outside the main-thread -> see Game
        self._func = ""
        self._done_func = False
        self._func_return = None
        self._do_function()

    def _accounts_screen(self):
        # Screen containing the options within the account section

        # Switch out old screen for this one
        self._current_frame.grid_forget()
        self._root.geometry(f"{self._win_size*8}x{self._win_size*4}")
        self._accounts_frame = tk.Frame(self._root)
        self._accounts_frame.grid(row=0, column=0, sticky="nesw")
        self._current_frame = self._accounts_frame

        tk.Grid.rowconfigure(self._accounts_frame, 0, weight=1)
        tk.Grid.columnconfigure(self._accounts_frame, 0, weight=1)

        # Add buttons and labels for the options
        self._accounts_row_frames = []
        for i in range(5):
            f = tk.Frame(self._accounts_frame)
            f.grid(row=i, column=0, sticky="nesw")
            tk.Grid.rowconfigure(self._accounts_frame, i, weight=1)
            self._accounts_row_frames.append(f)

            tk.Grid.rowconfigure(f, 0, weight=1)
            tk.Grid.columnconfigure(f, 0, weight=1)

        self._accounts_create_button = tk.Button(self._accounts_row_frames[0], text="Create Account", command=self._create_account_screen, font=self._default_font)
        self._accounts_create_button.grid(row=0, column=0, sticky="nesw")

        self._accounts_delete_button = tk.Button(self._accounts_row_frames[0], text="Delete Account", command=self._delete_account_screen, font=self._default_font)
        self._accounts_delete_button.grid(row=0, column=1, sticky="nesw")

        tk.Grid.columnconfigure(self._accounts_row_frames[0], 1, weight=1)

        self._accounts_players_button = tk.Button(self._accounts_row_frames[1], text="Players", command=self._player_list_screen, font=self._default_font)
        self._accounts_players_button.grid(row=0, column=0, sticky="nesw")

        self._accounts_games_button = tk.Button(self._accounts_row_frames[1], text="Games", command=self._game_list_screen, font=self._default_font)
        self._accounts_games_button.grid(row=0, column=1, sticky="nesw")
        tk.Grid.columnconfigure(self._accounts_row_frames[1], 1, weight=1)

        self._accounts_player1_label = tk.Label(self._accounts_row_frames[2], textvariable=self._text_vars["player 1"], font=self._default_font)
        self._accounts_player1_label.grid(row=0, column=0, sticky="nesw")

        self._accounts_player1_button = tk.Button(self._accounts_row_frames[2], textvariable=self._text_vars["player 1 option"], command=self._player1_change, font=self._default_font)
        self._accounts_player1_button.grid(row=0, column=1, sticky="nesw")

        tk.Grid.columnconfigure(self._accounts_row_frames[2], 1, weight=1)

        self._accounts_player2_label = tk.Label(self._accounts_row_frames[3], textvariable=self._text_vars["player 2"], font=self._default_font)
        self._accounts_player2_label.grid(row=0, column=0, sticky="nesw")

        self._accounts_player2_button = tk.Button(self._accounts_row_frames[3], textvariable=self._text_vars["player 2 option"], command=self._player2_change, font=self._default_font)
        self._accounts_player2_button.grid(row=0, column=1, sticky="nesw")

        tk.Grid.columnconfigure(self._accounts_row_frames[3], 1, weight=1)

        self._accounts_done_button = tk.Button(self._accounts_row_frames[4], text="Done", command=self._initial_screen, font=self._default_font)
        self._accounts_done_button.grid(row=0, column=0, sticky="nesw")

    def _initial_screen(self):
        # Puts back the main screen in, whilst removing the old screen
        self._current_frame.grid_forget()
        self._root.geometry(f"{self._win_size*6}x{self._win_size*4}")
        self._initial_screen_frame.grid(row=0, column=0, sticky="nesw")
        self._current_frame = self._initial_screen_frame
        tk.Grid.rowconfigure(self._root, 0, weight=1)
        tk.Grid.columnconfigure(self._root, 0, weight=1)
        tk.Grid.columnconfigure(self._root, 1, weight=0)

    def _create_account_screen(self):
        # Called from the accounts screen
        # Removes old screen and puts in the new screen with entries for inputting a username and password + done and go back buttons
        self._create_account_frame = tk.Frame(self._root)
        self._current_frame.grid_forget()
        self._create_account_frame.grid(row=0, column=0, sticky="nesw")
        self._current_frame = self._create_account_frame
        usr_label = tk.Label(self._create_account_frame, text="Enter username:", font=self._default_font)
        usr_label.grid(row=0, column=0, sticky="nesw")

        tk.Grid.rowconfigure(self._create_account_frame, 0, weight=1)
        tk.Grid.columnconfigure(self._create_account_frame, 0, weight=1)

        self._create_username_entry = tk.Entry(self._create_account_frame, textvariable=self._text_vars["create username"], font=self._default_font)
        self._text_vars["create username"].set("")
        self._create_username_entry.grid(row=1, column=0, sticky="nesw")

        tk.Grid.rowconfigure(self._create_account_frame, 1, weight=1)

        pw_label = tk.Label(self._create_account_frame, text="Enter password (more than 4 characters):", font=self._default_font)
        pw_label.grid(row=2, column=0, sticky="nesw")

        self.__is_pw_show = False

        tk.Grid.rowconfigure(self._create_account_frame, 2, weight=1)

        self._create_pw_entry = tk.Entry(self._create_account_frame, show="*", textvariable=self._text_vars["create pw"], font=self._default_font)
        self._text_vars["create pw"].set("")
        self._create_pw_entry.grid(row=3, column=0, sticky="nesw")

        tk.Grid.rowconfigure(self._create_account_frame, 3, weight=1)

        self._create_final_frame = tk.Frame(self._create_account_frame)
        self._create_final_frame.grid(row=4, column=0, sticky="nesw")

        tk.Grid.rowconfigure(self._create_account_frame, 4, weight=1)


        self._create_back_button = tk.Button(self._create_final_frame, text="Go back", command=self._accounts_screen, font=self._default_font)
        self._create_back_button.grid(row=0, column=0, sticky="nesw")

        self._create_done_button = tk.Button(self._create_final_frame, text="Create account", command=self._try_account_creation, font=self._default_font)
        self._create_done_button.grid(row=0, column=1, sticky="nesw")

        self._create_toggle_pw_show_button = tk.Button(self._create_final_frame, text="Show/hide password", command=self.__flip_pw_show, font=self._default_font)
        self._create_toggle_pw_show_button.grid(row=0, column=2, sticky="nesw")

        tk.Grid.rowconfigure(self._create_final_frame, 0, weight=1)
        tk.Grid.columnconfigure(self._create_final_frame, 0, weight=1)
        tk.Grid.columnconfigure(self._create_final_frame, 1, weight=1)
        tk.Grid.columnconfigure(self._create_final_frame, 2, weight=1)

    def __flip_pw_show(self):
        # Flips the setting for showing the password as **** or the characters
        if self.__is_pw_show:
            s = "*"
        else:
            s = ""
        self.__is_pw_show = not self.__is_pw_show
        # Update the entries that use this setting
        try:
            self._create_pw_entry.configure(show=s)
        except:
            pass
        try:
            self._delete_pw_entry.configure(show=s)
        except:
            pass
        try:
            self._sign_in_pw_entry.configure(show=s)
        except:
            pass

    def _try_account_creation(self):
        # Takes the username and password from the entries and passes them to the database
        flag = True
        username = self._text_vars["create username"].get()
        pw = self._text_vars["create pw"].get()
        pwhash = self._get_hash(pw) # Hashses password for security
        if len(pw) <= 4: # Password must be at least 4 characters
            flag = False
        if flag:
            flag = self._db._add_player(username, pwhash)
        if flag:
            self._notify("Success")
            self._accounts_screen()
        else:
            self._notify("Invalid username/password")

    def _delete_account_screen(self):
        # Same as the account creation screen, but instead for deleting an existing account
        self._delete_account_frame = tk.Frame(self._root)
        self._current_frame.grid_forget()
        self._delete_account_frame.grid(row=0, column=0, sticky="nesw")
        self._current_frame = self._delete_account_frame
        usr_label = tk.Label(self._delete_account_frame, text="Enter username:", font=self._default_font)
        usr_label.grid(row=0, column=0, sticky="nesw")

        tk.Grid.rowconfigure(self._delete_account_frame, 0, weight=1)
        tk.Grid.columnconfigure(self._delete_account_frame, 0, weight=1)

        self._delete_username_entry = tk.Entry(self._delete_account_frame, textvariable=self._text_vars["delete username"], font=self._default_font)
        self._text_vars["delete username"].set("")
        self._delete_username_entry.grid(row=1, column=0, sticky="nesw")

        tk.Grid.rowconfigure(self._delete_account_frame, 1, weight=1)

        pw_label = tk.Label(self._delete_account_frame, text="Enter password:", font=self._default_font)
        pw_label.grid(row=2, column=0, sticky="nesw")

        self.__is_pw_show = False

        tk.Grid.rowconfigure(self._delete_account_frame, 2, weight=1)

        self._delete_pw_entry = tk.Entry(self._delete_account_frame, show="*", textvariable=self._text_vars["delete pw"], font=self._default_font)
        self._text_vars["delete pw"].set("")
        self._delete_pw_entry.grid(row=3, column=0, sticky="nesw")

        tk.Grid.rowconfigure(self._delete_account_frame, 3, weight=1)

        self._delete_final_frame = tk.Frame(self._delete_account_frame)
        self._delete_final_frame.grid(row=4, column=0, sticky="nesw")

        tk.Grid.rowconfigure(self._delete_account_frame, 4, weight=1)


        self._delete_back_button = tk.Button(self._delete_final_frame, text="Go back", command=self._accounts_screen, font=self._default_font)
        self._delete_back_button.grid(row=0, column=0, sticky="nesw")

        self._delete_done_button = tk.Button(self._delete_final_frame, text="Delete account", command=self._try_account_deletion, font=self._default_font)
        self._delete_done_button.grid(row=0, column=1, sticky="nesw")

        self._delete_toggle_pw_show_button = tk.Button(self._delete_final_frame, text="Show/hide password", command=self.__flip_pw_show, font=self._default_font)
        self._delete_toggle_pw_show_button.grid(row=0, column=2, sticky="nesw")

        tk.Grid.rowconfigure(self._delete_final_frame, 0, weight=1)
        tk.Grid.columnconfigure(self._delete_final_frame, 0, weight=1)
        tk.Grid.columnconfigure(self._delete_final_frame, 1, weight=1)
        tk.Grid.columnconfigure(self._delete_final_frame, 2, weight=1)

    def _get_hash(self, pw):
        # Returns the hash of a password, using the Database method
        return self._db._get_hash(pw)

    def _try_account_deletion(self):
        # Same as account creation, but deleting instead
        username = self._text_vars["delete username"].get()
        pw = self._text_vars["delete pw"].get()
        pwhash = self._get_hash(pw)
        flag = self._db._remove_player(username, pwhash)
        if flag:
            self._notify("Success")
            self._accounts_screen()
        else:
            self._notify("Invalid username/password")

    def _player_list_screen(self):
        # A screen which lists of the players
        w = self._win_size*8
        self._current_frame.grid_forget()
        self._player_list_frame = tk.Frame(self._root)
        self._player_list_frame.grid(row=0, column=0)

        tk.Grid.rowconfigure(self._player_list_frame, 0, weight=2)
        tk.Grid.columnconfigure(self._player_list_frame, 0, weight=1)
        tk.Grid.rowconfigure(self._player_list_frame, 1, weight=1)

        self._current_frame = self._player_list_frame

        # Get all of the players, excluding the "fake" players
        usernames = self._db._usernames()
        usernames.remove("Anon")
        usernames.remove("AI")

        c_frame = tk.Frame(self._player_list_frame)
        c_frame.grid(row=0, column=0, sticky="nesw")

        tk.Grid.rowconfigure(c_frame, 0, weight=1)
        tk.Grid.columnconfigure(c_frame, 0, weight=10)
        tk.Grid.columnconfigure(c_frame, 1, weight=1)

        canvas = tk.Canvas(c_frame, width=w)
        scroll = tk.Scrollbar(c_frame, orient="vertical", command=canvas.yview, width=24)

        frame = tk.Frame(canvas, width=w)
        frame.grid(row=0, column=0, sticky="nesw")

        tk.Grid.rowconfigure(canvas, 0, weight=1)
        tk.Grid.columnconfigure(canvas, 0, weight=1)

        tk.Grid.columnconfigure(frame, 0, weight=1)
        for i, usr in enumerate(usernames):
            # Each player has a button which takes the user to a screen about that player
            b = tk.Button(frame, text=f"{usr}", height=1, width=52, font=self._default_font, command=partial(self._player_details_screen, usr))
            b.grid(row=i, column=0, sticky="nesw")
            tk.Grid.rowconfigure(frame, i, weight=1)

        canvas.create_window(0, 0, anchor="nw", window=frame)
        canvas.update_idletasks()

        canvas.configure(scrollregion=canvas.bbox("all"), yscrollcommand=scroll.set)
        canvas.grid(row=0, column=0, sticky="nesw")
        scroll.grid(row=0, column=1, sticky="nesw")
        
        done_button = tk.Button(self._player_list_frame, text="Done", command=self._accounts_screen, font=self._default_font)
        done_button.grid(row=1, column=0, sticky="nesw")

    def _player_details_screen(self, usr):
        # Screen showing the stats about the selected player
        self._player_details_frame = tk.Frame(self._root)
        self._current_frame.grid_forget()
        self._current_frame = self._player_details_frame
        self._player_details_frame.grid(row=0, column=0, sticky="nesw")

        wins, draws, losses = self._db._player_stats(usr) # Get player stats from the Database

        # Labels showing the stats
        usr_label = tk.Label(self._player_details_frame, text=f"{usr}", font=self._default_font)
        usr_label.grid(row=0, column=0, sticky="nesw")

        wins_label = tk.Label(self._player_details_frame, text=f"Wins: {wins}", font=self._default_font)
        wins_label.grid(row=1, column=0, sticky="nesw")

        draws_label = tk.Label(self._player_details_frame, text=f"Draws: {draws}", font=self._default_font)
        draws_label.grid(row=2, column=0, sticky="nesw")

        losses_label = tk.Label(self._player_details_frame, text=f"Losses: {losses}", font=self._default_font)
        losses_label.grid(row=3, column=0, sticky="nesw")

        back_button = tk.Button(self._player_details_frame, text="Done", font=self._default_font, command=self._player_list_screen)
        back_button.grid(row=4, column=0, sticky="nesw")

        tk.Grid.columnconfigure(self._player_details_frame, 0, weight=1)
        tk.Grid.rowconfigure(self._player_details_frame, 0, weight=1)
        tk.Grid.rowconfigure(self._player_details_frame, 1, weight=1)
        tk.Grid.rowconfigure(self._player_details_frame, 2, weight=1)
        tk.Grid.rowconfigure(self._player_details_frame, 3, weight=1)
        tk.Grid.rowconfigure(self._player_details_frame, 4, weight=1)

    def _game_list_screen(self):
        # A screen with the list of played games in it, with an options to download them as .pgn files, or to load a .pgn to view
        w = self._win_size*8
        self._current_frame.grid_forget()
        self._game_list_frame = tk.Frame(self._root)
        self._game_list_frame.grid(row=0, column=0)

        tk.Grid.rowconfigure(self._game_list_frame, 0, weight=2)
        tk.Grid.columnconfigure(self._game_list_frame, 0, weight=1)
        tk.Grid.rowconfigure(self._game_list_frame, 1, weight=1)

        self._current_frame = self._game_list_frame

        games = self._db._game_details() # Get games from database
        
        c_frame = tk.Frame(self._game_list_frame)
        c_frame.grid(row=0, column=0, sticky="nesw")

        tk.Grid.rowconfigure(c_frame, 0, weight=1)
        tk.Grid.columnconfigure(c_frame, 0, weight=10)
        tk.Grid.columnconfigure(c_frame, 1, weight=1)

        canvas = tk.Canvas(c_frame, width=w)
        scroll = tk.Scrollbar(c_frame, orient="vertical", command=canvas.yview, width=24)

        frame = tk.Frame(canvas, width=w)
        frame.grid(row=0, column=0, sticky="nesw")

        tk.Grid.rowconfigure(canvas, 0, weight=1)
        tk.Grid.columnconfigure(canvas, 0, weight=1)

        tk.Grid.columnconfigure(frame, 0, weight=1)
        tk.Grid.columnconfigure(frame, 1, weight=1)
        f = tkfont.Font(family="Calibri", size=14)
        tot_width = 60
        width_2 = 10
        # Button for importing .pgn
        import_button = tk.Button(frame, text="Load and replay .pgn game (single game files)", command=self._load_pgn_screen, height=1, width=tot_width-width_2, font=f)
        import_button.grid(row=0, column=0, sticky="nesw")
        l = tk.Label(frame, text="Download?", font=f)
        l.grid(row=0, column=1, sticky="nesw")
        tk.Grid.rowconfigure(frame, 0, weight=1)
        for i, game in enumerate(games):
            # Buttons for each of the game, with the button to replay it, if it is finished, and the button to download the .pgn of the game
            moves = self._db._get_moves_from_id(game[0])
            b = tk.Button(frame, text=f"{game[0] + 1}: {game[1]} vs {game[2]}, {game[3]} {['(Click to replay)', ''][game[3]=='Unfinished']}", height=1, width=tot_width-width_2, font=f, command=[partial(self._start_game, moves=moves, replay_mode=True), 0][game[3]=='Unfinished'])
            b.grid(row=i+1, column=0, sticky="nesw")
            b1 = tk.Button(frame, text=".pgn", height=1, width=width_2, font=f, command=partial(self._download_pgn, moves, f"{game[1]} vs {game[2]}, {game[3]}.pgn"))
            b1.grid(row=i+1, column=1, sticky="nesw")
            tk.Grid.rowconfigure(frame, i+1, weight=1)
       

        canvas.create_window(0, 0, anchor="nw", window=frame)
        canvas.update_idletasks()

        canvas.configure(scrollregion=canvas.bbox("all"), yscrollcommand=scroll.set)
        canvas.grid(row=0, column=0, sticky="nesw")
        scroll.grid(row=0, column=1, sticky="nesw")
        
        done_button = tk.Button(self._game_list_frame, text="Done", command=self._accounts_screen, font=self._default_font)
        done_button.grid(row=1, column=0, sticky="nesw")

    def _download_pgn(self, moves, filename):
        # Called by above function, writes the moves as a .pgn with the filename specified
        moves = moves[0]
        board = chess.Board()
        moves = [f"{move[0][0]}{move[0][1]}{move[1][0]}{move[1][1]}" if len(move[1]) == 2 else f"{move[0][0]}{move[0][1]}{move[1][0]}{move[1][1]}{move[1][2].lower()}" for move in moves]
        pgn = io.StringIO(board.variation_san([chess.Move.from_uci(m) for m in moves]))
        game = str(chess.pgn.read_game(pgn))
        with open(filename, "w") as f:
            f.writelines(game)

    def _load_pgn_screen(self):
        # Screen used when importing a .pgn
        # Asks the user for the filename
        self._current_frame.grid_forget()
        self._load_pgn_frame = tk.Frame(self._root)
        self._load_pgn_frame.grid(row=0, column=0, sticky="nesw")
        self._current_frame = self._load_pgn_frame
        tk.Grid.rowconfigure(self._load_pgn_frame, 0, weight=1)
        tk.Grid.columnconfigure(self._load_pgn_frame, 0, weight=1)

        filename_label = tk.Label(self._load_pgn_frame, text="Enter the filename, without the .pgn", font=self._default_font)
        filename_label.grid(row=0, column=0, sticky="nesw")
        tk.Grid.rowconfigure(self._load_pgn_frame, 0, weight=1)

        self._text_vars["pgn name"].set("")
        filename_entry = tk.Entry(self._load_pgn_frame, textvariable=self._text_vars["pgn name"], font=self._default_font)
        filename_entry.grid(row=1, column=0, sticky="nesw")
        tk.Grid.rowconfigure(self._load_pgn_frame, 1, weight=1)

        bottom_frame = tk.Frame(self._load_pgn_frame)
        bottom_frame.grid(row=2, column=0, sticky="nesw")
        tk.Grid.rowconfigure(self._load_pgn_frame, 2, weight=1)

        tk.Grid.rowconfigure(bottom_frame, 0, weight=1)
        tk.Grid.columnconfigure(bottom_frame, 0, weight=1)

        back = tk.Button(bottom_frame, text="Go back", command=self._game_list_screen, font=self._default_font)
        back.grid(row=0, column=0, sticky="nesw")

        done = tk.Button(bottom_frame, text="Open", command=self._try_pgn_load, font=self._default_font)
        done.grid(row=0, column=1, sticky="nesw")
        tk.Grid.columnconfigure(bottom_frame, 1, weight=1)

    def _try_pgn_load(self):
        # Takes the filename and attempts to find the game and load it
        filename = f"{self._text_vars['pgn name'].get()}.pgn"
        try:
            with open(filename) as pgn:
                game = chess.pgn.read_game(pgn)
            old_moves = [str(move) for move in game.mainline_moves()]
            moves = []
            # Parses the moves from the .pgn into the format for the Game class
            for move in old_moves:
                if len(move) == 4:
                    moves.append([[move[0], int(move[1])], [move[2], int(move[3])]])
                else:
                    moves.append([[move[0], int(move[1])], [move[2], int(move[3]), move[4]]])
            moves = [moves]
        except:
            moves = []
        if moves:
            self._start_game(moves=moves, replay_mode=True) # Enters replay mode with the loaded moves
        else:
            self._notify("Could not find file")

    def _player1_change(self):
        # Either signs in or out player 1, depending on if there is already someone signed in
        if self._player_1 is not None:
            self._player_1 = None
            self._text_vars["player 1"].set("Player 1: Not signed in")
            self._text_vars["player 1 option"].set("Sign in")
        else:
            self._sign_in(1)

    def _sign_in(self, player):
        # Loads the screen for signing a player in, with entries for the username and password
        flag = True
        self._sign_in_frame = tk.Frame(self._root)
        self._current_frame.grid_forget()
        self._sign_in_frame.grid(row=0, column=0, sticky="nesw")
        self._current_frame = self._sign_in_frame

        usr_label = tk.Label(self._sign_in_frame, text="Enter username:", font=self._default_font)
        usr_label.grid(row=0, column=0, sticky="nesw")

        tk.Grid.rowconfigure(self._sign_in_frame, 0, weight=1)
        tk.Grid.columnconfigure(self._sign_in_frame, 0, weight=1)

        self._sign_in_username_entry = tk.Entry(self._sign_in_frame, textvariable=self._text_vars["sign in username"], font=self._default_font)
        self._text_vars["sign in username"].set("")
        self._sign_in_username_entry.grid(row=1, column=0, sticky="nesw")

        tk.Grid.rowconfigure(self._sign_in_frame, 1, weight=1)

        pw_label = tk.Label(self._sign_in_frame, text="Enter password:", font=self._default_font)
        pw_label.grid(row=2, column=0, sticky="nesw")

        self.__is_pw_show = False

        tk.Grid.rowconfigure(self._sign_in_frame, 2, weight=1)

        self._sign_in_pw_entry = tk.Entry(self._sign_in_frame, show="*", textvariable=self._text_vars["sign in pw"], font=self._default_font)
        self._text_vars["sign in pw"].set("")
        self._sign_in_pw_entry.grid(row=3, column=0, sticky="nesw")

        tk.Grid.rowconfigure(self._sign_in_frame, 3, weight=1)

        self._sign_in_final_frame = tk.Frame(self._sign_in_frame)
        self._sign_in_final_frame.grid(row=4, column=0, sticky="nesw")

        tk.Grid.rowconfigure(self._sign_in_frame, 4, weight=1)


        self._sign_in_back_button = tk.Button(self._sign_in_final_frame, text="Go back", command=self._accounts_screen, font=self._default_font)
        self._sign_in_back_button.grid(row=0, column=0, sticky="nesw")

        self._sign_in_done_button = tk.Button(self._sign_in_final_frame, text="Sign in", command=partial(self._sign_in_attempt, player), font=self._default_font)
        self._sign_in_done_button.grid(row=0, column=1, sticky="nesw")

        self._sign_in_toggle_pw_show_button = tk.Button(self._sign_in_final_frame, text="Show/hide password", command=self.__flip_pw_show, font=self._default_font)
        self._sign_in_toggle_pw_show_button.grid(row=0, column=2, sticky="nesw")

        tk.Grid.rowconfigure(self._sign_in_final_frame, 0, weight=1)
        tk.Grid.columnconfigure(self._sign_in_final_frame, 0, weight=1)
        tk.Grid.columnconfigure(self._sign_in_final_frame, 1, weight=1)
        tk.Grid.columnconfigure(self._sign_in_final_frame, 2, weight=1)


    def _sign_in_attempt(self, player):
        # Uses the database function to check if the username and password hash match
        username = self._text_vars["sign in username"].get()
        pw = self._text_vars["sign in pw"].get() # Pulls values from the entries
        pwhash = self._get_hash(pw)
        if username in [self._player_1, self._player_2]:
            self._notify("Already signed in")
        elif self._db._check_auth(username, pwhash):
            exec(f"self._player_{player} = username")
            self._text_vars[f"player {player}"].set(f"Player {player}: {eval(f'self._player_{player}')}")
            self._text_vars[f"player {player} option"].set("Sign out")
            self._accounts_screen() # If successful, go back to the accounts screen
        else:
            self._notify("Invalid username/password")

    def _player2_change(self):
        # Either signs in or out player 2, depending on if there is already someone signed in
        if self._player_2 is not None:
            self._player_2 = None
            self._text_vars["player 2"].set("Player 2: Not signed in")
            self._text_vars["player 2 option"].set("Sign in")
        else:
            self._sign_in(2)

    def _start_game(self, moves=[], replay_mode=False):
        # This function starts a game, either a new game, a loaded game or a replay of a game

        # Initialising values
        self.start = []
        self.finish = []

        self._quiting = False

        self._green_last_moves = []
        self._undoing = False
        self._drawing = False

        self._pos_buttons = []
        self._text_vars["eval"].set(f"Evaluation: 0")
        self._current_frame.grid_forget()
        x = 3 # Proportion of screen to give to the options vs board
        self._root.geometry(f"{int(self._size * (x+1)/x)}x{self._size}")
        self._game_frame = tk.Frame(self._root)
        self._game_frame.grid(row=0, column=0, sticky="nesw")
        self._current_frame = self._game_frame
        tk.Grid.rowconfigure(self._root, 0, weight=1)
        tk.Grid.columnconfigure(self._root, 0, weight=1)
        self._board_frame = tk.Frame(self._game_frame)
        self._board_frame.grid(row=0, column=1, sticky="nesw")
        self._options_frame = tk.Frame(self._game_frame)
        self._options_frame.grid(row=0, column=0, sticky="nesw")
        self._options_frame.grid_propagate(0)
        tk.Grid.rowconfigure(self._game_frame, 0, weight=1)
        tk.Grid.columnconfigure(self._game_frame, 0, weight=1)
        tk.Grid.columnconfigure(self._game_frame, 1, weight=x)

        wraplen = int(self._size/x)

        # Creates the buttons for the options, if in replay mode, much fewer options, e.g. no saving
        options_font = tkfont.Font(family="Calibri", size=24)
        tk.Grid.columnconfigure(self._options_frame, 0, weight=1)

        if not replay_mode:
            self._options_undo_move_button = tk.Button(self._options_frame, text="Undo last move", font=options_font, command=self.__set_undo, wraplength=wraplen)
            self._options_undo_move_button.grid(row=0, column=0, sticky="nesw")
            tk.Grid.rowconfigure(self._options_frame, 0, weight=1)

            self._options_save_game_button = tk.Button(self._options_frame, text="Save game", font=options_font, wraplength=wraplen, command=self._save_game)
            self._options_save_game_button.grid(row=1, column=0, sticky="nesw")
            tk.Grid.rowconfigure(self._options_frame, 1, weight=1)

            self._options_eval_label = tk.Label(self._options_frame, textvariable=self._text_vars["eval"], font=options_font)
            self._options_eval_label.grid(row=2, column=0, sticky="nesw")
            tk.Grid.rowconfigure(self._options_frame, 2, weight=1)

            self._options_suggested_move_button = tk.Button(self._options_frame, text="Show suggested move", font=options_font, wraplength=wraplen)
            self._options_suggested_move_button.grid(row=3, column=0, sticky="nesw")
            tk.Grid.rowconfigure(self._options_frame, 3, weight=1)

            self._options_draw_button = tk.Button(self._options_frame, text="Offer draw", font=options_font, wraplength=wraplen, command=self.__set_draw)
            self._options_draw_button.grid(row=4, column=0, sticky="nesw")
            tk.Grid.rowconfigure(self._options_frame, 4, weight=1)

            self._options_difficulty_button = tk.Button(self._options_frame, textvariable=self._text_vars["settings difficulty"], font=options_font, wraplength=wraplen, command=partial(self.__increment_setting, 3))
            self._options_difficulty_button.grid(row=5, column=0, sticky="nesw")
            tk.Grid.rowconfigure(self._options_frame, 5, weight=1)

            n = 7 # number of options created
        else:
            self._options_undo_move_button = tk.Button(self._options_frame, text="Last move", font=options_font, command=self._replay_undo, wraplength=wraplen)
            self._options_undo_move_button.grid(row=0, column=0, sticky="nesw")
            tk.Grid.rowconfigure(self._options_frame, 0, weight=1)

            self._options_next_move_button = tk.Button(self._options_frame, text="Next move", font=options_font, wraplength=wraplen, command=self._next_move)
            self._options_next_move_button.grid(row=1, column=0, sticky="nesw")
            tk.Grid.rowconfigure(self._options_frame, 1, weight=1)
            n = 3 # number of options created

        self._options_quit_button = tk.Button(self._options_frame, text="Quit", font=options_font, wraplength=wraplen, command=self._end_early)
        self._options_quit_button.grid(row=n-1, column=0, sticky="nesw")
        tk.Grid.rowconfigure(self._options_frame, n-1, weight=1)

        self._options_empty_label = tk.Label(self._options_frame)
        nt = 14 # used to weight the empty space label correctly
        self._options_empty_label.grid(row=n, column=0, sticky="nesw")
        tk.Grid.rowconfigure(self._options_frame, n, weight=(nt-n))

        # Creates the buttons for each of the squares on the board, with the correct colour and command
        tk.Grid.columnconfigure(self._board_frame, 0, weight=1)
        for r in range(self._game._SIZE):
            row_frame = tk.Frame(self._board_frame)
            row_frame.grid(row=r, column=0, sticky="nesw")
            tk.Grid.rowconfigure(self._board_frame, r, weight=5)
            tk.Grid.rowconfigure(row_frame, 0, weight=1)
            self._pos_buttons.append([])
            for c in range(self._game._SIZE):
                image = ""
                button = tk.Button(row_frame, image=image, bg=[self._black_square, self._white_sqaure][(r + c + 1) % 2], height=1, width=1, relief="flat", command=partial(self.select_piece, r, c), takefocus=False, activebackground=[self._black_square, self._white_sqaure][(r + c + 1) % 2], disabledforeground=[self._black_square, self._white_sqaure][(r + c + 1) % 2])
                self._pos_buttons[r].append(button)
                button.grid(row=0, column=c, sticky="nesw")
                tk.Grid.columnconfigure(row_frame, c, weight=1)

        if not replay_mode:
            self._get_game_settings() # Creates a popup to get the desired settings
        else:
            self._settings = [0, 0, False, False] # Settings in replay mode are known

        if moves: # If the game is not new
            self._ready = "Load" # Sends signal to the other thread
            while self._game._ready is None:
                time.sleep(0.2) # Wait for signal back
            if not replay_mode: # So if loading moves to continue from
                for move in moves:
                    # Parses the move, then plays it, for every move loaded
                    if len(move[1]) == 3:
                        new_move = [[int(move[0][1]) - 1, ord(move[0][0].lower()) - 97], [int(move[1][1]) - 1, ord(move[1][0].lower()) - 97, move[1][2]]]
                    else:
                        new_move = [[int(move[0][1]) - 1, ord(move[0][0].lower()) - 97], [int(move[1][1]) - 1, ord(move[1][0].lower()) - 97]]
                    self._game._make_move(new_move, main=True)
                self._ready = "Done Loading" # sends signal to other thread
            else:
                self._replay_moves = deepcopy(moves[0]) # Gets moves ready for the replay mode
                self._replay_moves_2 = []
                self._display_board()
                # Doesn't send signal to the other thread
        else:
            self._ready = "New" # Sends signal to the other thread

    def _next_move(self):
        # Used in replay mode, advances the replay by 1 move
        if self._replay_moves: # Checks there is a next move to play
            move = self._replay_moves.pop(0) # Gets move
            self._replay_moves_2.append(move) # Appends it in case it needs undoing
            if len(move[1]) == 3: # Checks if the move is a promotion
                new_move = [[int(move[0][1]) - 1, ord(move[0][0].lower()) - 97], [int(move[1][1]) - 1, ord(move[1][0].lower()) - 97, move[1][2]]]
            else:
                new_move = [[int(move[0][1]) - 1, ord(move[0][0].lower()) - 97], [int(move[1][1]) - 1, ord(move[1][0].lower()) - 97]]
            self._game._make_move(new_move, main=True) # Plays move
            self._display_board() # Update board
            self._green_last(new_move) # Update visuals

    def _replay_undo(self):
        # Used in replay mode to go back 1 move
        if self._replay_moves_2: # Checks there is a move to undo
            self._game._undo_move(main=True) # Undoes the move
            self._replay_moves.insert(0, self._replay_moves_2.pop()) # Puts the undone move back in the moves to play at the start
            self._display_board()
            self._green_last("Undo") # Updates visuals

    def _end_early(self):
        # Used when the quit button is pressed, quits of the game and back to the main menu
        self._game.over = "Quit"
        self._quiting = True # These 3 kick the other thread round to the beginning of the function again
        self._ready = "Done Loading"

    def _do_function(self):
        # Part of the executing functions from the other thread system
        has_another_part = ["_get_prom_choice", "_notify", "_get_draw_decision", "_finished_save"] # If it is one of these, don't set the done flag
        if self._func != "":
            com = self._func[:self._func.index("(")]
            exec(f"self.{self._func}") # Execute the desired function
            self._func = ""
            if com in has_another_part:
                pass
            else:
                self._done_func = True # Set the flag to done, for the other thread to continue
        self._root.after(5, self._do_function) # Recall this function so other function can be executed when needed

    def _update_eval(self):
        # Updates the evaluation label in the GUI
        score = self._game._get_score()
        self._text_vars["eval"].set(f"Evaluation: {['', '+'][score>0]}{round(score, 2)}")

    def _disable(self):
        # Disables all of the buttons (during the AI move), so they can't be pressed
        for r in self._pos_buttons:
            for c in r:
                c.configure(command=0)
        for c in self._options_frame.winfo_children():
            c.configure(state="disable")

    def _enable(self):
        # Reenables all of the disabled buttons
        for i, r in enumerate(self._pos_buttons):
            for j, b in enumerate(r):
                b.configure(command=partial(self.select_piece, i, j))
        for c in self._options_frame.winfo_children():
            c.configure(state="normal")

    def _save_game(self, result="Unfinished"):
        # Attempts to save the current game

        # Gets the players of the game
        if self._game._players[0].__class__.__name__ == "AI":
            p1 = "AI"
        else:
            p1 = [self._player_1, "Anon"][self._player_1 is None]
        if self._game._players[1].__class__.__name__ == "AI":
            p2 = "AI"
        else:
            p2 = [self._player_2, "Anon"][self._player_2 is None]
        flag = self._db._add_game(p1, p2, self._game._played, result) # Uses the database method to attempt a save
        if flag:
            if result == "Unfinished":
                self._notify("Game saved")
        return flag

    def _finished_save(self, result):
        # When a game is finished, this brings up a popup asking the user if they would like the save the game
        # If so, it attempts to save it
        self._save_dec = None
        pad_y_size = 5
        pad_inbetween_size = 5
        pad_x_size = 20
        self._save_win = tk.Toplevel()
        self._save_win.overrideredirect(True)
        self._save_win.attributes("-topmost", True)
        self._save_win.grab_set()
        frame = tk.Frame(self._save_win)
        frame.grid(row=0, column=0, sticky="nesw")
        tk.Grid.rowconfigure(self._save_win, 0, weight=1)
        tk.Grid.columnconfigure(self._save_win, 0, weight=1)
        tk.Grid.columnconfigure(frame, 0, weight=1)
        label = tk.Label(frame, text="Would you like to save?")
        label.grid(row=0, column=0, sticky="nesw", padx=(0, 0), pady=(pad_y_size, pad_inbetween_size))
        tk.Grid.rowconfigure(frame, 0, weight=3)
        tk.Grid.rowconfigure(frame, 1, weight=1)
        done_frame = tk.Frame(frame)
        done_frame.grid(row=1, column=0, sticky="nesw", padx=(pad_x_size, pad_x_size), pady=(pad_inbetween_size, 0))
        tk.Grid.rowconfigure(done_frame, 0, weight=1)
        tk.Grid.columnconfigure(done_frame, 0, weight=1)
        tk.Grid.columnconfigure(done_frame, 1, weight=1)
        yes_button = tk.Button(done_frame, text="Yes", command=partial(self.__save_done, dec=True, result=result))
        yes_button.grid(row=0, column=0, sticky="nesw")
        no_button = tk.Button(done_frame, text="No", command=partial(self.__save_done, dec=False, result=result))
        no_button.grid(row=0, column=1, sticky="nesw")
        popup_wait_thread = Thread(target=self.__save_2, daemon=True)
        popup_wait_thread.start()

    def __save_2(self):
        while self._save_dec is None:
            time.sleep(0.1)
        self._func = "_save_3()"

    # These functions are used as the function is called from the other thread, but the waiting for an answer must be in the other thread or else the GUI freezes

    def _save_3(self):
        self._save_win.grab_release()
        self._save_win.destroy()

    def __save_done(self, dec=None, result=""):
        self._save_dec = dec
        if self._save_dec:
            success = self._save_game(result=result)

    def _load_game_screen(self):
        # Screen used when loading a game to continue from
        w = self._win_size*8
        self._current_frame.grid_forget()
        self._root.geometry(f"{self._win_size*8}x{self._win_size*4}")
        self._game_load_frame = tk.Frame(self._root)
        self._game_load_frame.grid(row=0, column=0)

        tk.Grid.rowconfigure(self._game_load_frame, 0, weight=2)
        tk.Grid.columnconfigure(self._game_load_frame, 0, weight=1)
        tk.Grid.rowconfigure(self._game_load_frame, 1, weight=1)

        self._current_frame = self._game_load_frame

        games = self._db._game_details() # Get games from database
        games = filter(lambda game: game[3]=="Unfinished",games) # Only allow unfinished games

        c_frame = tk.Frame(self._game_load_frame)
        c_frame.grid(row=0, column=0, sticky="nesw")

        tk.Grid.rowconfigure(c_frame, 0, weight=1)
        tk.Grid.columnconfigure(c_frame, 0, weight=10)
        tk.Grid.columnconfigure(c_frame, 1, weight=1)

        canvas = tk.Canvas(c_frame, width=w)
        scroll = tk.Scrollbar(c_frame, orient="vertical", command=canvas.yview, width=24)

        frame = tk.Frame(canvas, width=w)
        frame.grid(row=0, column=0, sticky="nesw")

        tk.Grid.rowconfigure(canvas, 0, weight=1)
        tk.Grid.columnconfigure(canvas, 0, weight=1)

        tk.Grid.columnconfigure(frame, 0, weight=1)
        # Creates buttons for each of the games
        for i, game in enumerate(games):
            b = tk.Button(frame, text=f"{game[0] + 1}: {game[1]} vs {game[2]}, {game[3]}", height=1, width=52, font=self._default_font, command=partial(self._load_game, game[0]))
            b.grid(row=i, column=0, sticky="nesw")
            tk.Grid.rowconfigure(frame, i, weight=1)
       

        canvas.create_window(0, 0, anchor="nw", window=frame)
        canvas.update_idletasks()

        canvas.configure(scrollregion=canvas.bbox("all"), yscrollcommand=scroll.set)
        canvas.grid(row=0, column=0, sticky="nesw")
        scroll.grid(row=0, column=1, sticky="nesw")
        
        done_button = tk.Button(self._game_load_frame, text="Back", command=self._initial_screen, font=self._default_font)
        done_button.grid(row=1, column=0, sticky="nesw")

    def _load_game(self, GameID):
        # Gets the moves of the game and then starts a game with them
        moves = self._db._get_moves_from_id(GameID)[0]
        self._start_game(moves=moves)

    def _green_last(self, move=[]):
        # Sets the squares of the most recent move to green, and resets other green squares
        if move:
            flag = True
            if self._green_last_moves:
                self._reset_colours()
            if move == "Undo": # If the move is undo, the "move" to use if the previously played one
                self._green_last_moves.pop()
                if self._green_last_moves:
                    move = self._green_last_moves[-1]
                else:
                    flag = False
            else:
                self._green_last_moves.append(move)
            if flag:
                self._pos_buttons[self._game._SIZE - move[0][0] - 1][move[0][1]].configure(bg=["#ABA23A", "#CED26B"][(self._game._SIZE - move[0][0] - 1 + move[0][1] + 1) % 2])
                self._pos_buttons[self._game._SIZE - move[1][0] - 1][move[1][1]].configure(bg=["#ABA23A", "#CED26B"][(self._game._SIZE - move[1][0] - 1 + move[1][1] + 1) % 2])
        else:
            if self._green_last_moves:
                move = self._green_last_moves[-1]
                self._pos_buttons[self._game._SIZE - move[0][0] - 1][move[0][1]].configure(bg=["#ABA23A", "#CED26B"][(self._game._SIZE - move[0][0] - 1 + move[0][1] + 1) % 2])
                self._pos_buttons[self._game._SIZE - move[1][0] - 1][move[1][1]].configure(bg=["#ABA23A", "#CED26B"][(self._game._SIZE - move[1][0] - 1 + move[1][1] + 1) % 2])

    def _reset_colours(self):
        # Removes and green or purple colourings from the board
        for r in range(self._game._SIZE):
            for c in range(self._game._SIZE):
                self._pos_buttons[r][c].configure(bg=[self._black_square, self._white_sqaure][(r + c + 1) % 2])

    def select_piece(self, r, c):
        # Called by the buttons in the board, attempts to make a move from selected positions
        if self.start:
            if self.finish:
                self.start = []
                self.finish = []
            piece = self._game._board[self._game._SIZE - r - 1][c]
            flag = True
            if piece != self._game._EMPTY:
                if piece._player == self._game._players[self._game._to_play]:
                    flag = False
                    self.start = [self._game._SIZE - r - 1, c]
                    # When a new piece selected, highlight correct squares purple and enlarge the piece
                    self._display_board()
                    self._change_sprite_size(r, c)
                    self._purple_avail_moves(r, c)
            if flag:
                self.finish = [self._game._SIZE - r - 1, c]
                self._display_board()
        else:
            piece = self._game._board[self._game._SIZE - r - 1][c]
            if piece != self._game._EMPTY:
                if piece._player == self._game._players[self._game._to_play]:
                    self.start = [self._game._SIZE - r - 1, c]
                    # When a new piece selected, highlight correct squares purple and enlarge the piece
                    self._change_sprite_size(r, c)
                    self._purple_avail_moves(r, c)

    def _change_sprite_size(self, r, c):
        # Makes the desired sprite larger
        piece = self._game._board[self._game._SIZE - r - 1][c]
        if piece == self._game._EMPTY:
            image_name = "None"
        else:
            image_name = f"{piece.__class__.__name__} - {['White', 'Black'][self._game._players.index(piece._player)]} - Big - {['Normal', 'Flipped'][self._game._settings[2] and self._game._to_play == 1]}"
        button = self._pos_buttons[r][c]
        img = self._root.sprites[image_name]
        button.configure(image=img)

    def _purple_avail_moves(self, r, c):
        # Highlights the legal destinations for the selected piece purple
        piece = self._game._board[self._game._SIZE - r - 1][c]
        moves = piece._avail_moves(careifcheck=True)
        for move in moves:
            new_r, new_c = move[:2]
            self._pos_buttons[self._game._SIZE - new_r - 1][new_c].configure(bg=[self._white_purple_square, self._black_purple_square][(new_r + new_c + 1) % 2])

    def _display_board(self):
        # Updates the buttons in the board to have the correct sprite, e.g. if a piece just moved
        self._reset_colours()
        self._green_last()
        for r in range(self._game._SIZE):
            for c in range(self._game._SIZE):
                piece = self._game._board[self._game._SIZE - r - 1][c]
                if piece == self._game._EMPTY:
                    image_name = "None"
                else:
                    image_name = f"{piece.__class__.__name__} - {['White', 'Black'][self._game._players.index(piece._player)]} - Normal - {['Normal', 'Flipped'][self._game._settings[2] and self._game._to_play == 1]}"
                    #image_name = "None"  # blindfolded
                button = self._pos_buttons[r][c]
                button.configure(image=self._root.sprites[image_name])

    def __set_undo(self):
        # Sets the fact that the chosen move is to undo
        self._undoing = True
        self._drawing = False

    def __set_draw(self):
        # Sets the fact that the chosen move is to offer a draw
        self._drawing = True
        self._undoing = False

    def _get_move(self, moves):
        # Checks the selected piece and other selected squares to form a move
        while True:
            if self.start and self.finish: # 2 squares have been selected
                break
            elif self._undoing or self._drawing or self._quiting: # Checks if the move is to quit, draw or undo
                break
            else:
                time.sleep(0.1)
        # If it is a special move, return it
        if self._undoing:
            return ["undo"]
        if self._drawing:
            return ["draw"]
        if self._quiting:
            return ["quit"]
        # If not, parse the move, and return the move
        x = [[chr(self.start[1] + 97), self.start[0] + 1], [chr(self.finish[1] + 97), self.finish[0] + 1]]
        if [self.start, self.finish] in [[m[0], m[1][:2]] for m in moves]:
            i = [[m[0], m[1][:2]] for m in moves].index([self.start, self.finish])
            if len(moves[i][1]) == 3: # If it is a promotion, get the choice and return it
                p = self._game._do_GUI_func("_get_prom_choice()")
                x.append(p)
        # Reset the selected squares
        self.start = []
        self.finish = []
        return x

    def __set_prom_choice(self, choice):
        # Called by a button to set a variable
        self._prom_choice = choice

    def _get_prom_choice(self):
        # Creates a window for the user to select the piece they would like when promoting a pawn
        self._prom_win = tk.Toplevel()
        self._prom_win.overrideredirect(True)
        self._prom_win.attributes("-topmost", True)
        self._prom_win.title("Promotion choice")
        self._prom_win.grab_set()
        self._prom_win.geometry(f"{self._win_size}x{4*self._win_size}")
        frame = tk.Frame(self._prom_win)
        frame.grid(row=0, column=0, sticky="nesw")
        tk.Grid.rowconfigure(self._prom_win, 0, weight=1)
        tk.Grid.columnconfigure(self._prom_win, 0, weight=1)
        tk.Grid.columnconfigure(frame, 0, weight=1)
        # Creates the buttons for each of the pieces
        for i in range(4):
            button = tk.Button(
                frame, height=self._win_size, width=self._win_size,
                image=self._root.sprites[f"{['Queen', 'Rook', 'Bishop', 'Knight'][i]} - {['White', 'Black'][self._game._to_play]} - Prom - {['Normal', 'Flipped'][self._game._settings[2] and self._game._to_play == 1]}"], command=partial(self.__set_prom_choice, ['Q', 'R', 'B', 'K'][i]))
            button.grid(row=i, column=0, sticky="nesw")
            tk.Grid.rowconfigure(frame, i, weight=1)
        wait_thread = Thread(target=self.__prom_choice_func_2, daemon=True)
        wait_thread.start()

    def __prom_choice_func_2(self):
        # Waiting for a decision to be made
        while self._prom_choice is None:
            time.sleep(0.1)
        choice = self._prom_choice
        self._prom_choice = None
        self._func_return = choice
        self._func = "_prom_choice_func_3()"

    def _prom_choice_func_3(self):
        # Destroys the promotion window once a choice is made
        self._prom_win.grab_release()
        self._prom_win.destroy()

    def __increment_setting(self, i):
        # Cycles the settings in the settings popup, and in game for certain settings
        if 0 <= i <= 1:
            self._settings_choice[i] = (self._settings_choice[i] + 1) % (self._game._AI_TYPES+1)
            self._text_vars[f"settings {['white', 'black'][i]}"].set(f"{['White', 'Black'][i]}: {['Player', 'AI - Random', 'AI - MiniMax', 'AI - MCTS'][self._settings_choice[i]]}")
        elif i == 2:
            self._settings_choice[i] = not self._settings_choice[i] 
            self._text_vars["settings flip"].set(f"Flip?: {['No', 'Yes'][self._settings_choice[i]]}")
        elif i == 3:
            self._settings_choice[i] = (self._settings_choice[i] % self._MAXDIFFICULTY) + 1
            self._text_vars["settings difficulty"].set(f"AI difficulty: {self._settings_choice[i]}/{self._MAXDIFFICULTY}")
        elif i == 4:
            self._settings_choice[i] = not self._settings_choice[i]
            self._text_vars["settings fischer"].set(f"{['Normal Chess', 'Fischer Random Chess'][self._settings_choice[i]]}")
        else:
            print("Setting incrementing error")
            quit()
        self._game._settings = self._settings_choice

    def __settings_okay(self, win):
        # Once the settings before the game are chosen, destroy the settings window
        self._accept_settings = True
        win.grab_release()
        win.destroy()
        self._root.quit()

    def _get_game_settings(self):
        # Creates a popup window for the user to select settings in
        win = tk.Toplevel()
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.title("Player choice")
        win.grab_set()
        settings_font = tkfont.Font(family="Calibri", size=16)
        num_options = 6
        win.geometry(f"{3 * self._win_size}x{int((num_options * self._win_size) + (self._win_size * 1/3))}")
        frame = tk.Frame(win)
        frame.grid(row=0, column=0, sticky="nesw")
        tk.Grid.rowconfigure(win, 0, weight=1)
        tk.Grid.columnconfigure(win, 0, weight=1)
        tk.Grid.columnconfigure(frame, 0, weight=1)
        label1 = tk.Label(frame, height=self._win_size, width=3*self._win_size, text="Settings:\nClick to cycle", font=settings_font)
        label1.grid(row=0, column=0, sticky="nesw")
        # Buttons for each of the settings
        tk.Grid.rowconfigure(frame, 0, weight=3)
        for i in range(2):
            button = tk.Button(
                frame, height=self._win_size, width=3*self._win_size, textvariable=self._text_vars[f"settings {['white', 'black'][i]}"], command=partial(self.__increment_setting, i), font=settings_font)
            button.grid(row=i+1, column=0, sticky="nesw")
            tk.Grid.rowconfigure(frame, i+1, weight=3)
        button1 = tk.Button(frame, height=self._win_size, width=3*self._win_size, textvariable=self._text_vars["settings flip"], command=partial(self.__increment_setting, 2), font=settings_font)
        button1.grid(row=3, column=0, sticky="nesw")
        tk.Grid.rowconfigure(frame, 3, weight=3)
        button2 = tk.Button(frame, height=self._win_size, width=3*self._win_size, textvariable=self._text_vars["settings difficulty"], command=partial(self.__increment_setting, 3), font=settings_font)
        button2.grid(row=4, column=0, sticky="nesw")
        tk.Grid.rowconfigure(frame, 4, weight=3)
        button3 = tk.Button(frame, height=self._win_size, width=3*self._win_size, textvariable=self._text_vars["settings fischer"], command=partial(self.__increment_setting, 4), font=settings_font)
        button3.grid(row=5, column=0, sticky="nesw")
        tk.Grid.rowconfigure(frame, 5, weight=3)
        okay_button = tk.Button(frame, height=int(self._win_size / 3), width=3*self._win_size, text="Done", command=partial(self.__settings_okay, win), font=settings_font)
        okay_button.grid(row=num_options, column=0, sticky="nesw")
        tk.Grid.rowconfigure(frame, num_options, weight=1)
        win.mainloop()
        return self._settings_choice

    def _popup(self, message, yes_no=False):
        # Generic popup to display a message, with a done button to close it
        if yes_no:
            self._popup_dec = None
        pad_y_size = 5
        pad_inbetween_size = 5
        pad_x_size = 20
        self.__popup_done_var = False
        self._popup_win = tk.Toplevel()
        self._popup_win.overrideredirect(True)
        self._popup_win.attributes("-topmost", True)
        self._popup_win.grab_set()
        frame = tk.Frame(self._popup_win)
        frame.grid(row=0, column=0, sticky="nesw")
        tk.Grid.rowconfigure(self._popup_win, 0, weight=1)
        tk.Grid.columnconfigure(self._popup_win, 0, weight=1)
        tk.Grid.columnconfigure(frame, 0, weight=1)
        label = tk.Label(frame, text=message)
        label.grid(row=0, column=0, sticky="nesw", padx=(0, 0), pady=(pad_y_size, pad_inbetween_size))
        tk.Grid.rowconfigure(frame, 0, weight=3)
        tk.Grid.rowconfigure(frame, 1, weight=1)
        if yes_no == False:
            okay_button = tk.Button(frame, text="Done", command=partial(self.__popup_done))
            okay_button.grid(row=1, column=0, sticky="nesw", padx=(pad_x_size, pad_x_size), pady=(pad_inbetween_size, 0))
        else:
            done_frame = tk.Frame(frame)
            done_frame.grid(row=1, column=0, sticky="nesw", padx=(pad_x_size, pad_x_size), pady=(pad_inbetween_size, 0))
            tk.Grid.rowconfigure(done_frame, 0, weight=1)
            tk.Grid.columnconfigure(done_frame, 0, weight=1)
            tk.Grid.columnconfigure(done_frame, 1, weight=1)
            yes_button = tk.Button(done_frame, text="Yes", command=partial(self.__popup_done, dec=True))
            yes_button.grid(row=0, column=0, sticky="nesw")
            no_button = tk.Button(done_frame, text="No", command=partial(self.__popup_done, dec=False))
            no_button.grid(row=0, column=1, sticky="nesw")
        popup_wait_thread = Thread(target=self.__popup_2, daemon=True)
        popup_wait_thread.start()

    def __popup_2(self):
        # Waiting for done to be pressed
        while not self.__popup_done_var:
            time.sleep(0.1)
        self._func = "_popup_3()"

    def _popup_3(self):
        self._popup_win.grab_release()
        self._popup_win.destroy()

    # More helper functions for the popup for the same reasons as before with the threading

    def __popup_done(self, dec=None):
        self.__popup_done_var = True
        if dec is not None:
            self._popup_dec = dec

    def _notify(self, message, yes_no=False):
        # Just calls the popup method, exists as _notify is a standard between GUI and Terminal
        self._popup(message, yes_no=yes_no)

    def _get_draw_decision(self, player):
        # Creates a popup to get a yes or no from the player on whether they would like to draw
        self._draw_dec = None
        if self._game._players[player].__class__.__name__ == "AI":
            return False
        self._draw_win = tk.Toplevel()
        self._draw_win.overrideredirect(True)
        self._draw_win.attributes("-topmost", True)
        self._draw_win.grab_set()
        frame = tk.Frame(self._draw_win)
        frame.grid(row=0, column=0, sticky="nesw")
        tk.Grid.rowconfigure(self._draw_win, 0, weight=1)
        tk.Grid.columnconfigure(self._draw_win, 0, weight=1)
        label = tk.Label(frame, text=f"{['White', 'Black'][player]}, would you like to draw?")
        label.grid(row=0, column=0, sticky="nesw")
        yes_button = tk.Button(frame, text="Yes", command=partial(self._draw_decider, True))
        yes_button.grid(row=1, column=0, sticky="nesw")
        no_button = tk.Button(frame, text="No", command=partial(self._draw_decider, False))
        no_button.grid(row=2, column=0, sticky="nesw")

        tk.Grid.rowconfigure(frame, 0, weight=1)
        tk.Grid.rowconfigure(frame, 1, weight=1)
        tk.Grid.rowconfigure(frame, 2, weight=1)
        tk.Grid.columnconfigure(frame, 0, weight=1)

        wait_thread = Thread(target=self._draw_2, daemon=True)
        wait_thread.start()

    def _draw_decider(self, val):
        # Set the variable to either true for false, depending on the choice
        self._draw_dec = val
        self._func_return = self._draw_dec

    def _draw_2(self):
        # Waiting for a decision to be made
        while self._draw_dec is None:
            time.sleep(0.1)
        self._func = "_draw_3()"

    def _draw_3(self):
        self._draw_win.grab_release()
        self._draw_win.destroy()

    def _end(self):
        # Ends the current game, going back to the main menu
        self._current_frame.grid_forget()
        self._ready = None
        self._root.geometry(f"{self._win_size*6}x{self._win_size*4}")
        self._initial_screen_frame.grid(row=0, column=0, sticky="nesw")
        self._current_frame = self._initial_screen_frame
        tk.Grid.rowconfigure(self._root, 0, weight=1)
        tk.Grid.columnconfigure(self._root, 0, weight=1)
        tk.Grid.columnconfigure(self._root, 1, weight=0)

    def _quit(self):
        # Quits out of the program
        self._root.destroy()


class Terminal(UI):
    def __init__(self, game):
        super().__init__(game)
        self._settings_choice = self._get_game_settings()
        self._ready = "New"

    def _display_board(self):
        # Prints the board to the terminal
        board = self._game._board
        x = "  "
        for i in range(len(board)):
            x += chr(65 + i) + " "
        x += "\n"
        for i, row in enumerate(board[::-1]):
            y = ""
            for element in row:
                if element == self._game._EMPTY:
                    y += element + " "
                else:
                    y += element._symbol + " "
            x += str(len(board) - i) + " " + y +str(len(board) - i) + "\n"
        x += "  "
        for i in range(len(board)):
            x += chr(65 + i) + " "
        x += "\n"
        print(x)

    def _get_move(self, moves):
        # Asks the user to input a move
        return input("Enter your move, old position then new position: ").split(" ")

    def _get_game_settings(self):
        # Gets the user to enter the settings by typing them
        s = []
        for i in range(2):
            x = ""
            while x not in ["player", "random", "minimax", "mcts"]:
                x = input(f"{['White', 'Black'][i]} type (Player, Random, Minimax, MCTS): ").lower()
            s.append(["player", "random", "minimax", "mcts"].index(x))
        s.append(False)  # flip is always false for Terminal
        s.append(5) # Difficulty is always 5 in Terminal
        s.append(False)  # fischer cannot be played in terminal
        return s

    def _notify(self, message):
        # Standard interface function, as in GUI, just prints the message
        print(message)

    def _get_draw_decision(self, player):
        # Asks the user if they would like to draw
        x = ""
        while x not in ['Y', 'N']:
            x = input(f"{['White', 'Black'][player]}, would you like to draw? (Y/N): ").upper()
        return x == "Y"

    def _end(self):
        # Another standard function, since you can't play multiple games in a row in Terminal, does nothing
        pass


if __name__ == "__main__":
    print("This file just contains the UI classes")
