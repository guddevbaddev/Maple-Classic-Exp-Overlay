"""Potions on the quickslot: which ones are there, and how many of each you have.

The quickslot (the 8 keys above the right end of the status bar) shows each item's picture
and, in its bottom-left corner, how many you have in all. The pictures and the count's
digits are the game's own (assets/potions), drawn at the size the game draws its UI, which
goes with the EXP digits' height.

A slot's key name ("Pup", "Del") is drawn see-through over the top of its picture, and the
count over its bottom-left, so a picture is matched by the rest: the potion's body, in
colour (a red and an orange potion are the same shape). A slot only counts if its count
reads clearly too, which also leaves out skills and anything that isn't a potion.

The quickslot is always in the same place next to the EXP number (at the UI's scale), so
only its 8 keys are looked at. Every key is checked for a potion now and then; in between,
only the keys where potions were found are read again.

On a Mac, screenshots come in the display's own colours (Display P3 on most Macs), not the
game's: bright colours come out a little paler (a Lemon's yellow most of all), so there each
picture is also tried in Display P3's colours.

PotionTracker turns the counts into potions used (the count went down) and picked up (it
went up), each worth its price (potions.json: the NPC shop price, which Settings can change).
"""
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ICON_MAX = 42.0             # colour difference (RMS, 0-255) a picture may have (true ones: ~20-37)
ICON_LEAD = 10.0            # ...and how much closer than any other picture it must be
SHAPE_MIN = 0.6             # how well its light and dark parts must line up (true ones: ~0.65-0.99,
                            # lowest for a White Potion on a pale key: there's little light and dark)
RIVAL_SHAPE = 0.85          # ...and for another picture to cast doubt on it (a White Potion "fits"
                            # most potions' colours a little, but lines up at only ~0.7)
DIGIT_MIN = 0.68            # how well each digit of a count must match (true ones: ~0.75+, stray bits ~0.6)
DIGIT_TAIL = 0.6            # a count is only read if nothing just before or after it fits a digit this
                            # well: a digit that fits a little less (drawn over a potion's dark outline)
                            # means the count may go on, so it's not read rather than read short
DIGIT_LEAD = 0.05           # ...and how far ahead of any other digit at that spot (a 6 and a 9 differ
                            # little at a slightly wrong size): an unsure count isn't read at all
SCALE_PER_GH = 1 / 8        # the UI's scale for an EXP digit height (1.35 at gh ~11)
ICON_STEPS = (0.86, 0.9, 0.93, 0.96, 0.99, 1.02)   # picture sizes tried, around the
                            # digits' scale (Classic World's pictures are a little smaller than these)
# The quickslot's keys, in units of the UI's scale, from where the EXP number starts
# (measured on 1920x1080 and 2000x1267 screenshots: the same in both)
SLOT_LEFT, SLOT_TOP = 199, -118
SLOT_PITCH = (35.5, 35)      # (measured on a lossless screenshot at the game's own size)
SLOT_SIZE = 30
SLOT_SLACK = 12             # how far from there a key's picture may be (the scale is a guess)
GRID_MIN = 0.4             # how clearly the quickslot's keys must show to line up with them (~0.6)
SEARCH_SECONDS = 30         # how often every key is checked for a (new) potion
COUNT_MAX = 9999


def load_catalog(folder):
    """[{"key", "name", "price", "hp", "mp"}] from potions.json (those with a picture), or []."""
    try:
        data = json.loads((Path(folder) / "potions.json").read_text(encoding="utf-8"))
        return [p for p in data["potions"] if (Path(folder) / f"{p['key']}.png").exists()]
    except Exception:
        return []


def _load_rgba(path):
    a = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if a is None or a.ndim != 3 or a.shape[2] != 4:
        raise ValueError(f"not a picture with transparency: {path}")
    return a


# sRGB to Display P3, in linear light (both use sRGB's curve)
_SRGB_TO_P3 = np.array([[0.8225, 0.1774, 0.0000],
                        [0.0332, 0.9669, 0.0000],
                        [0.0171, 0.0724, 0.9108]])


def _display_p3(a):
    """The picture (BGRA) as a Mac's screenshot of a Display P3 screen shows it."""
    v = a[..., 2::-1].astype(np.float64) / 255                         # (RGB)
    v = np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4) @ _SRGB_TO_P3.T
    v = np.where(v <= 0.0031308, v * 12.92, 1.055 * np.maximum(v, 0) ** (1 / 2.4) - 0.055)
    out = a.copy()
    out[..., :3] = np.clip(v[..., ::-1] * 255 + 0.5, 0, 255).astype(np.uint8)
    return out


def _resize(a, s):
    return cv2.resize(a, None, fx=s, fy=s, interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)


def _body(a, s):
    """(colour picture, 3-channel mask) at scale s: the solid part of the picture, without the
    top (under the key name), the bottom (under a long count) and the left (under the count)."""
    t = _resize(a, s)
    m = cv2.erode((t[..., 3] > 220).astype(np.uint8), np.ones((3, 3), np.uint8))
    h, w = m.shape
    m[:int(h * 0.4)] = 0
    m[int(h * 0.75):] = 0
    m[:, :int(w * 0.3)] = 0
    return t[..., :3].astype(np.float32), cv2.merge([m, m, m]).astype(np.float32), int(m.sum())


def _digit(a, s):
    t = _resize(a, s)
    return cv2.cvtColor(t[..., :3], cv2.COLOR_BGR2GRAY), (t[..., 3] > 100).astype(np.uint8)


class QuickslotReader:
    """Reads {potion key: count} from a picture of the area around the quickslot."""

    def __init__(self, folder, display_p3=sys.platform == "darwin"):
        self.catalog = load_catalog(folder)
        self.icons = {p["key"]: _load_rgba(Path(folder) / f"{p['key']}.png") for p in self.catalog}
        # each picture as it may show on screen: as it is, and on a Mac in Display P3's colours too
        self.looks = {k: [a] + ([_display_p3(a)] if display_p3 else []) for k, a in self.icons.items()}
        self.digits = [_load_rgba(Path(folder) / f"count_{d}.png") for d in range(10)]
        self._cache = {}            # scale -> prepared pictures
        self.forget()

    @property
    def ok(self):
        return bool(self.icons)

    def forget(self):
        """Look for the potions from scratch (the window changed size, or Reset)."""
        self.slots = {}             # key number -> (potion, scale, x, y, w, h, the key's box)
        self.digit_scale = None     # the UI's scale, as the count digits fit it best
        self.next_search = 0.0
        self._where = None          # (EXP digit height, anchor) the scale was found for
        self.lined_up = None        # the anchor, moved to where the quickslot's keys really are
        self.found = []             # what the last look found: [(key, (x, y, w, h), count)]
        self.keys = []              # what the last look at every key saw: [(box, count, potion, why)]
        self.closest = []           # the pictures closest to the last one looked at: [(rms, key, shape)]

    def _icons_at(self, s):
        s = round(s, 3)
        if s not in self._cache:
            if len(self._cache) > 40:
                self._cache.clear()
            self._cache[s] = {k: [_body(a, s) for a in looks] for k, looks in self.looks.items()}
        return self._cache[s]

    def _digits_at(self, s):
        key = ("digits", round(s, 3))
        if key not in self._cache:
            self._cache[key] = [_digit(a, s) for a in self.digits]
        return self._cache[key]

    @staticmethod
    def _rms(img, tpl, mask, n):
        """Colour difference of the picture at each spot of img (RMS per channel)."""
        if img.shape[0] < tpl.shape[0] or img.shape[1] < tpl.shape[1] or n < 20:
            return None
        r = cv2.matchTemplate(img, tpl, cv2.TM_SQDIFF, mask=mask)
        return np.sqrt(np.maximum(r, 0) / (3 * n))

    def _classify(self, img, scales, keys=None):
        """[(rms, key, x, y, w, h, scale)]: the potion in img (a key, with a little room around
        it), or [] if none fits well enough, or two fit nearly as well."""
        fits, self.closest = [], []
        for key in (keys or self.icons):
            best, look = None, 0                      # this picture's best spot, size and colours
            for s in scales:
                for i, (tpl, mask, n) in enumerate(self._icons_at(s)[key]):
                    r = self._rms(img, tpl, mask, n)
                    if r is None:
                        continue
                    _, v, _, (x, y) = cv2.minMaxLoc(-r)
                    if best is None or -v < best[0]:
                        best, look = (-v, key, x, y, tpl.shape[1], tpl.shape[0], s), i
            # (only pictures whose light and dark parts line up there too: a plain pale patch
            # is close to a White Potion's colour without looking like one)
            if best and best[0] <= ICON_MAX + ICON_LEAD:
                shape = self._shape(img, *best[1:4], best[6], look)
                self.closest.append((best[0], key, shape))
                if shape >= SHAPE_MIN:
                    fits.append(best + (shape,))
            elif best:
                self.closest.append((best[0], key, None))
        fits.sort()
        self.closest.sort()                           # (for the log and View capture)
        if not fits or fits[0][0] > ICON_MAX:
            return []
        # Of the pictures nearly as close in colour as the closest, the one whose light and dark
        # parts line up best wins (a White Potion comes close in colour to most potions, and can
        # even be a little closer, but lines up at only ~0.6): unless another lines up well too.
        near = [f for f in fits if f[0] - fits[0][0] < ICON_LEAD and f[0] <= ICON_MAX]
        near.sort(key=lambda f: -f[7])
        if len(near) > 1 and near[1][7] >= RIVAL_SHAPE:
            return []                                  # two potions fit nearly as well: unsure
        return [near[0][:7]]

    def _shape(self, img, key, x, y, s, look=0):
        """Not just the right colours: how well the picture's light and dark parts line up with
        the potion's (-1 to 1; a plain white patch is as close to a White Potion's colour as
        it gets, but has no light and dark parts: 0)."""
        tpl, mask, _ = self._icons_at(s)[key][look]
        h, w = tpl.shape[:2]
        patch = img[y:y + h, x:x + w]
        m = mask[..., 0] > 0
        a, b = patch[m].ravel(), tpl[m].ravel()
        if a.std() < 8 or b.std() < 1:
            return 0.0
        return float(np.corrcoef(a, b)[0, 1])

    def read_count(self, grey, box):
        """The count in the bottom-left corner of a quickslot key (box: x, y, w, h), or None."""
        got = self._count_at(grey, box, self.digit_scale) if self.digit_scale else None
        return got[0] if got else None

    def _find_digit_scale(self, grey, anchor, s):
        """The UI's scale, which s (from the EXP digits) is only a guess at: the size at which
        the counts on all the keys (lined up with the quickslot at that size) fit the game's digits best."""
        def fit(size):
            boxes = self.slot_boxes(self._line_up(grey, anchor, size), size)
            reads = [self._count_at(grey, box, size) for box in boxes]
            return sum(r[1] for r in reads if r)             # (each key once: a long misread isn't worth more)
        best = max(((fit(s * f), s * f) for f in np.arange(0.86, 1.15, 0.02)), key=lambda b: b[0])
        if best[0] == 0:
            return None
        return max([best] + [(fit(best[1] + d * s), best[1] + d * s) for d in (-0.01, 0.01)],
                   key=lambda b: b[0])[1]                 # (then finer, around the best)

    def _count_at(self, grey, box, s):
        """(count, how well its digits fit) at scale s, or None.

        The game writes a count from the key's left edge along its bottom, digit after digit, so
        it's read that way: from each starting spot near there, each digit that fits, then each
        that fits just after it, until none does. The reading whose digits fit best wins."""
        digits = self._digits_at(s)
        dh, dw = digits[0][0].shape
        x, y, w, h = box
        x0, x1 = max(0, int(x - 0.8 * dw)), min(grey.shape[1], int(x + 1.35 * w))  # (long ones spill over)
        y0, y1 = max(0, int(y + h - 1.7 * dh)), min(grey.shape[0], int(y + h + 0.25 * dh))
        area = grey[y0:y1, x0:x1]
        maps = []
        for tpl, mask in digits:
            if area.shape[0] < tpl.shape[0] or area.shape[1] < tpl.shape[1]:
                return None
            maps.append(np.nan_to_num(cv2.matchTemplate(area, tpl, cv2.TM_CCOEFF_NORMED, mask=mask),
                                      nan=-1.0, posinf=-1.0, neginf=-1.0))
        width = [t.shape[1] for t, _ in digits]
        rows = min(m.shape[0] for m in maps)
        gap = max(2, int(0.5 * dw))
        def steps(at, row, first):
            """The digits that could come next: the best spot for each digit, starting within
            `gap` of `at` (after the first, a pixel up, down or back too: a scaled-up picture
            rounds them a little apart)."""
            lo, hi = (max(0, at - 1), at + gap) if not first else (at, at + 1)
            out = []
            for d, m in enumerate(maps):
                pick = None
                for r in ((row,) if first else (row - 1, row, row + 1)):
                    seg = m[r, lo:min(m.shape[1], hi)] if 0 <= r < rows else m[:0, :0]
                    if seg.size:
                        i = int(seg.argmax())
                        if seg[i] >= DIGIT_MIN and (pick is None or seg[i] > pick[0]):
                            pick = (float(seg[i]), d, lo + i, r)
                if pick:
                    out.append(pick)
            return out

        def lead(v, d, i, r):
            """How far this digit is ahead of the best other digit at about the same spot."""
            others = [float(m[r, max(0, i - 1):i + 2].max()) for e, m in enumerate(maps)
                      if e != d and m[r, max(0, i - 1):i + 2].size]
            return v - max(others, default=-1.0)

        def tail(at, row):
            """How well the best digit fits just after a count that ends at `at`."""
            lo, hi = max(0, at - 1), at + gap
            return max((float(m[r, lo:min(m.shape[1], hi)].max()) for m in maps for r in (row - 1, row, row + 1)
                        if 0 <= r < rows and m[r, lo:min(m.shape[1], hi)].size), default=-1.0)

        def head(i, row):
            """How well the best digit fits just before a count whose first digit starts at `i`."""
            fits = [float(m[r, lo:hi].max()) for d, m in enumerate(maps) for r in (row - 1, row, row + 1)
                    for lo, hi in [(max(0, i - width[d] - gap), max(0, i - width[d] + 2))]
                    if 0 <= r < rows and m[r, lo:hi].size]
            return max(fits, default=-1.0)

        best = None

        def follow(text, fit, at, row, sure):
            nonlocal best
            nxt = steps(at, row, False) if len(text) < 5 else []
            for v, d, i, r in nxt:
                follow(text + str(d), fit + v, i + width[d], r, min(sure, lead(v, d, i, r)))
            if nxt or len(text) > 4 or (text.startswith("0") and text != "0"):
                return                                # (a count ends where no digit follows)
            if at > area.shape[1] - 0.3 * dw:
                return                                # it may go on past where it's looked at
            if tail(at, row) >= DIGIT_TAIL:
                return                                # it may go on: a digit that fits a little less
            if best is None or fit > best[1]:
                best = (int(text), fit, sure)

        for row in range(rows):
            for start in range(0, min(int(1.4 * dw), maps[0].shape[1])):
                for v, d, i, r in steps(start, row, True):
                    if head(i, r) < DIGIT_TAIL:        # (not where a count starts: one more digit before it)
                        follow(str(d), v, i + width[d], r, lead(v, d, i, r))
        if best is None or best[2] < DIGIT_LEAD:
            return None                               # (nothing, or a digit that could be another)
        return best[0], best[1] / len(str(best[0]))

    @staticmethod
    def _grid(s):
        """(picture, mask) of the quickslot's 8 keys at scale s: light keys on a dark frame, without
        the middle of each key (where a potion's picture is), for lining the keys up with it."""
        px, py, size = SLOT_PITCH[0] * s, SLOT_PITCH[1] * s, SLOT_SIZE * s
        H, W = int(py + size + 8), int(3 * px + size + 8)
        pic, mask = np.zeros((H, W), np.uint8), np.ones((H, W), np.uint8)
        for r in range(2):
            for c in range(4):
                x, y = int(4 + c * px), int(4 + r * py)
                pic[y + 2:y + int(size) - 2, x + 2:x + int(size) - 2] = 255
                mask[y + int(0.2 * size):y + int(0.8 * size), x + int(0.2 * size):x + int(0.8 * size)] = 0
        return pic, mask

    def _line_up(self, grey, anchor, s):
        """The anchor moved so the keys sit exactly on the quickslot found near where they should
        be (the EXP number gives where only to within a few pixels), or as it was if it isn't clear."""
        pic, mask = self._grid(s)
        x, y = self.slot_boxes(anchor, s)[0][:2]
        reach = self.reach(s)
        x0, y0 = max(0, x - 4 - reach), max(0, y - 4 - reach)       # (as far as the picture goes)
        area = grey[y0:y - 4 + reach + pic.shape[0], x0:x - 4 + reach + pic.shape[1]]
        if area.shape[0] < pic.shape[0] or area.shape[1] < pic.shape[1]:
            return anchor
        r = np.nan_to_num(cv2.matchTemplate(area, pic, cv2.TM_CCOEFF_NORMED, mask=mask), nan=-1.0)
        _, v, _, (dx, dy) = cv2.minMaxLoc(r)
        if v < GRID_MIN:
            return anchor
        return anchor[0] + x0 + dx - (x - 4), anchor[1] + y0 + dy - (y - 4)

    @staticmethod
    def reach(s):
        """How far from where the EXP number says the quickslot may really be, in pixels."""
        return int(0.6 * SLOT_PITCH[0] * s)

    @staticmethod
    def slot_boxes(anchor, s):
        """Where the 8 quickslot keys are (x, y, w, h), from where the EXP number starts (anchor:
        its left end and middle) and the UI's scale s. The quickslot sits above the right end
        of the status bar, the same distance from the EXP number at every window size."""
        ax, ay = anchor
        size = SLOT_SIZE * s
        return [(int(ax + s * (SLOT_LEFT + c * SLOT_PITCH[0])), int(ay + s * (SLOT_TOP + r * SLOT_PITCH[1])),
                 int(size), int(size)) for r in range(2) for c in range(4)]

    @staticmethod
    def area(anchor, s):
        """The part of the screen the quickslot is in, with room to spare: (x0, y0, x1, y1)."""
        boxes = QuickslotReader.slot_boxes(anchor, s)
        pad = QuickslotReader.reach(s * 1.15) + int(SLOT_SLACK * s) + 6   # (room to line the keys up)
        return (min(b[0] for b in boxes) - pad, min(b[1] for b in boxes) - pad,
                max(b[0] + b[2] for b in boxes) + pad, max(b[1] + b[3] for b in boxes) + pad)

    def read(self, bgr, gh, anchor, now=None):
        """{key: count} for the potions on the quickslot keys (with a count that reads clearly).
        bgr: a picture with the quickslot in it; anchor: where the EXP number starts in it."""
        self.found = []
        if not self.ok or bgr is None or bgr.size == 0 or not gh or not anchor:
            return {}
        now = time.monotonic() if now is None else now
        img = bgr.astype(np.float32)
        grey = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        s0 = gh * SCALE_PER_GH
        w = self._where                                    # (the UI's size only changes with these)
        if w is None or w[0] != gh or max(abs(w[1][0] - anchor[0]), abs(w[1][1] - anchor[1])) > 3:
            self._where, self.digit_scale, self.next_search = (gh, anchor), None, 0.0
        if now >= self.next_search:
            self.next_search = now + SEARCH_SECONDS
            self.slots = {}
            if self.digit_scale is None:
                self.digit_scale = self._find_digit_scale(grey, anchor, s0)
            if self.digit_scale is None:                   # no counts anywhere: no potions
                return {}
            self.lined_up = self._line_up(grey, anchor, self.digit_scale)
            boxes = self.slot_boxes(self.lined_up, self.digit_scale)
            self.keys = []
            for i, (x, y, w, h) in enumerate(boxes):
                n = self.read_count(grey, (x, y, w, h))
                if n is None:
                    self.keys.append(((x, y, w, h), None, None, "no count"))
                    continue                               # no count: not a potion (a skill, or empty)
                pad = int(SLOT_SLACK * s0)
                x0, y0 = max(0, x - pad), max(0, y - pad)
                hits = self._classify(img[y0:y + h + pad, x0:x + w + pad],
                                      [self.digit_scale * f for f in ICON_STEPS])
                # the potion's picture sits in the middle of its key (one that's off to a side
                # is something else lining up with the key's edges)
                hits = [o for o in hits if abs(x0 + o[2] + o[4] / 2 - (x + w / 2)) <= 0.2 * w
                        and abs(y0 + o[3] + o[5] / 2 - (y + h / 2)) <= 0.2 * h]
                if hits:
                    _, key, hx, hy, hw, hh, hs = hits[0]
                    self.slots[i] = (key, hs, x0 + hx, y0 + hy, hw, hh, (x, y, w, h))
                    self.keys.append(((x, y, w, h), n, key, ""))
                else:
                    near = ", ".join(f"{k} {v:.0f}" + (f"/{sh:.2f}" if sh is not None else "")
                                     for v, k, sh in self.closest[:2])
                    self.keys.append(((x, y, w, h), n, None, f"no potion matched (closest: {near})"))
        counts, gone = {}, []
        for i, (key, s, x, y, w, h, box) in self.slots.items():
            pad = max(3, int(0.15 * w))
            x0, y0 = max(0, x - pad), max(0, y - pad)
            hit = self._classify(img[y0:y + h + pad, x0:x + w + pad], [s], keys={key})
            if not hit:                                # moved, or something else there now
                gone.append(i)
                continue
            x, y = x0 + hit[0][2], y0 + hit[0][3]
            self.slots[i] = (key, s, x, y, w, h, box)
            n = self.read_count(grey, box)
            self.found.append((key, (x, y, w, h), n))
            if n is None:
                continue
            # the same potion on two keys shows the same total; if they differ, trust neither
            counts[key] = n if counts.get(key, n) == n else None
        for i in gone:
            del self.slots[i]
            self.next_search = min(self.next_search, now + 4)
        return {k: v for k, v in counts.items() if v is not None and v <= COUNT_MAX}


class PotionTracker:
    """Potions used and picked up since Start, from the quickslot's counts.

    A new count only counts once it's read the same twice in a row (three times for a change
    of more than 20, or a different number of digits), so a misread never shows up as potions
    used. A change of more than 100 at once is a trip to storage, or potions moved around:
    it starts counting afresh from the new number. Changes while paused aren't counted.

    Potions picked up go in `found` (kept from one session to the next, and set by hand too),
    and one used is taken from there first: a found one costs nothing, only a bought one does.
    """
    REBASE = 100

    def __init__(self, found=None):
        self.found = found if found is not None else {}     # key -> found potions not used yet
        self.changed = False        # `found` changed (to be saved)
        self.reset()

    def reset(self):
        self.counts = {}            # key -> confirmed count
        self._candidate = {}        # key -> (count, readings in a row)
        self.used = {}              # key -> potions used
        self.free = {}              # key -> ...of which found ones
        self.picked = {}            # key -> potions picked up

    def observe(self, counts, counting):
        """counts: {key: count} as read; counting: tracking is on."""
        for key, n in counts.items():
            old = self.counts.get(key)
            if n == old:
                self._candidate.pop(key, None)
                continue
            last, seen = self._candidate.get(key, (None, 0))
            seen = seen + 1 if n == last else 1
            self._candidate[key] = (n, seen)
            big = old is not None and (abs(n - old) > 20 or len(str(n)) != len(str(old)))
            if seen < (3 if big else 2):
                continue
            self._candidate.pop(key, None)
            self.counts[key] = n
            if old is None or not counting or abs(n - old) > self.REBASE:
                continue
            if n > old:
                self.picked[key] = self.picked.get(key, 0) + n - old
                self.found[key] = self.found.get(key, 0) + n - old
            else:
                free = min(self.found.get(key, 0), old - n)
                self.used[key] = self.used.get(key, 0) + old - n
                if free:
                    self.free[key] = self.free.get(key, 0) + free
                    self.found[key] -= free
            self.changed = True

    def bought(self, key):
        """Potions of this kind used that weren't found ones."""
        return self.used.get(key, 0) - self.free.get(key, 0)

    @staticmethod
    def _worth(amounts, prices):
        return sum(n * prices.get(k, 0) for k, n in amounts.items())

    def cost(self, prices):
        """Mesos worth of the potions used."""
        return self._worth(self.used, prices)

    def net(self, prices, found_kinds=()):
        """What potions cost: the bought ones used. Found ones are free, and so is every potion in
        found_kinds (the second potion of a kind on the quickslot: see the app's found_keys)."""
        return sum(self.bought(k) * prices.get(k, 0) for k in self.used if k not in found_kinds)

    def covered(self, prices, found_kinds=()):
        """Mesos worth of the found potions among the ones used (free)."""
        return self.cost(prices) - self.net(prices, found_kinds)

    @property
    def seen(self):
        return bool(self.counts)
