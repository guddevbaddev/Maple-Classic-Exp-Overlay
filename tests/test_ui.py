"""Drives the real overlay window (it needs a screen, so it isn't part of test_logic.py): the notes
box under the log. Run from the project folder:  py -3 tests/test_ui.py

It uses its own temporary data folder and never goes online."""
import json
import os
import sys
import tempfile
import time
from pathlib import Path

DATA = Path(tempfile.mkdtemp())
os.environ["MAPLE_EXP_DATA"] = str(DATA)                    # never touch your real data
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import maple_exp as m  # noqa: E402

failures = 0


def check(name, ok):
    global failures
    print(("PASS " if ok else "FAIL ") + name)
    failures += not ok


def farm(log, t0, seconds, party=1, map_name="Rocky Road II", level=27):
    t, nxt = t0, t0
    while t < t0 + seconds:
        if t >= nxt:
            log.gain(t, 100)
            nxt = t + 3
        log.tick(t, map_name, level, party, None, "Bandit")
        t += 0.5
    return t


def on_disk():
    return {(e["map"], e["party"]): e.get("note") for e in
            json.loads((DATA / "exp_log.json").read_text(encoding="utf-8"))["entries"]}


# a log to look at: one solo line, and one map played in parties of 4 and 5 (shown as one line)
seed = m.AutoLog(15, m.LOG_PATH, m.LOG_TEXT_PATH)
t = farm(seed, 0, 310, party=1, map_name="Ant Tunnel I")
t = farm(seed, t + 60, 310, party=4, map_name="Wild Boar Land II", level=30)
t = farm(seed, t + 60, 310, party=5, map_name="Wild Boar Land II", level=30)
m.save_config({**m.DEFAULTS, "log_open": True, "pos": [60, 60], "hotkeys_on": False, "check_updates": False})

root = m.tk.Tk()
app = m.App(root, m.DigitTemplates.load())
root.update()
tree, box = app.log_tree, app.note_text


def pump(seconds=0.0):
    end = time.time() + seconds
    root.update()
    while time.time() < end:
        root.update()
        time.sleep(0.02)


def row(map_name, group=False):
    for iid in tree.get_children():
        if tree.item(iid, "values")[1] == map_name and (iid in app.groups) == group:
            return iid


def select(iid):
    tree.selection_set(iid)
    pump(0.1)


def type_note(text):
    box.insert("end", text)
    pump(0.1)


solo, group = row("Ant Tunnel I"), row("Wild Boar Land II", group=True)
check("the log has a solo line and one shared party line", solo and group)
check("the Note column is there, empty to begin with",
      "note" in tree["columns"] and tree.item(solo, "values")[8] == "" and tree.item(group, "values")[8] == "")
check("with no line selected, the note box can't be typed in", str(box.cget("state")) == "disabled")

# a solo line
select(solo)
check("selecting a line opens its note", str(box.cget("state")) == "normal" and "Ant Tunnel I" in app.note_title.cget("text")
      and "only" in app.note_title.cget("text").lower())
type_note("Good drops, bring pots!")
check("what's typed isn't saved at once (it waits for a pause)", on_disk()[("Ant Tunnel I", 1)] is None)
pump(1.3)
check("...but a moment later it's saved in the log file", on_disk()[("Ant Tunnel I", 1)] == "Good drops, bring pots!")
check("...and the line gets its mark", tree.item(solo, "values")[8] == m.NOTE_MARK and "saved" in app.note_title.cget("text"))

# moving to another line saves the one left, and shows the other's note
type_note(" More")
select(group)
check("clicking another line saves the note being typed", on_disk()[("Ant Tunnel I", 1)] == "Good drops, bring pots! More")
check("the other line's box is empty and ready", box.get("1.0", "end-1c") == "" and str(box.cget("state")) == "normal")

# a shared party line: one note for all of its party sizes
type_note("Pt of 4-5 works.\nKS-ing.")
select(solo)
check("a note on a shared party line goes on each party size", on_disk()[("Wild Boar Land II", 4)] == on_disk()[("Wild Boar Land II", 5)]
      == "Pt of 4-5 works.\nKS-ing.")
check("...and shows on the shared line", tree.item(group, "values")[8] == m.NOTE_MARK)
tree.item(group, open=True)
app._sync_group(group)
child = tree.get_children(group)[0]
select(child)
check("opening it, each party size shows the same note", box.get("1.0", "end-1c") == "Pt of 4-5 works.\nKS-ing."
      and tree.item(child, "values")[8] == m.NOTE_MARK)

# the log refreshes by itself every few minutes: that must not disturb a note being typed
select(solo)
box.mark_set("insert", "1.4")
type_note("\n(typed while the log refilled)")
before = box.get("1.0", "end-1c")
app._fill_log()
pump(0.3)
check("a refilled log keeps the same line selected", tree.selection() == (row("Ant Tunnel I"),))
check("...keeps what's being typed", box.get("1.0", "end-1c") == before)
check("...and saved it first", on_disk()[("Ant Tunnel I", 1)] == before)

# renaming a map keeps its note
app.autolog.rename(app.autolog.entries[[e["map"] for e in app.autolog.entries].index("Ant Tunnel I")], "Ant Tunnel One")
app._fill_log()
pump(0.2)
check("renaming a map keeps its note", on_disk()[("Ant Tunnel One", 1)] == before and tree.item(row("Ant Tunnel One"), "values")[8] == m.NOTE_MARK)
check("...and the box goes empty (that line is gone under its old name)", str(box.cget("state")) == "disabled")

# typing needs the hotkeys out of the way: Shift+1 is "!"
select(row("Ant Tunnel One"))
box.event_generate("<FocusIn>")
pump(0.1)
check("hotkeys are off while typing a note", getattr(app.hotkeys, "_paused", True) is True)
box.event_generate("<FocusOut>")
pump(0.1)
check("...and back on after", getattr(app.hotkeys, "_paused", False) is False)

# an over-long note is cut to the limit, in the box too
select(row("Ant Tunnel One"))
box.delete("1.0", "end")
box.insert("1.0", "x" * (m.NOTE_MAX + 500))
pump(1.3)
check("a note longer than the limit is cut to it", len(box.get("1.0", "end-1c")) == m.NOTE_MAX
      and len(on_disk()[("Ant Tunnel One", 1)]) == m.NOTE_MAX)

# deleting a line with a note says so
asked = []
m.messagebox.askyesno = lambda title, text, **k: asked.append(text) or False
app._delete([app.shown[row("Ant Tunnel One")]])
check("deleting a line that has a note says its note goes too", asked and "note on it will be deleted too" in asked[0])

# closing the overlay (or hiding the log) saves a note still being typed
select(row("Ant Tunnel One"))
box.delete("1.0", "end")
type_note("last words")
app.set_compact(True)
check("switching to compact mode saves a note being typed", on_disk()[("Ant Tunnel One", 1)] == "last words")
app.set_compact(False)
pump(0.3)
select(row("Ant Tunnel One"))
type_note(" and one more")
app.close()
check("closing the overlay saves a note being typed", on_disk()[("Ant Tunnel One", 1)] == "last words and one more")
saved = json.loads((DATA / "exp_log.json").read_text(encoding="utf-8"))["entries"]
check("every line is still as the overlay wrote it (notes don't break the seal)",
      all(not m.AutoLog(15, m.LOG_PATH, m.LOG_TEXT_PATH).edited(e) for e in saved))

# ---- the design: every size, every state, and awkward values never break the window
root = m.tk.Tk()
m.save_config({**m.DEFAULTS, "hotkeys_on": False, "check_updates": False, "pos": [60, 60]})
app = m.App(root, m.DigitTemplates.load())
t, meso = app.tracker, app.meso
sizes_ok, widths = True, {}
for scale in m.UI_SCALES:
    try:
        app.cfg["ui_scale"] = scale
        app._apply_ui_scale()
        for case in ("idle", "tracking", "huge", "compact", "details"):
            if case == "idle":
                t.exp = t.pct = t.req = None
                t.rate = lambda: None
                t.rolling_rate = lambda: None
            else:
                t.exp, t.pct, t.req, t.gained, t.levels = 31204, 54.2, 57600, 412300, 2
                huge = case == "huge"
                t.rate = lambda huge=huge: 123456789.0 if huge else 72566.0
                t.rolling_rate = lambda huge=huge: 99999999.0 if huge else 71900.0
                t.elapsed = lambda: 5620.0
                meso.value, meso.gained = 18449220, 41000
                app.level = 35
            app.set_compact(case == "compact")
            if case == "details" and not app.view.details_open:
                app.view._toggle_details()
            app.session.on = case != "idle"
            app._update_display()
            root.update()
            widths[scale] = app.view.winfo_width()
    except Exception as e:                                   # (printed, so a failure says where)
        print("   error at", scale, "%:", type(e).__name__, e)
        sizes_ok = False
check("the window draws at every size (80% to 200%) and in every state: idle, tracking, huge numbers, compact, details", sizes_ok)
check(f"a bigger size makes the window wider, not clipped ({widths})",
      all(widths[a] < widths[b] for a, b in zip(m.UI_SCALES, m.UI_SCALES[1:])))
app.view.show(rate="123,456,789", state="alert", state_text="Can't read the EXP bar",
              message="A very long message " * 12, tiles={"Last 5 min": "99,999,999", "Mesos / hr": "-", "Elapsed": "123:59:59"})
root.update()
check("long messages and big numbers still fit the window", app.view.winfo_reqwidth() <= app.theme.px(400) + 4)
app.set_compact(False)
app.set_compact(True)
app._update_display()
hero = app.view.hero
check("compact mode shows mesos/hr under the number, and only there",
      hero.itemcget(hero._mval, "state") == "normal" and hero.itemcget(hero._mval, "text") != "")
app.set_compact(False)
app._update_display()
check("full mode doesn't show that line (it has the tile)", hero.itemcget(hero._mval, "state") == "hidden")
picked = []
selector = m.RegionSelector(root, picked.append)             # (it crashed on Windows in 0.9.7 and 0.9.8-beta)
root.update()
check("Select area opens its full-screen picker", selector.win.winfo_exists())
selector._finish(None)
check("...and Esc closes it without choosing anything", picked == [None] or picked == [])
import numpy as np
fake = m.Reading(*([None] * len(m.Reading._fields)))._replace(
    where="MapleStory window 1920x1080", text="3,060 [1.04%]", image=np.full((40, 200, 3), 60, np.uint8), boxes=[])
app.last_capture = fake
app.job = None
app.reader.job_look = {"image": np.full((60, 300, 3), 90, np.uint8), "boxes": [(10, 10, 80, 40, "exp")],
                       "why": "the tries didn't agree on what it says"}
before = set(root.winfo_children())
app.view_capture()
root.update()
win = next(w for w in set(root.winfo_children()) - before)
texts = " | ".join(w.cget("text") for w in win.winfo_children() if w.winfo_class() == "Label" and w.cget("text"))
check("View capture says why the class wasn't read", "Class. Not read: the tries didn't agree" in texts)
win.destroy()
app.reader.job_look = {"image": None, "boxes": [], "why": "this window is covering the class name: move it"}
app.view_capture(); root.update()
win = next(w for w in set(root.winfo_children()) - before)
check("...and works when there is no picture (the overlay is in the way)",
      "covering the class name" in " ".join(w.cget("text") for w in win.winfo_children() if w.winfo_class() == "Label"))
win.destroy()
app.reader.box = (700, 1000, 200, 30)                          # (the EXP bar is found: only then is the class worth asking about)
files = app._save_report_files(False)
text = app._report_text(files)
check("a bug report says why the class wasn't read", "Class not read: this window is covering the class name" in text)
check("it saves a picture, and the details as a text file", files["picture"].exists() and files["details"].exists())
check("...with the whole story in the text file", all(w in files["details"].read_text(encoding="utf-8")
                                                      for w in ("== Game window ==", "== What it found ==", "== What happened")))
check("the web address a report is opened with stays short enough",
      len(m.urllib.parse.urlencode({"title": "x", "body": text})) < 7000)
check("it never contains the Windows user name",
      not any(len(s) > 2 and s in text + files["details"].read_text(encoding="utf-8")
              for s in {str(m.Path.home()), m.os.environ.get("USERNAME", "")}))
print(text)
app.job, app.reader.job_look, app.last_capture = None, None, None
app.reader.box = None
# ---- every Size at every Windows scaling: nothing drawn outside its box, nothing cut off, nothing broken
def spill(widget, slack=2):
    """Texts or pictures that stick out of the canvas they're drawn in (listed by kind)."""
    bad = []
    for canvas in [widget] + [c for c in widget.winfo_children()]:
        stack = [canvas]
        while stack:
            c = stack.pop()
            stack.extend(c.winfo_children())
            if c.winfo_class() != "Canvas" or not c.winfo_ismapped():
                continue
            c.update_idletasks()
            w, h = c.winfo_width(), c.winfo_height()
            for item in c.find_all():
                if c.type(item) != "text" or c.itemcget(item, "state") == "hidden" or not c.itemcget(item, "text"):
                    continue
                x0, y0, x1, y1 = c.bbox(item)
                if x0 < -slack or y0 < -slack or x1 > w + slack or y1 > h + slack:
                    bad.append(f"{c.itemcget(item, 'text')[:18]!r} {x0},{y0},{x1},{y1} in {w}x{h}")
    return bad


app._check_screen = lambda: None                          # (it would put the screen's own scaling back)
layout_bad = []
for dpi in (96, 120, 144, 192):                          # Windows scaling 100%, 125%, 150%, 200%
    app._dpi = dpi
    for scale in m.UI_SCALES:
        app.cfg["ui_scale"] = scale
        app._apply_ui_scale()
        for case in ("tracking", "huge", "compact", "details"):
            t.exp, t.pct, t.req, t.gained, t.levels = 31204, 54.2, 57600, 412300, 2
            huge = case == "huge"
            t.rate = lambda huge=huge: 123456789.0 if huge else 72566.0
            t.rolling_rate = lambda huge=huge: 99999999.0 if huge else 71900.0
            t.elapsed = lambda: 5620.0
            meso.value, meso.gained = 18449220, 41000
            app.level = 35
            app.set_compact(case == "compact")
            if case == "details" and not app.view.details_open:
                app.view._toggle_details()
            if case != "details" and app.view.details_open:
                app.view._toggle_details()
            app.session.on = True
            app._update_display()
            root.update()
            for line in spill(app.view):
                layout_bad.append(f"{dpi}dpi {scale}% {case}: {line}")
        app.set_compact(False)
check("at every Size and Windows scaling, no text sticks out of its box on the main window"
      + (f" ({len(layout_bad)} problems, first: {layout_bad[:3]})" if layout_bad else ""), not layout_bad)

fonts_small = []
for dpi in (96, 120, 144, 192):
    app._dpi = dpi
    for scale in m.UI_SCALES:
        app.cfg["ui_scale"] = scale
        app._apply_ui_scale()
        for name, f in app.fonts.items():
            if abs(int(f.cget("size"))) < 9:
                fonts_small.append(f"{dpi}dpi {scale}% {name} {f.cget('size')}")
        for (weight, size), f in app.theme._tk.items():
            if abs(int(f.cget("size"))) < m.MIN_TEXT_PX if hasattr(m, "MIN_TEXT_PX") else False:
                fonts_small.append(f"{dpi}dpi {scale}% {weight} {size}")
check(f"text never gets smaller than the readable minimum ({fonts_small[:3]})", not fonts_small)

# the window, the log and Settings still fit their contents at the smallest and biggest sizes
fit_bad = []
for dpi in (96, 192):
    app._dpi = dpi
    for scale in (60, 70, 100, 200):
        app.cfg["ui_scale"] = scale
        app._apply_ui_scale()
        app.set_compact(False)
        if not app.log_open:
            app.toggle_log()
        root.update()
        tree = app.log_tree
        headfont = m.tkfont.nametofont("TkHeadingFont") if "TkHeadingFont" in m.tkfont.names(root) else app.fonts["text"]
        for col in tree["columns"]:
            need = app.fonts["text"].measure(tree.heading(col, "text") or "") + 6
            if int(tree.column(col, "width")) + 2 < min(need, 40):
                fit_bad.append(f"{dpi}dpi {scale}% log column {col}")
        app.open_settings()
        sw = app.settings_win
        sw.geometry("")
        sw.update()
        for child in sw.winfo_children():
            stack = [child]
            while stack:
                c = stack.pop()
                stack.extend(c.winfo_children())
                if c.winfo_ismapped() and (c.winfo_rootx() + c.winfo_width() > sw.winfo_rootx() + sw.winfo_width() + 2
                                           or c.winfo_rooty() + c.winfo_height() > sw.winfo_rooty() + sw.winfo_height() + 2):
                    fit_bad.append(f"{dpi}dpi {scale}% settings: {c.winfo_class()} sticks out")
        for line in spill(sw):
            fit_bad.append(f"{dpi}dpi {scale}% settings: {line}")
        sw.destroy()
        app.settings_win = None
        app.toggle_log()
check(f"the log and Settings fit at the smallest and biggest Sizes ({fit_bad[:3]})", not fit_bad)
app._dpi = 192 if app._dpi not in (96, 120, 144, 192) else app._dpi
app.cfg["ui_scale"] = 100
app._apply_ui_scale()

# ---- Size and Transparency limits
check("sizes from 60% to 200% are offered", m.UI_SCALES[0] == 60 and m.UI_SCALES[1] == 70 and m.UI_SCALES[-1] == 200)
saved = m.CONFIG_PATH
cfg_file = Path(tempfile.mkdtemp()) / "config.json"
cfg_file.write_text(json.dumps({"transparency": 90, "ui_scale": 70}), encoding="utf-8")
m.CONFIG_PATH = cfg_file
loaded = m.load_config()
m.CONFIG_PATH = saved
check("an older config with transparency 90 loads as the 40% limit, and a saved 70% size is kept",
      loaded["transparency"] == 40 and loaded["ui_scale"] == 70)
cfg_file.write_text(json.dumps({"transparency": -5, "ui_scale": 65}), encoding="utf-8")
m.CONFIG_PATH = cfg_file
loaded = m.load_config()
m.CONFIG_PATH = saved
check("a negative transparency is 0, and a size that isn't offered is 100%", loaded["transparency"] == 0 and loaded["ui_scale"] == 100)
check("transparency can't go past 40%", m.MAX_TRANSPARENCY == 40)

# ---- the transparency slider stops at the limit, and the window can't fade past it
app.cfg["transparency"] = 90
app._apply_window_settings()
check("the window is never more see-through than the limit (opacity %.2f)" % float(root.attributes("-alpha")),
      float(root.attributes("-alpha")) >= 1 - m.MAX_TRANSPARENCY / 100 - 0.01)
app.cfg["transparency"] = 0
app._apply_window_settings()

# ---- hotkeys in Settings: one waiting at a time, and clicking it again cancels
if app.hotkeys.supported:
    app.open_settings()
    sw = app.settings_win
    sw.update()
    ui = app._hotkey_ui
    names = list(ui["buttons"])
    keys_before = dict(app.cfg["hotkeys"])
    texts = lambda: {a: b.itemcget(b._txt, "text") for a, b in ui["buttons"].items()}
    ui["choose"](names[0])
    check("clicking a hotkey makes it wait for keys", ui["choosing"]["action"] == names[0] and texts()[names[0]] == "Press keys...")
    ui["choose"](names[1])
    t2 = texts()
    check("clicking another one moves the wait to it: only one says Press keys",
          ui["choosing"]["action"] == names[1] and sum(v == "Press keys..." for v in t2.values()) == 1
          and t2[names[0]] == (keys_before[names[0]] or "Off"))
    ui["choose"](names[1])
    check("clicking the waiting one again cancels it, and every key is as it was",
          ui["choosing"]["action"] is None and texts() == {a: (keys_before[a] or "Off") for a in names}
          and app.cfg["hotkeys"] == keys_before)
    check("hotkeys work again after cancelling", getattr(app.hotkeys, "_paused", True) is False)
    ui["choose"](names[2])
    esc = type("E", (), {"keysym": "Escape", "state": 0, "keycode": 27})()
    ui["pressed"](esc)
    check("Esc cancels too, keeping the key", ui["choosing"]["action"] is None and app.cfg["hotkeys"] == keys_before)
    ui["choose"](names[3])
    back = type("E", (), {"keysym": "BackSpace", "state": 0, "keycode": 8})()
    ui["pressed"](back)
    check("Backspace turns that hotkey off", app.cfg["hotkeys"][names[3]] == "" and ui["choosing"]["action"] is None)
    app.cfg["hotkeys"].update(keys_before)
    m.save_config(app.cfg)
    ui["choose"](names[0])
    ui["on"].set(False)
    sw.update()
    check("turning hotkeys off while one is waiting ends the wait", ui["choosing"]["action"] is None)
    ui["on"].set(True)
    sw.update()
    sw.destroy()
    app.settings_win = None
    check("closing Settings leaves hotkeys working", getattr(app.hotkeys, "_paused", True) is False)

# ---- the Share button: a picture of the session, copied to paste into Discord
copied = []
real_copy = m.PLATFORM.copy_image
m.PLATFORM.copy_image = lambda path: copied.append(path) or True
t = app.tracker
t.rate = lambda: None
said = []
real_info = m.messagebox.showinfo
m.messagebox.showinfo = lambda title, text, **kw: said.append(text)
app.share_card()                                          # nothing yet: says so (no card)
m.messagebox.showinfo = real_info
root.update()
check("Share before there's an EXP/hr makes no card, and says why", not copied and "Nothing to share yet" in said[0])
t.exp, t.pct, t.req, t.gained, t.levels = 31204, 54.2, 57600, 412300, 2
t.rate = lambda: 72566.0
t.elapsed = lambda: 3753.0
app.map_name, app.level, app.job, app.party = "Sleepywood Dungeon IV", 35, "Hermit", 4
app.share_card()
root.update()
card = m.DATA_DIR / "share-card.png"
check("Share makes the card and copies it", copied == [card] and card.is_file())
from PIL import Image
with Image.open(card) as img:
    check(f"the card is a big, sharp picture ({img.size})", img.size == (1280, 688))
check("...and shows it, saying it was copied", app.card_win.winfo_exists() and "Copied!" in " ".join(
    str(w.cget("textvariable") and w.getvar(w.cget("textvariable"))) for w in app.card_win.winfo_children()
    if w.winfo_class() == "Label"))
stats = app._card_stats()
check("the card shows EXP/hr, mesos/hr, the map, level, class and party",
      (stats.exp_hr, stats.map_name, stats.level, stats.job, stats.party, stats.elapsed)
      == ("72,566", "Sleepywood Dungeon IV", 35, "Hermit", "4ppl party", "1:02:33"))
check("...and nothing from the log's notes, or who you are",
      not any(f in m.CardStats.__dataclass_fields__ for f in ("note", "notes", "name", "character")))
app.pq_mode = True
check("in PQ mode, the card says Party Quest", app._card_stats().map_name == m.PQ_MAP)
app.pq_mode = False
m.PLATFORM.copy_image = lambda path: False
app.share_card()
root.update()
said = " ".join(w.getvar(w.cget("textvariable")) for w in app.card_win.winfo_children()
               if w.winfo_class() == "Label" and w.cget("textvariable"))
check(f"where copying doesn't work, it says to drag the file in ({said!r})", "drag the picture" in said)
app.card_win.destroy()
m.PLATFORM.copy_image = real_copy

# ---- Settings > Save logs: the logs in one zip, to send
import zipfile
m.log_error("an error for the logs test", RuntimeError(str(Path.home())))      # (a path with the user name)
(m.DATA_DIR / "crash.log").write_text("Fatal Python error: Segmentation fault\n", encoding="utf-8")
shown, said = [], []
real_show, real_info = m.PLATFORM.show_file, m.messagebox.showinfo
m.PLATFORM.show_file = shown.append
m.messagebox.showinfo = lambda title, text, **kw: said.append(text)
saved = app.save_logs()
m.PLATFORM.show_file, m.messagebox.showinfo = real_show, real_info
names = zipfile.ZipFile(saved).namelist() if saved else []
check(f"Save logs makes one zip with the logs and the report details, and shows it ({names})",
      shown == [saved] and {"errors.log", "crash.log", "overlay.log", "bug-report-details.txt"} <= set(names))
everything = " ".join(zipfile.ZipFile(saved).read(n).decode("utf-8") for n in names)
check("...without the user name, and with the crash in the details",
      str(Path.home()) not in everything and "Segmentation fault" in everything)
asked = []
real_ask = m.messagebox.askyesno
m.messagebox.askyesno = lambda title, text, **kw: asked.append(text) or False
app.tell_last_crash()
m.messagebox.askyesno = real_ask
check("after a crash, the next start says so and offers to save the logs", asked and "Save logs" in asked[0])

# ---- Update now: in the update window when it's the download, and what happens when it's clicked
import time as _time
zip_name = m.updater.asset_names("9.9.9", sys.platform == "darwin")[0]
assets = {zip_name: "https://github.com/x/releases/download/v9.9.9/z", "SHA256SUMS.txt": "https://github.com/x/s"}
real_where, real_prepare, real_install, real_close = (m.updater.installed_location, m.updater.prepare,
                                                      m.updater.start_install, app.close)
texts = lambda w: " ".join(str(getattr(c, "text", "")) for c in w.winfo_children() + [
    g for f in w.winfo_children() for g in f.winfo_children()])
m.updater.installed_location = lambda: None
app._show_update(("9.9.9", "Fixes.", assets), True, None)
root.update()
check("running from source, there's no Update now (only the download page)", "Update now" not in texts(app.update_win))
app.update_win.destroy()
m.updater.installed_location = lambda: Path(tempfile.mkdtemp())
app._show_update(("9.9.9", "Fixes.", assets), True, None)
root.update()
check("the download gets an Update now button", "Update now" in texts(app.update_win))
installs, closed = [], []
m.updater.prepare = lambda version, assets, opener, progress, mac: (progress(5_000_000, 60_000_000), ("NEW", "WORK"))[1]
m.updater.start_install = lambda new, installed, work, log: installs.append((new, work))
app.close = lambda: closed.append(True)
app._update_progress = m.tk.StringVar(value="")
app.start_update("9.9.9", assets, Path("INSTALLED"))
for _ in range(50):
    root.update()
    app._pump()
    if closed:
        break
    _time.sleep(0.05)
check(f"Update now downloads, then closes so the new version is put in place ({installs})",
      installs == [("NEW", "WORK")] and closed == [True])
def failing(*a, **k):
    raise m.updater.UpdateError("the download doesn't match its SHA-256")
m.updater.prepare = failing
closed.clear()
app.start_update("9.9.9", assets, Path("INSTALLED"))
for _ in range(50):
    root.update()
    app._pump()
    if "didn't work" in app._update_progress.get():
        break
    _time.sleep(0.05)
check(f"a failed update changes nothing and says so ({app._update_progress.get()[:60]}...)",
      not closed and "nothing was changed" in app._update_progress.get())
app.update_win.destroy()
m.updater.installed_location, m.updater.prepare, m.updater.start_install, app.close = (real_where, real_prepare,
                                                                                        real_install, real_close)

# ---- the version, at the bottom of the main window (not in compact mode)
root.update()
check(f"the version shows at the bottom ({app.view.version.cget('text')})",
      app.view.version.cget("text") == f"v{m.VERSION}" and app.view.version.winfo_ismapped())
app.set_compact(True); root.update()
check("...but not in compact mode", not app.view.version.winfo_ismapped())
app.set_compact(False); root.update()

# ---- high levels: the EXP bar shows only the %, so the level is asked once and counted up after
asked, real_ask = [], m.simpledialog.askinteger
m.simpledialog.askinteger = lambda *a, **k: (asked.append(k), 62)[1]
app.meso.reset()
app.cfg["level"], app.asked_level, app.tracker.req = 0, False, None
pct = lambda p: m.Reading(where="MapleStory window 1920x1080", confident=True, text=f"[{p:.2f}%]", pct=p)
app._handle(pct(88.50))
root.update()
check(f"a %-only bar asks the level once ({len(asked)})", len(asked) == 1 and app.cfg["level"] == 62)
check("...and keeps it", json.loads(m.CONFIG_PATH.read_text())["level"] == 62)
app.tracker.start()
for p in (88.50, 88.50, 88.60, 99.99, 0.05, 0.07):
    app._handle(pct(p))
root.update()
check(f"...knows Lv {app.level} after a level-up, and remembers it", app.level == 63 and app.cfg["level"] == 63 and len(asked) == 1)
check("...and has the menu item to change it", app.pct_only)
app._handle(m.Reading(where="MapleStory window 1920x1080", candidates=[(68601, 71.68)], confident=True))
check("a bar with the number again isn't %-only", not app.pct_only)
app.tracker.reset()
m.simpledialog.askinteger = real_ask

# ---- potions: what they cost, in Details, and their prices in Settings
app.session.reset()
app.session.on = True
app.tracker.elapsed = lambda: 3600.0
for v in (10000,) * 3 + (14000,) * 3:
    app._handle(m.Reading(where="MapleStory window 1920x1080", mesos=v))
for n in (80, 80, 60, 60, 62, 62):
    app._handle(m.Reading(where="MapleStory window 1920x1080", potions={"red_potion": n}))
app._update_display()
root.update()
details = {name: app.view.details.itemcget(app.view.details._vals[name], "text") for name in ("Potions", "Profit / hr")}
check(f"Profit / hr is also a tile, next to Mesos / hr ({app.view.tiles['Profit / hr'].itemcget(app.view.tiles['Profit / hr']._v, 'text')})",
      app.view.tiles["Profit / hr"].itemcget(app.view.tiles["Profit / hr"]._v, "text") == "3,100")
check(f"Details shows what potions cost and what the picked-up ones covered ({details})",
      details == {"Potions": "-1,000 / +100", "Profit / hr": "3,100"})
tiles = {k: {n: t.itemcget(getattr(t, n), "text") for n in ("_title", "_v", "_sub")} for k, t in app.view.potion_tiles.items()}
check(f"the HP tile shows the potion seen, how many are left, how many an hour and what they cost an hour ({tiles['hp']})",
      tiles["hp"] == {"_title": "RED POTION", "_v": "62 left", "_sub": "20/hr \u00b7 -1,000/hr"})
check(f"the MP tile, with no MP potion on the quickslot, says so ({tiles['mp']})",
      tiles["mp"]["_v"] == "\u2014" and tiles["mp"]["_sub"] == "Not on quickslot")
check("the potion's picture is on its square", app.view.potion_tiles["hp"]._icon_photo is not None
      and app.view.potion_tiles["mp"]._icon_photo is None)
for n in (200, 200):
    app._handle(m.Reading(where="MapleStory window 1920x1080", potions={"red_potion": 62, "white_potion": n}))
app._update_display()
root.update()
hp = app.view.potion_tiles["hp"]
shown = {n: hp.itemcget(getattr(hp, n), "text") for n in ("_title", "_v", "_sub")}
check(f"two HP potions: both named, the one used most first, each one's count, and the HP used an hour of both ({shown})",
      shown == {"_title": "RED + WHITE", "_v": "62 \u00b7 200 left", "_sub": "20/hr \u00b7 -1,000/hr"}
      and hp._more_photo is not None and hp.itemcget(hp._more, "state") == "normal")
hero = app.view.hero
hero.show(eta="Lv 51 in 1 h 37 min")       # (read right away: the window's own refresh shows its real line)
parts = [hero.itemcget(i, "text") for i in (hero._eta, hero._eta_in, hero._eta_time)]
check(f"the level and the time to it are set apart, the time in white ({parts})",
      parts == ["Lv 51", "in", "1 h 37 min"] and hero.itemcget(hero._eta_time, "fill") == __import__("ui_gfx").TEXT
      and hero.bbox(hero._eta)[2] < hero.bbox(hero._eta_time)[0])
shown_meat = app._potion_icon("meat")
cutout = m.Image.open(m.ASSETS / "potions" / "meat.png")
check("a potion recognised by a cut-out picture is shown whole (assets/potions/display/)",
      shown_meat is not None and shown_meat.size != cutout.size)
app.set_compact(True); root.update()
check("compact mode hides the potion tiles", not app.view.potions_row.winfo_ismapped())
app.set_compact(False); root.update()
check("...and the full window shows them", app.view.potions_row.winfo_ismapped())
dialog = app.open_potion_prices()
root.update()
entries = [w for w in dialog.winfo_children()[0].winfo_children() if isinstance(w, m.tk.Entry)]
check(f"Potion prices lists every potion, at the shop's price ({len(entries)})",
      len(entries) == len(app.reader.quickslot.catalog) and entries[0].get() == "50")
entries[0].delete(0, "end")
entries[0].insert(0, "80")
stack, buttons = [dialog], []
while stack:
    w = stack.pop()
    buttons += [w] if isinstance(w, m.Button) else []
    stack.extend(w.winfo_children())
next(b for b in buttons if b.text == "Save").command()
root.update()
check("a price changed there is saved and used", app.cfg["potion_prices"] == {"red_potion": 80}
      and json.loads(m.CONFIG_PATH.read_text())["potion_prices"] == {"red_potion": 80}
      and app.potion_prices()["red_potion"] == 80)
app.session.reset()

# ---- the low-potion sound: each potion used once it's down to "Warn at" (15 to start with)
beeps, real_sound = [], m.PLATFORM.play_sound
m.PLATFORM.play_sound = lambda wav: (beeps.append(wav), True)[1]
app.session.on = True
check("the low-potion sound is on, at 15 left, to start with",
      app.cfg["low_potion_alert"] is True and app.cfg["low_potions"] == 15)


def potion_count(n, times=2):
    for _ in range(times):
        app._handle(m.Reading(where="MapleStory window 1920x1080", potions={"red_potion": n}))


potion_count(20)
potion_count(16)
check("no sound while there are more than 15", beeps == [])
potion_count(15)
check(f"a sound when one is used and 15 are left ({app.status.get()})",
      len(beeps) == 1 and "Red Potion (15 left)" in app.status.get())
potion_count(14)
potion_count(12)
check(f"...and each time one is used after that ({len(beeps)})", len(beeps) == 3)
potion_count(12, times=4)
check("not again while none is used", len(beeps) == 3)
potion_count(40, times=3)
potion_count(39)
check("restocked above 15: quiet again", len(beeps) == 3)
app.cfg["low_potions"] = 40
potion_count(38)
check("Warn at can be changed (40: one used at 38 left sounds)", len(beeps) == 4)
app.cfg["low_potion_alert"] = False
potion_count(37)
check("turned off, it stays quiet", len(beeps) == 4)
app.cfg["low_potion_alert"], app.cfg["low_potions"] = True, 15
app.session.on = False
potion_count(10, times=3)
check("not while tracking is paused (Pause pressed)", len(beeps) == 4)
app.cfg["alert_volume"] = 0
app.session.on = True
potion_count(9)
check("at volume 0 it's silent", len(beeps) == 4)
app.cfg["alert_volume"] = 70
app.play_alert(100)
loud, quiet = m.alert_sound(100), m.alert_sound(20)
peak = lambda wav: int(np.abs(np.frombuffer(wav[44:], "<i2")).max())
check(f"the sound is a real .wav, louder at a higher volume ({peak(quiet)} < {peak(loud)})",
      beeps[-1] == loud and loud[:4] == b"RIFF" and loud[8:12] == b"WAVE" and 0 < peak(quiet) < peak(loud) <= 32767
      and peak(m.alert_sound(0)) == 0)
m.PLATFORM.play_sound = real_sound
app.session.reset()
app.low_counts = {}
del app.tracker.elapsed

if sys.platform == "darwin":
    # ---- Mac: an always-on-top overlay is on every desktop (or Mission Control can lose it)
    import platforms.macos as mac
    root.update()
    behaviour = lambda: [mac._send_uint(w, mac._Sel(b"collectionBehavior")) for w in m.PLATFORM._ns_windows(root.title())]
    on = m.PLATFORM.on_every_desktop(root, True)
    check(f"on every desktop, and over a full-screen game ({behaviour()})",
          on and behaviour() and all(b & mac._ALL_SPACES and b & mac._FULL_SCREEN_AUX for b in behaviour()))
    m.PLATFORM.on_every_desktop(root, False)
    check("...and back to one desktop when it isn't always on top",
          behaviour() and not any(b & mac._ALL_SPACES for b in behaviour()))
    app._bring_back()
    root.update()
    check("clicking its Dock icon brings it back, on every desktop again",
          root.state() == "normal" and all(b & mac._ALL_SPACES for b in behaviour()) == bool(app.cfg["topmost"]))

check("the typeface is the bundled one, or it fell back cleanly", app._own_fonts in (True, False) and bool(app.theme.fam["extra"]))
app.close()

print("\nALL PASSED" if not failures else f"\n{failures} FAILED")
sys.exit(1 if failures else 0)
