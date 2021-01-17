import sqlite3
import pickle
import os
import hashlib
import itertools


class Database:
	def __init__(self):
		self._path = "chess.db" # Filename and location of the database
		if os.path.isfile(self._path): # Check if there is already a databse
			# If so, connect to it
			self._conn = sqlite3.connect(self._path)
		else:
			# If not, initialise the database with the correct tables and fields
			self._conn = sqlite3.connect(self._path)
			script = """
			CREATE TABLE Players (
			Username VARCHAR(30) NOT NULL,
			PwHash VARCHAR(255) NOT NULL,
			PRIMARY KEY(Username)
			);
			 
			CREATE TABLE Games (
			GameID INTEGER NOT NULL,
			Played_Moves BLOB,
			Result VARCHAR(255),
			PRIMARY KEY(GameID)
			);
			 
			CREATE TABLE Player_Games (
			Username VARCHAR(30) NOT NULL,
			GameID INTEGER NOT NULL,
			Colour VARCHAR(255),
			FOREIGN KEY(Username) REFERENCES Players(Username),
			FOREIGN KEY(GameID) REFERENCES Games(GameID)
			);
			"""
			self._conn.executescript(script)

			# The database has 2 "fake" players, used when someone isn't signed in, or is playing against the AI
			self._add_player("Anon", self._get_hash("admin_only"))
			self._add_player("AI", self._get_hash("admin_only"))

	def _add_player(self, usr, pwhash):
		# Takes a username and password hash and attempts to add the player to the database
		# Returns true if successful, false if not
		usrs = self._usernames()
		if usr in usrs:
			return False
		stmt = f"INSERT INTO Players (Username, PwHash) VALUES ('{usr}', '{pwhash}')"
		self._conn.execute(stmt)
		self._conn.commit()
		return True

	def _remove_player(self, usr, pwhash):
		# Takes a username and password hash and attempts to remove the player to the database
		# Returns true if successful, false if not
		usrs = self._usernames()
		if usr not in usrs:
			return False
		if not self._check_auth(usr, pwhash):
			return False
		stmt = f"DELETE FROM Players WHERE Username='{usr}'"
		self._conn.execute(stmt)
		self._conn.commit()
		return True

	def _usernames(self):
		# Returns a list of all the usernames in the database
		stmt = f"SELECT Username FROM Players"
		return[i[0] for i in self._conn.execute(stmt).fetchall()]

	def _ids(self):
		# Returns a list of all the GameIDs in the database
		stmt = f"SELECT GameID FROM Games"
		return[i[0] for i in self._conn.execute(stmt).fetchall()]

	def _game_details(self, GameID=None):
		# Returns the details of either all games, or a specific game if GameID is specifified
		stmt = f"""SELECT Games.GameID, Username, Result FROM Player_Games
		INNER JOIN Games ON Player_Games.GameID = Games.GameID{['', f' WHERE Games.GameID={GameID}'][GameID is not None]}"""
		links = [i for i in self._conn.execute(stmt).fetchall()]
		links = [[k, [x for x in g]] for k, g in itertools.groupby(links, lambda x: x[0])] 
		games = []
		for link in links:
			game = [link[0]]
			game.append(link[1][0][1])
			game.append(link[1][1][1])
			game.append(link[1][0][2])
			games.append(game)
		if GameID is None:
			return games
		else:
			return games[0]

	def _get_moves_from_id(self, GameID):
		# Returns the list of moves of a game given the id
		stmt = f"SELECT Played_Moves FROM Games WHERE GameID={GameID}"
		return[pickle.loads(i[0]) for i in self._conn.execute(stmt).fetchall()]

	def _add_game(self, white_usr, black_usr, moves, res):
		# Attempts to add a game to the database, given the players, move and result
		# Returns true if successful, false if not
		stmt = f"SELECT Username FROM Players"
		usrs = [i[0] for i in self._conn.execute(stmt).fetchall()]
		if white_usr not in usrs or black_usr not in usrs:
			return False
		game_id = 0
		stmt = f"SELECT GameID FROM Games"
		ids = [i[0] for i in self._conn.execute(stmt).fetchall()]
		while game_id in ids:
			game_id += 1
		stmt_game = f"INSERT INTO Games (GameID, Played_Moves, Result) VALUES ({game_id},?,'{res}')"
		self._conn.execute(stmt_game,[sqlite3.Binary(pickle.dumps(moves))])
		stmt_white = f"INSERT INTO Player_Games (Username, GameID, Colour) VALUES ('{white_usr}',{game_id},'White')"
		stmt_black = f"INSERT INTO Player_Games (Username, GameID, Colour) VALUES ('{black_usr}',{game_id},'Black')"
		self._conn.execute(stmt_white)
		self._conn.execute(stmt_black)
		self._conn.commit()
		return True

	def _remove_game(self, GameID):
		# Attempts to delete a game with the id specified from the database
		# Returns true if successful, false if not
		if GameID not in self._ids():
			return False
		stmt = f"DELETE FROM Player_Games WHERE GameID={GameID}"
		self._conn.execute(stmt)
		stmt = f"DELETE FROM Games WHERE GameID={GameID}"
		self._conn.execute(stmt)
		self._conn.commit()
		return True

	def _check_auth(self, usr, pwhash):
		# Returns if the username and password hash match, i.e. a successful login attempt
		if usr not in self._usernames():
			return False
		stmt = f"SELECT PwHash FROM Players WHERE Username='{usr}'"
		correct_hash = self._conn.execute(stmt).fetchall()[0][0]
		return pwhash==correct_hash

	def _player_stats(self, usr):
		# Returns the number of wins, draws and losses for a player with the username specified
		stmt = f"""SELECT Games.GameID 
				FROM Games INNER JOIN Player_Games ON Games.GameID = Player_Games.GameID
				WHERE Username ='{usr}' AND ( (Result = 'White wins' AND Colour = 'White') OR (Result = 'Black wins' AND Colour = 'Black') )
				"""
		win_ids = [i[0] for i in self._conn.execute(stmt).fetchall()]
		stmt = f"""SELECT Games.GameID 
				FROM Games INNER JOIN Player_Games ON Games.GameID = Player_Games.GameID
				WHERE Username ='{usr}' AND Result = 'Draw'
				"""
		draw_ids = [i[0] for i in self._conn.execute(stmt).fetchall()]
		stmt = f"""SELECT Games.GameID 
				FROM Games INNER JOIN Player_Games ON Games.GameID = Player_Games.GameID
				WHERE Username ='{usr}' AND ( (Result = 'Black wins' AND Colour = 'White') OR (Result = 'White wins' AND Colour = 'Black') )
				"""
		loss_ids = [i[0] for i in self._conn.execute(stmt).fetchall()]
		return len(win_ids), len(draw_ids), len(loss_ids)

	def _get_hash(self, pw):
		return hashlib.sha1(pw.encode()).hexdigest()


if __name__ == "__main__":
	print("This file just contains the Database class")