# Templates

These were cropped directly from the screenshots you sent, so treat
them as a first draft — template matching is picky about exact pixels,
scale, and zoom level, so re-crop any of these from a fresh screenshot
taken at the same resolution/zoom you'll actually run the bot at.

- `mine_marker.png` — a distinctive chunk of the mine room (the "MIN"
  sign fragment), used only to confirm you're in the mine before the
  fixed-coordinate click fires.
- `yes_button_dialog.png` — currently the **whole** "Would you like to
  go Cart Surfing?" dialog box, not just the Yes button. It'll still
  match and click near the dialog's center, but that's fragile if the
  dialog layout shifts. Recommended: re-crop this to just the "Yes"
  button graphic (tight crop, no surrounding blue) for a more precise
  click point.
- `title_logo.png` — the "CART SURFER" logo, used to confirm the
  title screen has loaded.
- `play_button.png` — the PLAY button on the title screen.

## Tips for reliable matches

- Crop templates as tightly as possible around a unique, static
  visual feature — avoid including anti-aliased edges or areas that
  might animate (glow, particles, etc).
- Take template screenshots at the same browser zoom / window size
  you'll run the bot at — `matchTemplate` is not scale-invariant.
- If matches are flaky, lower `CONFIDENCE_THRESHOLD` in `run.py`
  slightly (e.g. 0.75) or re-crop a cleaner template.
