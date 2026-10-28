"""Tests for the potions on the quickslot: reading them (from a quickslot drawn with the game's
own pictures and count digits, at several UI sizes) and counting potions used and picked up.

A potion that isn't read is allowed (it's read again a few seconds later). A wrong count, or
a skill or an empty key taken for a potion, is not.

Run from the project folder:  py -3 tests/test_potions.py
"""
import os
import random
import sys
import tempfile
from pathlib import Path

os.environ["MAPLE_EXP_DATA"] = tempfile.mkdtemp()           # never touch your real data
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import cv2  # noqa: E402
import numpy as np  # noqa: E402
import potions  # noqa: E402

ASSETS = Path(__file__).resolve().parent.parent / "assets" / "potions"
rnd = random.Random(3)
failures = 0


def check(name, ok):
    global failures
    print(("PASS " if ok else "FAIL ") + name)
    failures += not ok


def paste(img, rgba, x, y):
    h, w = rgba.shape[:2]
    h, w = min(h, img.shape[0] - y), min(w, img.shape[1] - x)
    a = rgba[:h, :w, 3:4] / 255.0
    img[y:y + h, x:x + w] = (rgba[:h, :w, :3] * a + img[y:y + h, x:x + w] * (1 - a)).astype(np.uint8)


def scaled(path, s):
    a = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    return cv2.resize(a, None, fx=s, fy=s, interpolation=cv2.INTER_LINEAR if s >= 1 else cv2.INTER_AREA)


def quickslot(keys, s, anchor=(300, 500), size=(1300, 620)):
    """A game-like picture: the quickslot's 8 keys (light squares on a dark frame) with
    keys[i] = (potion key or "skill" or None, count) on each, where the overlay expects them."""
    img = np.full((size[1], size[0], 3), (60, 52, 48), np.uint8)
    img[:] = cv2.GaussianBlur(np.random.default_rng(rnd.randint(0, 999)).integers(
        0, 120, img.shape, dtype=np.uint8), (0, 0), 4)
    q = potions.QuickslotReader(ASSETS)
    boxes = q.slot_boxes(anchor, s)
    x0, y0 = boxes[0][0] - int(4 * s), boxes[0][1] - int(4 * s)
    x1, y1 = boxes[-1][0] + boxes[-1][2] + int(4 * s), boxes[-1][1] + boxes[-1][3] + int(4 * s)
    img[y0:y1, x0:x1] = (70, 66, 62)
    for (x, y, w, h), (key, count) in zip(boxes, keys):
        img[y:y + h, x:x + w] = (226, 222, 218)
        if key == "skill":                            # a skill: a busy picture, no count
            img[y + 4:y + h - 4, x + 4:x + w - 4] = np.random.default_rng(x).integers(0, 255, (h - 8, w - 8, 3))
        elif key:
            icon = scaled(ASSETS / f"{key}.png", s)
            paste(img, icon, x + (w - icon.shape[1]) // 2, y + (h - icon.shape[0]) // 2)
        if count is not None:
            dx = x - int(s)                           # (counts start at the key's left edge)
            for ch in str(count):
                d = scaled(ASSETS / f"count_{ch}.png", s)
                paste(img, d, dx, y + h - d.shape[0])
                dx += d.shape[1] + max(1, round(s))        # (a small gap after each digit)
    return img


# ---- reading the quickslot
layout = [("red_potion", 27), ("skill", None), (None, None), ("blue_potion", 0),
          ("orange_potion", 163), ("lemon", 238), ("white_potion", 150), ("skill", None)]
want = {"red_potion": 27, "blue_potion": 0, "orange_potion": 163, "lemon": 238, "white_potion": 150}
for gh, s in ((7.0, 0.875), (11.0, 1.35), (14.0, 1.75), (22.0, 2.75)):
    img = quickslot(layout, s)
    q = potions.QuickslotReader(ASSETS)
    got = q.read(img, gh, (300, 500), now=0)
    # (a White Potion, pale on a pale key, has little to go on: it may be missed, never misread)
    sure = {k: v for k, v in want.items() if k != "white_potion"}
    check(f"reads every potion and its count, and nothing else (EXP digits {gh} px: {got})",
          got in (want, sure))
    again = q.read(img, gh, (300, 500), now=1)
    check(f"...and again from where they were found ({again})", again == got)
    wrong = {k: v for k, v in got.items() if want.get(k) != v}
    check(f"never a wrong count, even with the UI size guessed 8% off ({wrong})",
          not wrong and not {k: v for k, v in potions.QuickslotReader(ASSETS).read(
              img, gh * 1.08, (300, 500), now=0).items() if want.get(k) != v})

for gh, s in ((11.0, 1.35), (14.0, 1.75)):
    got = potions.QuickslotReader(ASSETS).read(quickslot(layout[:6] + [("white_potion", 1500), layout[7]], s),
                                               gh, (300, 500), now=0)
    check(f"a 4-digit count is read right or not at all ({got.get('white_potion')})",
          got.get("white_potion") in (1500, None))

# ---- the real game (docs/screenshot-game.jpg, a 1920x1080 window): Pup, Del, End and Pdn
shot = cv2.imread(str(Path(__file__).resolve().parent.parent / "docs" / "screenshot-game.jpg"))
for gh in (10.0, 11.0, 12.0):
    got = potions.QuickslotReader(ASSETS).read(shot, gh, (1054, 1044), now=0)
    check(f"reads the potions in a real screenshot, with the UI size guessed from {gh} px ({got})",
          got == {"red_potion": 27, "orange_potion": 163, "lemon": 238, "blue_potion": 0})

# ---- a player's quickslot (a crop of a screenshot, keys named 1, 2, S, Pup / 3, 4, End, Pdn): an
# Orange Potion (269) and a Lemon (266), and items that aren't potions (counts 58, 54 and 140)
lemon = cv2.imread(str(Path(__file__).parent / "frames" / "quickslot_lemon.png"))
q = potions.QuickslotReader(ASSETS)
got = q.read(lemon, 11.0, (404 - 600, 1085 - 870), now=0)
check(f"reads the Orange Potion and the Lemon on a player's quickslot ({got})",
      got == {"orange_potion": 269, "lemon": 266})
seen = [(n, k, why[:16]) for _, n, k, why in q.keys]
check(f"...and says what every key showed ({seen})",
      seen[0][:2] == (269, "orange_potion") and seen[3][:2] == (266, "lemon")
      and seen[1][:2] == (58, None) and seen[1][2].startswith("no potion") and seen[5][:2] == (None, None))

# ---- another player's quickslot, at the game's own size (a lossless screenshot): Lemon 446 and
# Meat 491, Classic World's own pictures, and items that aren't potions (counts 18, 38 and 44)
meat = cv2.imread(str(Path(__file__).parent / "frames" / "quickslot_meat.png"))
for gh, anchor in ((7.0, (-60 - 100, 293 - 160)), (7.5, (-55 - 100, 290 - 160)), (8.0, (-65 - 100, 296 - 160))):
    got = potions.QuickslotReader(ASSETS).read(meat, gh, anchor, now=0)
    check(f"reads the Lemon and the Meat at the game's own size, and nothing else ({gh} px: {got})",
          got == {"lemon": 446, "meat": 491})

# ---- a Mac's screenshots come in the display's colours (Display P3): a Lemon's yellow is paler
# there, too far from the picture's own colours, so on a Mac the pictures are tried in P3's too
def display_p3(bgr):
    return potions._display_p3(np.dstack([bgr, np.full(bgr.shape[:2], 255, np.uint8)]))[..., :3]


for name, shot_, gh, anchor, want_ in (
        ("Lemon and Meat", meat, 7.0, (-60 - 100, 293 - 160), {"lemon": 446, "meat": 491}),
        ("Orange Potion and Lemon", lemon, 11.0, (404 - 600, 1085 - 870), {"orange_potion": 269, "lemon": 266})):
    for p3 in (False, True):
        got = potions.QuickslotReader(ASSETS, display_p3=True).read(display_p3(shot_) if p3 else shot_,
                                                                    gh, anchor, now=0)
        check(f"on a Mac, reads the {name} in {'Display P3' if p3 else 'sRGB'} colours ({got})", got == want_)
for gh, s in ((7.0, 0.875), (11.0, 1.35), (22.0, 2.75)):
    img = quickslot(layout, s)
    got = potions.QuickslotReader(ASSETS, display_p3=True).read(img, gh, (300, 500), now=0)
    check(f"...and reads nothing wrong for it (EXP digits {gh} px: {got})",
          got in (want, {k: v for k, v in want.items() if k != "white_potion"}))
    got = potions.QuickslotReader(ASSETS, display_p3=True).read(display_p3(img), gh, (300, 500), now=0)
    check(f"...even in Display P3 colours ({got})", not {k: v for k, v in got.items() if want.get(k) != v})

# Where the quickslot is comes from the EXP number, to within a few pixels: the keys are lined up
# with the quickslot itself, so a few pixels (or more) off still reads every key right.
for name, shot_, anchor, want_ in (("player's quickslot", lemon, (404 - 600, 1085 - 870), {"orange_potion": 269, "lemon": 266}),
                                  ("1920x1080 screenshot", shot, (1054, 1044),
                                   {"red_potion": 27, "orange_potion": 163, "lemon": 238, "blue_potion": 0})):
    results = {(dx, dy): potions.QuickslotReader(ASSETS).read(shot_, 11.0, (anchor[0] + dx, anchor[1] + dy), now=0)
               for dx in (-20, -8, 8, 20) for dy in (-8, 8)}
    off = {k: v for k, v in results.items() if v != want_}
    check(f"the {name} reads right with the quickslot's place 8-20 px off ({off})", not off)

q = potions.QuickslotReader(ASSETS)
img = quickslot(layout, 1.35)
q.read(img, 11.0, (300, 500), now=0)
img2 = quickslot([("red_potion", 26)] + layout[1:], 1.35)
check("a count that goes down is read as it is now", q.read(img2, 11.0, (300, 500), now=5).get("red_potion") == 26)
img3 = quickslot([(None, None)] + layout[1:], 1.35)
got = q.read(img3, 11.0, (300, 500), now=10)
check(f"a potion taken off its key isn't read any more ({got})", "red_potion" not in got)
check("an empty quickslot reads nothing", potions.QuickslotReader(ASSETS).read(
    quickslot([(None, None)] * 8, 1.35), 11.0, (300, 500), now=0) == {})
check("skills and empty keys aren't potions", potions.QuickslotReader(ASSETS).read(
    quickslot([("skill", None)] * 4 + [(None, 5)] * 4, 1.35), 11.0, (300, 500), now=0) == {})

# ---- the catalog
cat = potions.load_catalog(ASSETS)
names = {p["key"]: p for p in cat}
check(f"every potion in potions.json has a picture ({len(cat)})", len(cat) >= 20)
check("NPC shop prices from meowdb (Classic World)",
      (names["red_potion"]["price"], names["orange_potion"]["price"], names["white_potion"]["price"],
       names["blue_potion"]["price"]) == (50, 150, 350, 220))

# ---- counting potions used and picked up
t = potions.PotionTracker()
prices = {"red_potion": 50, "blue_potion": 220}
t.observe({"red_potion": 80}, True)
check("the first count needs 2 readings that agree", not t.seen)
t.observe({"red_potion": 80}, True)
check("...then it's the starting point, nothing used yet", t.counts == {"red_potion": 80} and t.cost(prices) == 0)
for n in (78, 78, 75, 75):
    t.observe({"red_potion": n}, True)
check(f"potions used are counted and cost their price ({t.used}, {t.cost(prices)})",
      t.used == {"red_potion": 5} and t.cost(prices) == 250)
t.observe({"red_potion": 39}, True)
t.observe({"red_potion": 75}, True)
check("a one-off misread isn't counted", t.used == {"red_potion": 5} and t.counts["red_potion"] == 75)
for n in (77, 77):
    t.observe({"red_potion": n}, True)
check(f"potions picked up cover some of the cost (net {t.net(prices)})",
      t.picked == {"red_potion": 2} and t.net(prices) == 150)
for n in (50, 50):
    t.observe({"red_potion": n}, True)
check("a change of more than 20 needs 3 readings", t.counts["red_potion"] == 77)
t.observe({"red_potion": 50}, True)
check("...then counts", t.used == {"red_potion": 32})
for n in (9, 9):
    t.observe({"red_potion": n}, True)
check("so does a different number of digits", t.counts["red_potion"] == 50)
t.observe({"red_potion": 50}, True)
for n in (300,) * 3:
    t.observe({"red_potion": n}, True)
check("more than 100 at once (storage) starts afresh, uncounted", t.counts["red_potion"] == 300
      and t.picked == {"red_potion": 2} and t.used == {"red_potion": 32})
for n in (290, 290):
    t.observe({"red_potion": n}, False)
check("potions used while paused aren't counted", t.used == {"red_potion": 32} and t.counts["red_potion"] == 290)
t.observe({}, True)
check("not seeing the quickslot keeps the last count", t.counts["red_potion"] == 290)
for n in (288, 288):
    t.observe({"red_potion": n}, True)
check("...and the next count read counts from it", t.used == {"red_potion": 34})
t.reset()
check("reset forgets it all", not t.seen and t.cost(prices) == 0)

print("\nALL PASSED" if not failures else f"\n{failures} FAILED")
sys.exit(1 if failures else 0)
