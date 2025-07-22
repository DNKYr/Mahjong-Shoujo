from mahjong.shanten import Shanten
from mahjong.tile import TilesConverter
from mahjong.hand_calculating.hand import HandCalculator
from mahjong.hand_calculating.hand_config import HandConfig, OptionalRules
from game_state import Tile

class AIPlayer:
    def __init__(self, player_name):
        self.name = player_name
        self.shanten_calculator = Shanten()
        self.hand_calculator = HandCalculator()

    def _to_34_array(self, tiles):
        tile_map = {
            'man': [0, 9], 'pin': [9, 18], 'sou': [18, 27],
            'wind': {'east': 27, 'south': 28, 'west': 29, 'north': 30},
            'dragon': {'white': 31, 'green': 32, 'red': 33}
        }
        hand_array = [0] * 34
        for tile in tiles:
            if tile.suit in ['man', 'pin', 'sou']:
                index = tile_map[tile.suit][0] + tile.rank - 1
                hand_array[index] += 1
            else:
                index = tile_map[tile.suit][tile.rank]
                hand_array[index] += 1
        return hand_array

    def calculate_shanten(self, hand_tiles):
        if not hand_tiles:
            return 99
        hand_array = self._to_34_array(hand_tiles)
        # The mahjong library calculates for standard, seven pairs, and thirteen orphans.
        # The result is the minimum of these.
        return self.shanten_calculator.calculate_shanten(hand_array)

    def estimate_hand_value(self, hand_tiles):
        """
        Estimates the potential value of a hand if it were to be completed.
        This is a simplified heuristic. A full implementation would be much more complex.
        """
        if not hand_tiles:
            return {'han': 0, 'yaku': []}

        hand_array = self._to_34_array(hand_tiles)
        
        # We can't calculate value on an incomplete hand, so we'll look for yaku potential.
        # This is a very simplified approach.
        potential_han = 0
        potential_yaku = []

        # Check for potential Tanyao (all simples)
        is_tanyao = all(tile.suit in ['man', 'pin', 'sou'] and 1 < tile.rank < 9 for tile in hand_tiles)
        if is_tanyao:
            potential_han += 1
            potential_yaku.append('Tanyao')

        # Check for potential Yakuhai (dragons, seat/round wind)
        # This is a simplification - we're just checking for triplets.
        from collections import Counter
        counts = Counter(hand_tiles)
        for tile, count in counts.items():
            if count >= 3 and tile.suit in ['dragon', 'wind']:
                potential_han += 1
                potential_yaku.append(f'Yakuhai ({tile.rank})')

        return {'han': potential_han, 'yaku': potential_yaku}


    def choose_discard(self, hand_tiles):
        """
        Chooses the best tile to discard by balancing shanten and potential hand value.
        """
        if not hand_tiles or len(hand_tiles) % 3 == 0:
            return None

        best_discard_tile = None
        best_score = -9999  # Initialize with a very low score

        unique_tiles = list(set(hand_tiles))
        # Sort the tiles to ensure deterministic behavior in case of ties
        unique_tiles.sort(key=lambda t: (t.suit, t.rank))

        for tile_to_check in unique_tiles:
            temp_hand = list(hand_tiles)
            temp_hand.remove(tile_to_check)

            shanten = self.calculate_shanten(temp_hand)
            
            # If shanten is 0 (tenpai), the value calculation is more meaningful.
            # For now, we'll use a simpler heuristic for all shanten levels.
            value_estimate = self.estimate_hand_value(temp_hand)
            potential_han = value_estimate['han']

            # --- The Heuristic Score ---
            # We want to minimize shanten and maximize han.
            # The weighting factor determines how much we value one over the other.
            # A higher weight for shanten makes the AI play faster.
            # A higher weight for han makes the AI play greedier.
            SHANTEN_WEIGHT = 5 
            score = (potential_han * 1) - (shanten * SHANTEN_WEIGHT)

            if score > best_score:
                best_score = score
                best_discard_tile = tile_to_check

        if best_discard_tile is None and unique_tiles:
            best_discard_tile = unique_tiles[0]

        return best_discard_tile