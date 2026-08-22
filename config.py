"""
All tunable settings for the Cart Surfer bot live here.
"""

from pathlib import Path

TEMPLATE_DIR = Path(__file__).parent / "templates"

# ----------------------------------------------------------------------
# Template matching
# ----------------------------------------------------------------------
CONFIDENCE_THRESHOLD = 0.7     # 0-1, raise if you get false positives
POLL_INTERVAL = 0.5            # seconds between screenshot checks (launch sequence)
STAGE_TIMEOUT = 20             # seconds to wait for a launch-sequence stage

# ----------------------------------------------------------------------
# Launch sequence (mine -> Play button)
# ----------------------------------------------------------------------
MINE_TO_GAME_AREA_CLICK = (1500, 300)  # fixed point clicked while in the mine

# ----------------------------------------------------------------------
# Gameplay: turn sign reaction
# ----------------------------------------------------------------------

# Where the signs pass through on screen (center point to watch).
LEFT_TURN_POINT = (1200, 500)
RIGHT_TURN_POINT = (600, 500)

# How big a box (pixels, half-width/half-height) around each point to
# sample for black pixels. Keep this small for speed/accuracy, but big
# enough that the sign is fully inside it when it "passes through"
# that point.
DETECTION_RADIUS = 100

# --- Black-pixel sign detection ---
# A pixel counts as "black" if its grayscale value is <= this.
# 0 = pure black, 255 = pure white. Raise slightly if near-black
# (dark grey) parts of the sign aren't being picked up.
BLACK_PIXEL_THRESHOLD = 40

# Fraction (0-1) of pixels in the detection box that must be "black"
# for it to count as a sign being present. Tune this up if background
# scenery is triggering false positives, down if the sign isn't
# reliably detected.
BLACK_PIXEL_RATIO = 0.15

# Key bindings - change if Cart Surfer uses different keys.
DOWN_KEY = "down"
LEFT_KEY = "left"
RIGHT_KEY = "right"

# --- Timing you'll tune ---
DELAY_BEFORE_DOWN = 0.5        # delay from sign detection to Down keypress
DELAY_DOWN_TO_TURN = 0.3       # delay from Down keypress to turn key press
TURN_KEY_HOLD_DURATION = 1   # how long to hold the turn key down

# After reacting to a sign, ignore that same point for this long so we
# don't re-trigger on the same sign while it's still in the detection box.
REACTION_COOLDOWN = 1.0

# How often to poll the screen while watching for signs (seconds).
# Lower = more responsive, more CPU.
GAMEPLAY_POLL_INTERVAL = 0.02
