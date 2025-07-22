
from collections import Counter

class Tile:
    """Represents a single Mahjong tile."""
    def __init__(self, suit, rank):
        # suit: man, pin, sou, wind, dragon
        # rank: 1-9 for numbered suits, or e.g., 'east', 'white' for honors
        self.suit = suit
        self.rank = rank

    def __repr__(self):
        return f"{self.suit}{self.rank}"

    def __eq__(self, other):
        return self.suit == other.suit and self.rank == other.rank

    def __hash__(self):
        return hash((self.suit, self.rank))

class Player:
    """Represents a player in the game."""
    def __init__(self, name):
        self.name = name
        self.hand = [] # A list of Tile objects
        self.discards = []
        self.melds = []
        self.score = 25000

    def __repr__(self):
        return f"Player({self.name})"

class GameState:
    """Represents the entire state of the Mahjong game at a point in time."""
    def __init__(self):
        self.players = [Player('Player 1'), Player('Player 2'), Player('Player 3'), Player('Player 4')]
        self.current_player_index = 0
        self.round_wind = 'east'
        self.round_number = 1
        self.dora_indicators = []
        self.wall_size = 70 # Starting wall size

    def get_player(self, name):
        for player in self.players:
            if player.name == name:
                return player
        return None

    def print_summary(self):
        """Prints a text-based summary of the current game state."""
        print("--- Game State Summary ---")
        print(f"Round: {self.round_wind.capitalize()} {self.round_number}, Wall Tiles Left: {self.wall_size}")
        print(f"Dora Indicators: {self.dora_indicators}")
        print("--------------------------")
        for player in self.players:
            print(f"> {player.name} (Score: {player.score}) <")
            # Using Counter for a cleaner summary of the hand
            hand_summary = Counter(tile.__repr__() for tile in player.hand)
            print(f"  Hand: {dict(hand_summary)}")
            print(f"  Discards: {player.discards}")
            print(f"  Melds: {player.melds}")
        print("--------------------------")

# --- Utility Functions ---

def tile_from_string(s):
    """Converts a string (e.g., 'man1', 'wind_east') to a Tile object."""
    if s.startswith('wind') or s.startswith('dragon'):
        parts = s.split('_')
        return Tile(parts[0], parts[1])
    else:
        suit = s[:-1]
        rank = int(s[-1])
        return Tile(suit, rank)

