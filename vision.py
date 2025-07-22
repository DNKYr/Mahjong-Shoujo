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
        
        locations = []
        for pt in zip(*loc[::-1]): # Switch x and y
            locations.append((pt[0], pt[1], w, h))
        
        if locations:
            all_locations[name] = locations
            
    return all_locations

def main():
    """Main function to capture screen, find tiles, and display results."""
    print("Loading templates...")
    try:
        templates = load_templates(TEMPLATE_DIR)
        print(f"Loaded {len(templates)} templates.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please make sure you have created a 'templates' directory and populated it with tile images.")
        return

    print("\nTaking screenshot... (make sure the game is visible)")
    # Using Pillow for better cross-platform compatibility
    screenshot_pil = ImageGrab.grab()
    screenshot_cv = cv2.cvtColor(np.array(screenshot_pil), cv2.COLOR_RGB2BGR)
    screenshot_gray = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)
    
    print("Finding tiles on screen...")
    locations = find_all_matches(screenshot_gray, templates, MATCH_THRESHOLD)
    
    if not locations:
        print(f"No tiles found with a threshold of {MATCH_THRESHOLD}. Try adjusting the threshold or checking your template images.")
        return

    print(f"Found {sum(len(v) for v in locations.values())} tiles in total.")

    # Draw rectangles around found tiles
    for name, locs in locations.items():
        print(f"- Found {name}: {len(locs)} time(s)")
        for (x, y, w, h) in locs:
            cv2.rectangle(screenshot_cv, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(screenshot_cv, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Display the result
    print("\nDisplaying result. Press any key in the window to close.")
    cv2.imshow('Result', screenshot_cv)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
