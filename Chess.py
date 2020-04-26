from pathlib import Path
from sys import argv
from Game_Player import Game
from UI import GUI, Terminal
from Pieces import Rook


def usage():
    print(f"""
To play a game of chess:
python {Path(__file__).name} [g | t]
g: initiates a GUI based game
t: initiates a terminal based game""")
    quit()


if __name__ == "__main__":
    if len(argv) != 2:
        usage()
    elif argv[1] == "g":
        game = Game(GUI)
    elif argv[1] == "t":
        game = Game(Terminal)
    else:
        usage()

    game.play_game()
