"""
Cart Surfer gameplay loop - turn sign reaction
------------------------------------------------
Watches the two fixed points where turn signs pass through, and reacts
by pressing Down, then (after a delay) pressing and holding the turn
key.

Run this after run.py has already clicked Play and the game has
loaded.

    python gameplay.py
"""

import time
import cv2
import numpy as np
import pyautogui

from run import TEMPLATE_DIR, screenshot_gray  # reuse existing helpers


# ======================================================================
# TUNING PARAMETERS - this is the section you'll want to adjust.
# All values are in seconds unless noted otherwise.
# ======================================================================

# Where the signs pass through on screen (center point to watch).
LEFT_TURN_POINT = (1200, 500)
RIGHT_TURN_POINT = (600, 500)

# How big a box (pixels, half-width/half-height) around each point to
# search for the sign template. Keep this small for speed/accuracy,
# but big enough that the sign is fully inside it when it "passes
# through" that point.
DETECTION_RADIUS = 60

# Key bindings - change if Cart Surfer uses different keys.
DOWN_KEY = "down"
LEFT_KEY = "left"
RIGHT_KEY = "right"

# --- Timing you said you'll tune ---
DELAY_BEFORE_DOWN = 0.0        # delay from sign detection to Down keypress
DELAY_DOWN_TO_TURN = 0.3       # delay from Down keypress to turn key press
TURN_KEY_HOLD_DURATION = 0.3   # how long to hold the turn key down

# After reacting to a sign, ignore that same point for this long so we
# don't re-trigger on the same sign while it's still in the detection
# box.
REACTION_COOLDOWN = 1.0

# Template match confidence (0-1)
CONFIDENCE_THRESHOLD = 0.8

# How often to poll the screen while watching for signs (seconds).
# Lower = more responsive, more CPU.
POLL_INTERVAL = 0.03

# ======================================================================
# End of tuning parameters
# ======================================================================


LEFT_TEMPLATE = cv2.imread(str(TEMPLATE_DIR / "left_turn.png"), cv2.IMREAD_GRAYSCALE)
RIGHT_TEMPLATE = cv2.imread(str(TEMPLATE_DIR / "right_turn.png"), cv2.IMREAD_GRAYSCALE)


def region_around(point, radius):
    x, y = point
    return (x - radius, y - radius, x + radius, y + radius)


def crop(frame: np.ndarray, box):
    x1, y1, x2, y2 = box
    h, w = frame.shape
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    return frame[y1:y2, x1:x2]


def matches(frame_crop: np.ndarray, template: np.ndarray) -> bool:
    if frame_crop.shape[0] < template.shape[0] or frame_crop.shape[1] < template.shape[1]:
        return False
    result = cv2.matchTemplate(frame_crop, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)
    return max_val >= CONFIDENCE_THRESHOLD


def react_to_turn(direction: str):
    """direction: 'left' or 'right'"""
    turn_key = LEFT_KEY if direction == "left" else RIGHT_KEY
    print(f"[sign] {direction} turn detected -> reacting")

    if DELAY_BEFORE_DOWN > 0:
        time.sleep(DELAY_BEFORE_DOWN)

    pyautogui.keyDown(DOWN_KEY)
    print(f"[key] down: {DOWN_KEY}")

    time.sleep(DELAY_DOWN_TO_TURN)

    pyautogui.keyDown(turn_key)
    print(f"[key] down: {turn_key} (holding {TURN_KEY_HOLD_DURATION}s)")
    time.sleep(TURN_KEY_HOLD_DURATION)

    pyautogui.keyUp(turn_key)
    pyautogui.keyUp(DOWN_KEY)
    print(f"[key] released {turn_key} and {DOWN_KEY}")


def watch_for_turns():
    print("Watching for turn signs. Ctrl+C to stop.")
    left_box = region_around(LEFT_TURN_POINT, DETECTION_RADIUS)
    right_box = region_around(RIGHT_TURN_POINT, DETECTION_RADIUS)

    last_left_reaction = 0.0
    last_right_reaction = 0.0

    while True:
        now = time.time()
        frame = screenshot_gray()

        if now - last_left_reaction > REACTION_COOLDOWN:
            left_crop = crop(frame, left_box)
            if matches(left_crop, LEFT_TEMPLATE):
                react_to_turn("left")
                last_left_reaction = time.time()
                continue  # re-screenshot fresh next loop

        if now - last_right_reaction > REACTION_COOLDOWN:
            right_crop = crop(frame, right_box)
            if matches(right_crop, RIGHT_TEMPLATE):
                react_to_turn("right")
                last_right_reaction = time.time()
                continue

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    print("Starting in 3 seconds - switch to the game window now...")
    time.sleep(3)
    try:
        watch_for_turns()
    except KeyboardInterrupt:
        print("\nStopped.")
