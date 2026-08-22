"""
Cart Surfer launch-sequence bot
--------------------------------
Stage 1 of the project: get from the mine room to the Cart Surfer
title screen and press Play. Score/coin tracking will be layered on
top of this once the launch sequence is reliable.

How it works
------------
1. Screenshot the screen.
2. cv2.matchTemplate() the screenshot against a reference image in
   templates/.
3. If the match confidence clears CONFIDENCE_THRESHOLD, click on the
   matched region (or a fixed coordinate, for the mine->game-area
   click) and move to the next stage.
4. Repeat until Play has been clicked, or STAGE_TIMEOUT is hit.

Run:
    pip install -r requirements.txt
    python run.py
"""

import sys
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import pyautogui

# ----------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------

TEMPLATE_DIR = Path(__file__).parent / "templates"

CONFIDENCE_THRESHOLD = 0.8   # 0-1, raise if you get false positives
POLL_INTERVAL = 0.5          # seconds between screenshot checks
STAGE_TIMEOUT = 20           # seconds to wait for a stage before giving up

# Fixed point to click while standing in the mine to walk to the
# Cart Surfer game area (per your instructions).
MINE_TO_GAME_AREA_CLICK = (1500, 300)

# Failsafe: move mouse to a screen corner to abort (pyautogui built-in)
pyautogui.FAILSAFE = True


# ----------------------------------------------------------------------
# Core matching helpers
# ----------------------------------------------------------------------

def screenshot_gray() -> np.ndarray:
    """Grab the current screen as a grayscale numpy array."""
    shot = pyautogui.screenshot()
    frame = cv2.cvtColor(np.array(shot), cv2.COLOR_RGB2GRAY)
    return frame


def find_template(template_name: str, threshold: float = CONFIDENCE_THRESHOLD):
    """
    Look for templates/<template_name> on the current screen.
    Returns (center_x, center_y, confidence) if found above threshold,
    else None.
    """
    template_path = TEMPLATE_DIR / template_name
    template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
    if template is None:
        raise FileNotFoundError(f"Template not found: {template_path}")

    screen = screenshot_gray()

    # Guard against the template being larger than the current screen
    # capture (e.g. multi-monitor weirdness).
    if template.shape[0] > screen.shape[0] or template.shape[1] > screen.shape[1]:
        return None

    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val >= threshold:
        h, w = template.shape
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        return center_x, center_y, max_val

    return None


def wait_for_template(template_name: str, timeout: float = STAGE_TIMEOUT):
    """Poll until a template appears on screen, or raise TimeoutError."""
    print(f"[wait] looking for '{template_name}' ...")
    start = time.time()
    while time.time() - start < timeout:
        match = find_template(template_name)
        if match:
            x, y, conf = match
            print(f"[found] '{template_name}' at ({x}, {y}) conf={conf:.2f}")
            return x, y
        time.sleep(POLL_INTERVAL)
    raise TimeoutError(f"Timed out waiting for '{template_name}'")


def click_at(x: int, y: int, label: str = ""):
    print(f"[click] {label or 'clicking'} at ({x}, {y})")
    pyautogui.moveTo(x, y, duration=0.2)
    pyautogui.click()


def wait_and_click(template_name: str, timeout: float = STAGE_TIMEOUT, label: str = ""):
    x, y = wait_for_template(template_name, timeout)
    click_at(x, y, label or template_name)
    return x, y


# ----------------------------------------------------------------------
# Launch sequence (mine -> Play button pressed)
# ----------------------------------------------------------------------

@dataclass
class Stage:
    name: str
    fn: callable


def stage_confirm_in_mine():
    """Confirm we're standing in the mine before doing anything else."""
    wait_for_template("mine_marker.png")


def stage_walk_to_game_area():
    """Click the fixed point that walks the character to the Cart
    Surfer entrance."""
    click_at(*MINE_TO_GAME_AREA_CLICK, label="walk to Cart Surfer entrance")


def stage_confirm_dialog():
    """'Would you like to go Cart Surfing?' -> click Yes.

    NOTE: yes_button_dialog.png as provided is a crop of the *whole*
    dialog box, not just the Yes button. That will still generally
    match the dialog and click near its center, but for reliability
    you should crop templates/yes_button_dialog.png down to just the
    Yes button (see the comment in templates/README below).
    """
    wait_and_click("yes_button_dialog.png", label="Yes (Cart Surfing dialog)")


def stage_confirm_title_screen():
    """Wait for the Cart Surfer logo/title screen to load, then hit Play."""
    wait_for_template("title_logo.png")
    wait_and_click("play_button.png", label="Play button")


LAUNCH_SEQUENCE = [
    Stage("confirm_in_mine", stage_confirm_in_mine),
    Stage("walk_to_game_area", stage_walk_to_game_area),
    Stage("confirm_dialog", stage_confirm_dialog),
    Stage("confirm_title_screen", stage_confirm_title_screen),
]


def run_launch_sequence():
    print("Starting Cart Surfer launch sequence.")
    print("Move mouse to a screen corner at any time to abort (failsafe).")
    for stage in LAUNCH_SEQUENCE:
        print(f"\n=== Stage: {stage.name} ===")
        try:
            stage.fn()
        except TimeoutError as e:
            print(f"[error] {e}")
            print("Aborting sequence. Check that the template images "
                  "match what's actually on screen (crop tighter if needed).")
            sys.exit(1)
        time.sleep(0.5)  # brief settle time between stages

    print("\nLaunch sequence complete: Play has been clicked. "
          "Game should now be loading.")


if __name__ == "__main__":
    # Give yourself a few seconds to switch to the game window.
    print("Starting in 3 seconds - switch to the game window now...")
    time.sleep(3)
    run_launch_sequence()
