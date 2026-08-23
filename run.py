"""
Cart Surfer bot - single entry point
--------------------------------------
Runs the whole thing: mine -> Cart Surfer entrance -> confirm dialog
-> title screen -> Play -> then watches for turn signs and reacts
with Down + turn key for the rest of the run.

All tunable numbers (coordinates, delays, hold durations, thresholds)
live in config.py - edit that file, not this one.

Run:
    pip install -r requirements.txt
    python run.py
"""

import sys
import threading
import time
from dataclasses import dataclass

import cv2
import numpy as np
import pyautogui

import config

pyautogui.FAILSAFE = True  # move mouse to a screen corner to abort


# ----------------------------------------------------------------------
# Core screen / template helpers
# ----------------------------------------------------------------------

def screenshot_rgb() -> np.ndarray:
    """Grab the current screen as an RGB numpy array."""
    return np.array(pyautogui.screenshot())


def screenshot_gray() -> np.ndarray:
    """Grab the current screen as a grayscale numpy array."""
    return cv2.cvtColor(screenshot_rgb(), cv2.COLOR_RGB2GRAY)


def find_template(template_name: str, threshold: float = config.CONFIDENCE_THRESHOLD):
    """
    Look for templates/<template_name> on the current screen.
    Returns (center_x, center_y, confidence) if found above threshold,
    else None.
    """
    template_path = config.TEMPLATE_DIR / template_name
    template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
    if template is None:
        raise FileNotFoundError(f"Template not found: {template_path}")

    screen = screenshot_gray()

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


def wait_for_template(template_name: str, timeout: float = config.STAGE_TIMEOUT):
    """Poll until a template appears on screen, or raise TimeoutError."""
    print(f"[wait] looking for '{template_name}' ...")
    start = time.time()
    while time.time() - start < timeout:
        check_for_crash_screen()
        match = find_template(template_name)
        if match:
            x, y, conf = match
            print(f"[found] '{template_name}' at ({x}, {y}) conf={conf:.2f}")
            return x, y
        time.sleep(config.POLL_INTERVAL)
    raise TimeoutError(f"Timed out waiting for '{template_name}'")


def click_at(x: int, y: int, label: str = ""):
    print(f"[click] {label or 'clicking'} at ({x}, {y})")
    pyautogui.moveTo(x, y, duration=0.2)
    pyautogui.click()


def wait_and_click(template_name: str, timeout: float = config.STAGE_TIMEOUT, label: str = ""):
    x, y = wait_for_template(template_name, timeout)
    click_at(x, y, label or template_name)
    return x, y


# ----------------------------------------------------------------------
# Crash recovery ("PRESS SPACEBAR TO CONTINUE")
# ----------------------------------------------------------------------
# Can appear at any point. check_for_crash_screen() is cheap to call
# often - it's wired into both the launch-sequence wait loop and the
# gameplay loop so it gets caught wherever it happens.

_last_crash_check = 0.0


def check_for_crash_screen() -> bool:
    """If the 'PRESS SPACEBAR TO CONTINUE' screen is up, press space
    and return True. Rate-limited internally so it's safe to call on
    every loop tick without slowing things down."""
    global _last_crash_check
    now = time.time()
    if now - _last_crash_check < config.CRASH_CHECK_INTERVAL:
        return False
    _last_crash_check = now

    match = find_template("press_spacebar.png")
    if match:
        x, y, conf = match
        print(f"[recover] 'PRESS SPACEBAR TO CONTINUE' detected (conf={conf:.2f}) "
              f"-> pressing {config.CRASH_RECOVERY_KEY}")
        pyautogui.press(config.CRASH_RECOVERY_KEY)
        time.sleep(0.5)  # let it register before anything else happens
        return True
    return False


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
    click_at(*config.MINE_TO_GAME_AREA_CLICK, label="walk to Cart Surfer entrance")


def stage_confirm_dialog():
    """'Would you like to go Cart Surfing?' -> click Yes."""
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

    print("\nLaunch sequence complete: Play has been clicked. Game is loading.")


# ----------------------------------------------------------------------
# Gameplay: turn sign reaction
# ----------------------------------------------------------------------
# Sign detection here is NOT template matching. At the two fixed watch
# points, the only time black pixels show up is when a turn sign
# (black chevron on yellow) is passing through. So we just check: is
# there a meaningful amount of black in this box right now? If yes,
# a sign is there.

def region_around(point, radius):
    x, y = point
    return (x - radius, y - radius, x + radius, y + radius)


def crop(frame: np.ndarray, box):
    x1, y1, x2, y2 = box
    h, w = frame.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    return frame[y1:y2, x1:x2]


def black_ratio(frame_crop: np.ndarray) -> float:
    """Fraction of pixels in this crop that are black."""
    if frame_crop.size == 0:
        return 0.0
    black_pixels = np.count_nonzero(frame_crop <= config.BLACK_PIXEL_THRESHOLD)
    return black_pixels / frame_crop.size


def has_sign(frame_crop: np.ndarray) -> tuple:
    ratio = black_ratio(frame_crop)
    return ratio >= config.BLACK_PIXEL_RATIO, ratio


def blue_ratio(frame_crop_rgb: np.ndarray) -> float:
    """Fraction of pixels in this RGB crop matching the end-screen blue."""
    if frame_crop_rgb.size == 0:
        return 0.0
    target = np.array(config.END_SCREEN_BLUE_RGB)
    diff = np.abs(frame_crop_rgb.astype(np.int16) - target)
    matches_mask = np.all(diff <= config.END_SCREEN_COLOR_TOLERANCE, axis=-1)
    return np.count_nonzero(matches_mask) / matches_mask.size


def is_end_screen(frame_crop_rgb: np.ndarray) -> tuple:
    ratio = blue_ratio(frame_crop_rgb)
    return ratio >= config.END_SCREEN_BLUE_RATIO, ratio


# ----------------------------------------------------------------------
# Tricks (back flip / side flip) - run in a background thread,
# continuously, at the same time signs are being watched for.
# ----------------------------------------------------------------------

_tricks_allowed = threading.Event()  # set = ok to start a new trick
_trick_thread_stop = threading.Event()


def do_backflip():
    """Back flip: Down first, then Space."""
    print("[trick] back flip")
    pyautogui.press(config.BACKFLIP_KEY)
    time.sleep(config.TRICK_KEY_GAP)
    pyautogui.press(config.TRICK_KEY)


def do_sideflip():
    """Side flip: Space first, then Left."""
    print("[trick] side flip")
    pyautogui.press(config.TRICK_KEY)
    time.sleep(config.TRICK_KEY_GAP)
    pyautogui.press(config.SIDEFLIP_KEY)


def _trick_loop():
    """Background thread body. Performs tricks according to
    config.TRICK_MODE whenever tricks are allowed. When a turn sign is
    detected, react_to_turn() clears _tricks_allowed immediately - this
    loop will simply not START a new trick after that point, but a
    trick already in flight here just finishes on its own; nothing
    waits on it and nothing cancels it mid-way."""
    do_backflip_next = True
    while not _trick_thread_stop.is_set():
        if _tricks_allowed.is_set():
            if config.TRICK_MODE == "backflip_only":
                do_backflip()
                time.sleep(config.BACKFLIP_COOLDOWN)
            elif config.TRICK_MODE == "sideflip_only":
                do_sideflip()
                time.sleep(config.SIDEFLIP_COOLDOWN)
            else:  # "alternate"
                if do_backflip_next:
                    do_backflip()
                    time.sleep(config.BACKFLIP_COOLDOWN)
                else:
                    do_sideflip()
                    time.sleep(config.SIDEFLIP_COOLDOWN)
                do_backflip_next = not do_backflip_next
        else:
            time.sleep(config.TRICK_PAUSE_POLL)


def start_trick_thread():
    _trick_thread_stop.clear()
    _tricks_allowed.set()
    thread = threading.Thread(target=_trick_loop, daemon=True)
    thread.start()
    return thread


def stop_trick_thread(thread: threading.Thread):
    _tricks_allowed.clear()
    _trick_thread_stop.set()
    thread.join(timeout=2)


def react_to_turn(direction: str, ratio: float):
    """direction: 'left' or 'right'"""
    turn_key = config.LEFT_KEY if direction == "left" else config.RIGHT_KEY
    print(f"[sign] {direction} turn detected (black_ratio={ratio:.2f}) -> reacting")

    # Stop new tricks from starting, but do NOT wait for a trick that's
    # already in progress - the delay below runs concurrently with it.
    _tricks_allowed.clear()

    if config.DELAY_BEFORE_DOWN > 0:
        time.sleep(config.DELAY_BEFORE_DOWN)

    pyautogui.keyDown(config.DOWN_KEY)
    print(f"[key] down: {config.DOWN_KEY}")

    time.sleep(config.DELAY_DOWN_TO_TURN)

    pyautogui.keyDown(turn_key)
    print(f"[key] down: {turn_key} (holding {config.TURN_KEY_HOLD_DURATION}s)")
    time.sleep(config.TURN_KEY_HOLD_DURATION)

    pyautogui.keyUp(turn_key)
    pyautogui.keyUp(config.DOWN_KEY)
    print(f"[key] released {turn_key} and {config.DOWN_KEY}")

    # Turn is done - tricks can resume.
    _tricks_allowed.set()


def watch_for_turns():
    """Runs the sign-reaction loop until the end-of-run blue background
    shows up at END_SCREEN_CHECK_POINT, then returns. Does not click
    the X - that's handled by the caller, since the X button also
    appears (and shouldn't be clicked) during normal gameplay.

    Tricks (back flip / side flip) run continuously in a background
    thread for the duration of this function - see start_trick_thread /
    react_to_turn for how they pause around turns."""
    print("\nWatching for turn signs. Run ends when end-screen blue is detected.")
    left_box = region_around(config.LEFT_TURN_POINT, config.DETECTION_RADIUS)
    right_box = region_around(config.RIGHT_TURN_POINT, config.DETECTION_RADIUS)
    end_box = region_around(config.END_SCREEN_CHECK_POINT, config.END_SCREEN_DETECTION_RADIUS)

    last_left_reaction = 0.0
    last_right_reaction = 0.0
    last_end_check = 0.0

    trick_thread = start_trick_thread()
    try:
        while True:
            now = time.time()

            if check_for_crash_screen():
                continue  # re-screenshot fresh next loop

            frame_rgb = screenshot_rgb()
            frame_gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY)

            if now - last_left_reaction > config.REACTION_COOLDOWN:
                is_sign, ratio = has_sign(crop(frame_gray, left_box))
                if is_sign:
                    react_to_turn("left", ratio)
                    last_left_reaction = time.time()
                    continue  # re-screenshot fresh next loop

            if now - last_right_reaction > config.REACTION_COOLDOWN:
                is_sign, ratio = has_sign(crop(frame_gray, right_box))
                if is_sign:
                    react_to_turn("right", ratio)
                    last_right_reaction = time.time()
                    continue

            if now - last_end_check > config.END_SCREEN_POLL_INTERVAL:
                last_end_check = now
                ended, ratio = is_end_screen(crop(frame_rgb, end_box))
                if ended:
                    print(f"[found] end-of-run blue detected (ratio={ratio:.2f})")
                    return

            time.sleep(config.GAMEPLAY_POLL_INTERVAL)
    finally:
        stop_trick_thread(trick_thread)


# ----------------------------------------------------------------------
# End of run: close summary screen and loop
# ----------------------------------------------------------------------

def finish_run():
    """Handle the end-of-run screen: wait for it, then click the X."""
    watch_for_turns()
    wait_and_click("end_screen_close.png", label="close summary screen (X)")
    time.sleep(config.POST_CLOSE_SETTLE)


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------

if __name__ == "__main__":
    print("Starting in 3 seconds - switch to the game window now...")
    time.sleep(3)

    run_number = 0
    try:
        while True:
            run_number += 1
            print(f"\n########## RUN {run_number} ##########")
            run_launch_sequence()
            finish_run()
    except KeyboardInterrupt:
        print("\nStopped.")
