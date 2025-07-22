import cv2
import numpy as np
import os
from PIL import ImageGrab

# --- Configuration ---
TEMPLATE_DIR = 'templates'
MATCH_THRESHOLD = 0.9 # Adjust this value based on detection accuracy (0.0 to 1.0)

def load_templates(directory):
    """Loads all template images from the specified directory."""
    templates = {}
    for filename in os.listdir(directory):
        if filename.endswith(('.png', '.jpg', '.jpeg')):
            name = os.path.splitext(filename)[0]
            path = os.path.join(directory, filename)
            template_img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if template_img is not None:
                templates[name] = template_img
            else:
                print(f"Warning: Could not load template image {path}")
    if not templates:
        raise FileNotFoundError(f"No templates loaded. Is the '{directory}' directory empty or incorrect?")
    return templates

def find_all_matches(screenshot_gray, templates, threshold):
    """Finds all occurrences of all templates in the screenshot."""
    all_locations = {}
    for name, template_img in templates.items():
        w, h = template_img.shape[::-1]
        res = cv2.matchTemplate(screenshot_gray, template_img, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        
        # Store scores along with locations
        score_locations = []
        for pt in zip(*loc[::-1]): # Switch x and y
            score = res[pt[1], pt[0]] # Get the score for this location
            score_locations.append((pt[0], pt[1], w, h, score))

        # Apply Non-Maximum Suppression
        if score_locations:
            all_locations[name] = non_max_suppression(score_locations, 0.5) # 0.5 is the overlap threshold
            
    return all_locations

def non_max_suppression(boxes, overlapThresh):
    """Filters overlapping bounding boxes to find the best match."""
    if len(boxes) == 0:
        return []

    # Convert boxes to a list of lists for easier manipulation
    boxes = [list(b) for b in boxes]

    # Sort the boxes by their score in descending order
    boxes = sorted(boxes, key=lambda b: b[4], reverse=True)
    
    pick = []
    while len(boxes) > 0:
        # Pick the top box
        last = len(boxes) - 1
        i = boxes[last]
        pick.append(i[:4]) # Append the location (x, y, w, h)
        suppress = [last]

        # Loop over all other boxes
        for pos in range(last):
            j = boxes[pos]
            
            # Find the overlapping area
            xx1 = max(i[0], j[0])
            yy1 = max(i[1], j[1])
            xx2 = min(i[0] + i[2], j[0] + j[2])
            yy2 = min(i[1] + i[3], j[1] + j[3])

            w = max(0, xx2 - xx1)
            h = max(0, yy2 - yy1)

            # Compute the ratio of overlap
            overlap = float(w * h) / (i[2] * i[3])

            if overlap > overlapThresh:
                suppress.append(pos)

        # Delete all suppressed boxes
        boxes = [boxes[i] for i in range(len(boxes)) if i not in suppress]

    return pick

from game_state import GameState, tile_from_string

def main():
    """Main function to capture screen, find tiles, and update game state."""
    print("Loading templates...")
    try:
        templates = load_templates(TEMPLATE_DIR)
        print(f"Loaded {len(templates)} templates.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please make sure you have created a 'templates' directory and populated it with tile images.")
        return

    print("\nTaking screenshot... (make sure the game is visible)")
    screenshot_pil = ImageGrab.grab()
    screenshot_cv = cv2.cvtColor(np.array(screenshot_pil), cv2.COLOR_RGB2BGR)
    screenshot_gray = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)
    
    print("Finding tiles on screen...")
    locations = find_all_matches(screenshot_gray, templates, MATCH_THRESHOLD)
    
    if not locations:
        print(f"No tiles found with a threshold of {MATCH_THRESHOLD}. Try adjusting the threshold or checking your template images.")
        return

    # --- Create and Update Game State ---
    game = GameState()
    my_player = game.get_player('Player 1') # Assuming we are Player 1

    # Clear the hand before populating it with new data
    my_player.hand = [] 

    for name, locs in locations.items():
        # For each location this tile was found, add a tile to our hand
        for _ in locs:
            tile = tile_from_string(name)
            my_player.hand.append(tile)

    # Sort the hand for readability (optional, but good practice)
    my_player.hand.sort(key=lambda t: (t.suit, t.rank))

    # --- Print the Game State Summary ---
    print("\n")
    game.print_summary()

    # --- (Optional) Display the visual result ---
    print("\nDisplaying visual recognition result. Press any key in the window to close.")
    for name, locs in locations.items():
        for (x, y, w, h) in locs:
            cv2.rectangle(screenshot_cv, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.imshow('Result', screenshot_cv)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
