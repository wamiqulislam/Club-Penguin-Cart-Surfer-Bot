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
BLACK_PIXEL_THRESHOLD = 10

# Fraction (0-1) of pixels in the detection box that must be "black"
# for it to count as a sign being present. Tune this up if background
# scenery is triggering false positives, down if the sign isn't
# reliably detected.
BLACK_PIXEL_RATIO = 0.02

# Key bindings - change if Cart Surfer uses different keys.
DOWN_KEY = "down"
LEFT_KEY = "left"
RIGHT_KEY = "right"

# --- Timing you'll tune ---
DELAY_BEFORE_DOWN = 0.6        # delay from sign detection to Down keypress
DELAY_DOWN_TO_TURN = 0.1       # delay from Down keypress to turn key press
TURN_KEY_HOLD_DURATION = 1   # how long to hold the turn key down

# After reacting to a sign, ignore that same point for this long so we
# don't re-trigger on the same sign while it's still in the detection box.
REACTION_COOLDOWN = 1.75

# How often to poll the screen while watching for signs (seconds).
# Lower = more responsive, more CPU.
GAMEPLAY_POLL_INTERVAL = 0.02

# ----------------------------------------------------------------------
# End of run (Cart Surfer summary screen)
# ----------------------------------------------------------------------
# The summary screen is detected by a solid blue background color
# showing up at a fixed point - NOT by matching the X button, since a
# similar-looking X also appears elsewhere during gameplay.

# Point to sample for the "end of run" blue background.
END_SCREEN_CHECK_POINT = (1100, 500)

# How big a box (pixels, half-width/half-height) around that point to
# sample.
END_SCREEN_DETECTION_RADIUS = 15

# Target blue color (R, G, B) sampled from the summary screen background.
END_SCREEN_BLUE_RGB = (2, 128, 205)

# How close (per channel, 0-255) a pixel's color must be to
# END_SCREEN_BLUE_RGB to count as a match. Keep this tight since we
# want high confidence - raise slightly only if real matches are being
# missed.
END_SCREEN_COLOR_TOLERANCE = 12

# Fraction (0-1) of pixels in the detection box that must match the
# blue color for it to count as "the run has ended". Keep this high
# for confidence, since the box should be solid blue when it's really
# the summary screen.
END_SCREEN_BLUE_RATIO = 0.9

# How often to check for the end-of-run blue while a run is in
# progress. Checked on the same loop tick as sign detection.
END_SCREEN_POLL_INTERVAL = GAMEPLAY_POLL_INTERVAL

# Delay after clicking the close (X) button before starting the next
# launch sequence, to let the mine screen finish loading.
POST_CLOSE_SETTLE = 1.0

# ----------------------------------------------------------------------
# Tricks (back flip / side flip) - run continuously between turns
# ----------------------------------------------------------------------
# Alternates back flip, side flip, back flip, side flip... in a
# background thread, at the same time signs are being watched for.
# When a turn sign is detected, no *new* tricks are started, but a
# trick already in progress is NOT waited on or cancelled - the turn
# reaction's own delay (DELAY_BEFORE_DOWN + DELAY_DOWN_TO_TURN above)
# starts counting down immediately from the moment the sign is seen,
# and is assumed to be long enough to cover any stray trick finishing.

TRICK_KEY = "space"          # key that starts any trick
TRICK_KEY_GAP = 0.1          # delay between the trick key and the direction key

BACKFLIP_KEY = "down"
SIDEFLIP_KEY = "left"

# Which trick(s) the background thread performs:
#   "alternate"      - back flip, side flip, back flip, side flip, ...
#   "backflip_only"  - back flip every time
#   "sideflip_only"  - side flip every time
TRICK_MODE = "alternate"

# Cooldown after each specific trick
BACKFLIP_COOLDOWN = 1
SIDEFLIP_COOLDOWN = 0.7

# How often the trick thread checks whether it's allowed to start a
# new trick (i.e. no turn currently in progress).
TRICK_PAUSE_POLL = 0.01

# ----------------------------------------------------------------------
# Crash recovery ("PRESS SPACEBAR TO CONTINUE")
# ----------------------------------------------------------------------
# This screen can show up at basically any point (crash/disconnect).
# It's checked continuously in the gameplay loop and during every
# poll while waiting on a launch-sequence stage, so it gets caught
# and dismissed no matter where in the flow it happens.
CRASH_RECOVERY_KEY = "space"

# How often to check for it while polling elsewhere (seconds).
CRASH_CHECK_INTERVAL = 1.0
