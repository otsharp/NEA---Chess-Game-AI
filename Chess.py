from pathlib import Path
from sys import argv
from Game_Player import Game
from UI import GUI, Terminal
from Pieces import Rook
from threading import Thread


def usage():
    print(f"""
To play a game of chess:
python {Path(__file__).name} [g | t]
g: initiates a GUI based game
t: initiates a terminal based game
no argument: initiates a GUI based game""")

def do_gui_game():
    game = Game(GUI)
    # The functionality and GUI are run in different threads to allow them to work indpendently, i.e. not waiting on each other
    play_game_thread = Thread(target=game.wait_until_ready_then_play, daemon=True)
    play_game_thread.start()
    game._UI._root.mainloop()

def do_tui_game():
    game = Game(Terminal)
    game.wait_until_ready_then_play()

if __name__ == "__main__":
    # Uses command line arguments to determine if it is a GUI or Terminal based game
    if len(argv) != 2:
        usage()
        do_gui_game()
    elif argv[1] == "g":
        do_gui_game()
    elif argv[1] == "t":
        do_tui_game()
    else:
        usage()
