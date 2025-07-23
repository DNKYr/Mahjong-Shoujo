import cv2
import numpy as np
import os
from PIL import ImageGrab
from game_state import GameState, tile_from_string
from ai_player import AIPlayer

# --- Configuration ---
TEMPLATE_DIR = 'templates'
# The minimum confidence score required to accept a dora match, even if it's the top score.
DORA_MATCH_THRESHOLD = 0.75 
# A higher threshold for hand tiles, which are generally clearer.
HAND_MATCH_THRESHOLD = 0.9

# --- Regions of Interest (ROI) ---
DORA_WIDTH = 66
DORA_HEIGHT = 92
DORA_ROIS = [
    (140, 371, DORA_WIDTH, DORA_HEIGHT), (216, 371, DORA_WIDTH, DORA_HEIGHT),
    (293, 371, DORA_WIDTH, DORA_HEIGHT), (371, 371, DORA_WIDTH, DORA_HEIGHT),
    (445, 371, DORA_WIDTH, DORA_HEIGHT),
]

HAND_ROI_TL = (402, 1558)
HAND_ROI_BR = (2244, 1749)

def load_templates(directory):
    templates = {}
    for filename in os.listdir(directory):
        if filename.endswith(('.png', '.jpg', '.jpeg')):
            name = os.path.splitext(filename)[0]
            path = os.path.join(directory, filename)
            template_img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if template_img is not None:
                templates[name] = template_img
    return templates

def find_best_match_in_roi(screenshot_gray, templates, threshold, roi):
    """Finds the single best matching tile in an ROI, if it exceeds the threshold."""
    x, y, w, h = roi
    roi_image = screenshot_gray[y:y+h, x:x+w]
    best_match = {'name': None, 'score': 0, 'location': None}

    for name, template_img in templates.items():
        # Stretch template to the exact size of the ROI to handle aspect ratio differences
        template_stretched = cv2.resize(template_img, (w, h))
        
        res = cv2.matchTemplate(roi_image, template_stretched, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        if max_val > best_match['score']:
            best_match.update({
                'score': max_val, 
                'name': name, 
                'location': (max_loc[0] + x, max_loc[1] + y, w, h)
            })
    
    # Only return the match if its score is above our minimum confidence threshold
    if best_match['score'] >= threshold:
        return best_match
    else:
        return None

def find_all_matches_in_roi(screenshot_gray, templates, threshold, roi_tl, roi_br):
    x1, y1 = roi_tl
    x2, y2 = roi_br
    hand_roi_image = screenshot_gray[y1:y2, x1:x2]
    all_locations = {}
    for name, template_img in templates.items():
        w, h = template_img.shape[::-1]
        res = cv2.matchTemplate(hand_roi_image, template_img, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        score_locations = []
        for pt in zip(*loc[::-1]):
            score = res[pt[1], pt[0]]
            full_screen_pt = (pt[0] + x1, pt[1] + y1)
            score_locations.append((full_screen_pt[0], full_screen_pt[1], w, h, score))
        if score_locations:
            all_locations[name] = non_max_suppression(score_locations, 0.5)
    return all_locations

def non_max_suppression(boxes, overlapThresh):
    if len(boxes) == 0: return []
    boxes = sorted([list(b) for b in boxes], key=lambda b: b[4], reverse=True)
    pick = []
    while len(boxes) > 0:
        i = boxes.pop(0)
        pick.append(i[:4])
        suppress_indices = []
        for pos, j in enumerate(boxes):
            xx1, yy1 = max(i[0], j[0]), max(i[1], j[1])
            xx2, yy2 = min(i[0] + i[2], j[0] + j[2]), min(i[1] + i[3], j[1] + j[3])
            w, h = max(0, xx2 - xx1), max(0, yy2 - yy1)
            area_i = i[2] * i[3]
            if area_i == 0: continue
            overlap = float(w * h) / area_i
            if overlap > overlapThresh:
                suppress_indices.append(pos)
        boxes = [b for i, b in enumerate(boxes) if i not in suppress_indices]
    return pick

def main():
    print("Loading templates...")
    templates = load_templates(TEMPLATE_DIR)
    if not templates: return

    print("\nTaking screenshot...")
    screenshot_pil = ImageGrab.grab()
    screenshot_cv = cv2.cvtColor(np.array(screenshot_pil), cv2.COLOR_RGB2BGR)
    screenshot_gray = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)
    
    game = GameState()
    all_dora_matches = []
    print("Finding all dora indicators...")
    for roi in DORA_ROIS:
        dora_match = find_best_match_in_roi(screenshot_gray, templates, DORA_MATCH_THRESHOLD, roi)
        if dora_match:
            game.add_dora_indicator(tile_from_string(dora_match['name']))
            all_dora_matches.append(dora_match)
    print(f"Identified {len(game.dora_indicators)} dora indicator(s).")

    print("Finding hand tiles within ROI...")
    locations = find_all_matches_in_roi(screenshot_gray, templates, HAND_MATCH_THRESHOLD, HAND_ROI_TL, HAND_ROI_BR)
    
    my_player = game.get_player('Player 1')
    my_player.hand = [] 
    if locations:
        for name, locs in locations.items():
            for _ in locs:
                my_player.hand.append(tile_from_string(name))
    my_player.hand.sort(key=lambda t: (t.suit, t.rank))

    ai = AIPlayer(player_name='AI Bot')
    recommended_discard = ai.choose_discard(my_player.hand, game.dora_tiles)

    print("\n")
    game.print_summary()
    print("--- AI Analysis ---")
    current_shanten = ai.calculate_shanten(my_player.hand)
    print(f"Current Shanten: {current_shanten}")
    print(f"Recommended Discard: {recommended_discard}")
    print("-------------------")

    print("\nDisplaying visual recognition result...")
    cv2.rectangle(screenshot_cv, HAND_ROI_TL, HAND_ROI_BR, (0, 255, 255), 2)
    for roi in DORA_ROIS:
        x, y, w, h = roi
        cv2.rectangle(screenshot_cv, (x, y), (x + w, y + h), (255, 0, 0), 2)

    if locations:
        for name, locs in locations.items():
            for (x, y, w, h) in locs:
                tile_obj = tile_from_string(name)
                color = (0, 0, 255) if tile_obj == recommended_discard else (0, 255, 0)
                cv2.rectangle(screenshot_cv, (x, y), (x + w, y + h), color, 2)

    for match in all_dora_matches:
        (x, y, w, h) = match['location']
        cv2.rectangle(screenshot_cv, (x, y), (x + w, y + h), (255, 255, 0), 2)

    cv2.imshow('Result', screenshot_cv)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()