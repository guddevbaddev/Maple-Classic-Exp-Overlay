"""Potions and other supplies used from the hotbar: how many, and what they cost.

The hotbar's counts are read from the screen (one count per slot); a slot whose count goes down
is being used. What's in a slot is told apart by its icon (a small fingerprint of it), and is
named once by the player. The price is the shop price in the town nearest the map you're on, or
the price the player set for it (bought from other players, or a shop not listed here).

Prices are the NPC shop prices meowdb.com lists for MapleStory Classic (from in-game footage).
Anything not listed has no price until the player sets one."""
from collections import deque

# Shop prices that are the same in every town that sells them.
BASE_PRICES = {
    "Red Potion": 50, "Orange Potion": 150, "White Potion": 350, "Blue Potion": 240,
    "Warrior Potion": 500, "Magic Potion": 500, "Sniper Potion": 500, "Dexterity Potion": 500,
    "Speed Potion": 500,
}
# What a town's shop charges differently, or sells only there.
TOWN_PRICES = {
    "Orbis": {"Blue Potion": 220},
    "El Nath": {"Blue Potion": 220, "Pure Water": 1120, "Sunrise Dew": 3000, "Sunset Dew": 3750},
}
# Items to pick from when naming a slot: priced ones, and common ones whose price is set by hand.
ITEMS = sorted({*BASE_PRICES, *(i for t in TOWN_PRICES.values() for i in t),
                "Mana Elixir", "Elixir", "Power Elixir", "Arrows for Bow", "Arrows for Crossbow",
                "Throwing Stars"})

# The town each area's maps are nearest to, by words in the map's name (checked in order).
TOWN_AREAS = [
    ("El Nath", ("el nath", "dead mine", "ice valley", "snowy", "sharp cliff", "orbis tower")),
    ("Orbis", ("orbis", "garden of", "cloud park", "stairway to the sky", "entrance to the garden")),
    ("Ludibrium", ("ludibrium", "eos tower", "helios tower", "toy factory", "path of time",
                   "kentaurus", "ludus")),
    ("Sleepywood", ("sleepywood", "ant tunnel", "dungeon", "drake", "cave of evil eye",
                    "another entrance", "deep sleepywood")),
    ("Perion", ("perion", "rocky", "excavation site", "camp", "wild boar", "burnt land",
                "east rocky", "west rocky", "iron boar", "dangerous valley", "ruins of excavation",
                "perion street")),
    ("Kerning City", ("kerning", "subway", "swamp", "construction site", "line 1", "wetland",
                      "the swamp of despair")),
    ("Henesys", ("henesys", "mushroom", "pig beach", "hunting ground", "pig park", "split road",
                 "the field east of henesys", "the forest east of henesys")),
    ("Ellinia", ("ellinia", "forest", "tree dungeon", "the tree", "fairy")),
    ("Lith Harbor", ("lith harbor", "lith", "port road", "beach", "dolphin")),
]


def nearest_town(map_name):
    """The town nearest a map, from its name, or None if it's not known."""
    name = (map_name or "").lower()
    for town, words in TOWN_AREAS:
        if any(w in name for w in words):
            return town
    return None


def shop_price(item, town):
    """The shop price of an item in a town (or anywhere, for town None), or None if unknown."""
    if town and item in TOWN_PRICES.get(town, {}):
        return TOWN_PRICES[town][item]
    return BASE_PRICES.get(item)


def price(item, town, custom):
    """What one costs: the player's own price for it if they set one, else the shop's."""
    if item in custom:
        return custom[item]
    return shop_price(item, town)


class SupplyTracker:
    """Counts what each hotbar slot uses up, from readings of its count.

    A new count only counts once two readings in a row agree on it. Going down counts as used;
    going up (bought more, or moved some in) or down by more than half at once (moved away, or a
    misread) starts that slot afresh. A slot whose icon changes is a different item: afresh too.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.slots = {}                       # slot -> {"count", "icon", "pending", "used"}
        self.used = {}                        # icon fingerprint -> total used while counting
        self.samples = deque()                # (elapsed, {icon: used so far}) for windows
        self.start = None                     # elapsed when counting began

    def observe(self, counts, elapsed, running):
        """counts: {slot: (count, icon fingerprint)} from one look at the hotbar."""
        changed = False
        for slot, (count, icon) in counts.items():
            s = self.slots.get(slot)
            if s is None or s["icon"] != icon:
                self.slots[slot] = {"count": None, "icon": icon, "pending": (count, 1)}
                continue
            if count == s["count"]:
                s["pending"] = None
                continue
            last = s["pending"]
            n = last[1] + 1 if last and last[0] == count else 1
            s["pending"] = (count, n)
            if n < 2 and s["count"] is not None:
                continue
            old, s["count"], s["pending"] = s["count"], count, None
            if old is None or not running:
                continue
            drop = old - count
            if 0 < drop <= max(3, old // 2):  # used (not moved away, not a misread)
                self.used[icon] = self.used.get(icon, 0) + drop
                changed = True
        if running and self.start is None:
            self.start = elapsed
            self.samples.append((elapsed, dict(self.used)))
        elif running and changed:
            self.samples.append((elapsed, dict(self.used)))
            while len(self.samples) > 2 and self.samples[1][0] <= elapsed - 3600:
                self.samples.popleft()

    def in_use(self):
        """Icon fingerprints of what's been used, most used first."""
        return sorted(self.used, key=lambda i: -self.used[i])

    def used_in_last(self, icon, seconds, elapsed):
        """(how many were used in the last `seconds` of tracking, seconds that covers), or None."""
        if self.start is None or elapsed - self.start < 10:
            return None
        before = next((u.get(icon, 0) for t, u in reversed(self.samples) if t <= elapsed - seconds), 0)
        return self.used.get(icon, 0) - before, min(seconds, elapsed - self.start)

    def per_hour(self, icon, elapsed):
        if self.start is None or elapsed - self.start < 30:
            return None
        return self.used.get(icon, 0) / (elapsed - self.start) * 3600
