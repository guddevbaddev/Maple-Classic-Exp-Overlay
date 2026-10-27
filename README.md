<h1><img src="docs/icon.png" width="40" align="top"> Maple Classic Exp Overlay</h1>

**A free EXP tracker for MapleStory Classic World.** A small window sits next to the game and shows how fast you're leveling and making mesos.

This copy doesn't connect to the original author's best-maps website: it never shares your runs, and it has no **Best maps** button. The only time it goes online is the update check, which looks at this repository's releases.

**[Download it here](../../releases/latest)** (Windows and Mac) · [How to install](#how-to-install) · [On a Mac](#on-a-mac)

> **This is a beta.** It works, but you might run into rough edges. I'm actively improving it, so check back for updates. If something doesn't work, please [tell me](../../issues)!

![The overlay next to MapleStory, while farming](docs/screenshot-game.jpg)

## What it shows

![The overlay up close, with its log open](docs/screenshot-main.png)

- **EXP per hour**, for your whole session and for the last 5 minutes
- **How long until your next level**, right under your EXP/hr (for example "Lv 31 in 36 min")
- **How much of a level you gained** in the last 5, 15 and 30 minutes and the last hour (under **Details**). Paused time doesn't count. Until you've tracked that long, it shows what you've gained so far ("2.40% so far").
- **Mesos per hour**, read from your inventory
- **What your potions cost** (beta), read from your quickslot: potions used come off your profit, potions picked up cover some of it, and **Profit / hr** shows what's left
- **A log of every map you farm**: your EXP/hr and mesos/hr there, at which level and class, solo or in a party

You don't type anything in. It reads all of this from your game screen by itself.

## How to install

You need Windows 10 or 11 (on a Mac, see [On a Mac](#on-a-mac)). It takes about 2 minutes, and you don't need to install anything else.

1. Go to the **[download page](../../releases/latest)**.
2. Under **Assets**, click the **Maple-Classic-Exp-Overlay-v….zip** file (for example `Maple-Classic-Exp-Overlay-v0.9.10-beta.zip`) to download it. Don't click "Source code": that's for programmers.
3. Find the zip in your Downloads folder. **Right-click it**, choose **Extract All...**, then click **Extract**. (Just double-clicking the zip isn't enough. It has to be extracted.)
4. Open the new folder, then the **Maple Classic Exp Overlay** folder inside it.
5. Double-click **Maple Classic Exp Overlay.exe**. It may show as just **Maple Classic Exp Overlay**, with a gold chart icon.

**Windows says "Windows protected your PC"?** Click **More info**, then **Run anyway**. Windows shows this for any new program that isn't from a big company.

**Keep the whole folder together.** The program needs the files next to it, so don't drag it out of its folder. To put it on your desktop, right-click **Maple Classic Exp Overlay.exe** and choose **Send to**, then **Desktop (create shortcut)**. On Windows 11, **Send to** is under **Show more options**.

### On a Mac

You need a Mac with Apple Silicon (M1 or newer) and macOS 14 (Sonoma) or newer, with MapleStory running through CrossOver, Whisky, Parallels or a game stream.

1. On the **[download page](../../releases/latest)**, under **Assets**, click the file ending in **-mac.zip**.
2. Double-click the zip in your Downloads folder to unpack it, and drag **Maple Classic Exp Overlay** (the app) into your **Applications** folder. (If you had an older copy, delete it first rather than replacing it.)
3. Open **Terminal** (press Cmd+Space, type Terminal, press Enter), paste these two lines and press Enter. They take away the "downloaded from the internet" mark and sign the app on your Mac, so macOS lets it start (without them it can close the moment it opens, with no message):

   ```
   xattr -cr "/Applications/Maple Classic Exp Overlay.app"
   codesign --force --deep --sign - "/Applications/Maple Classic Exp Overlay.app"
   ```
4. Open the app from Applications. If macOS says it can't check it for malware (it isn't from a registered Apple developer): click **Done**, open **System Settings > Privacy & Security**, scroll down, and click **Open Anyway** next to Maple Classic Exp Overlay.
5. **Let it see the game (Screen Recording).** That's how it reads your EXP. Open **System Settings > Privacy & Security > Screen Recording** (on newer macOS: **Screen & System Audio Recording**):
   - If **Maple Classic Exp Overlay** is in the list already, select it and click **–** to remove it (an entry from an older copy doesn't work for this one).
   - Click **+**, choose **Maple Classic Exp Overlay** in Applications, and make sure its switch is **on**.
   - Quit the overlay with **Cmd+Q** and open it again. (macOS only applies the permission when the app starts.)

**Hotkeys aren't available on a Mac yet**, so use the buttons. Everything else works as on Windows.

#### If something's wrong on a Mac

- **It closes right away, or Terminal says "killed":** do step 3 again.
- **The timer starts, then pauses ("it can't see the game's EXP bar") even while you're killing monsters, or Details > Current never changes:** it can't see the game. Do step 5 again: remove it from Screen Recording with **–**, add it back with **+**, then Cmd+Q and open it again. Switching it off and on isn't always enough.
- **After an update:** **Update now** does step 3 by itself, but macOS may want step 5 again for the new version.
- **Still not working:** ⚙ > **Save logs**, and attach the zip to a [bug report](../../issues).

## How to use it

1. **Start MapleStory.** Windowed, borderless or fullscreen all work, at any size.
2. **Open Maple Classic Exp Overlay.** It finds the game window by itself.
3. **Move the overlay so it doesn't cover these parts of the game:**
   - the minimap (top left)
   - the EXP bar (bottom)
   - the mesos at the bottom of your inventory
   - the party list
   - the quickslot (the 8 keys above the right end of the status bar), for potions

   The overlay reads them from your screen, so it can't see through itself. If it's in the way, it tells you at the bottom of its window. It remembers where you put it.
4. **Press Start** and play normally. You only need to press it once:
   - It **pauses by itself** when you get no EXP for 2 minutes, and when it can't see the game's EXP bar for 10 seconds (the game is minimized, or something covers it). It carries on at your next EXP gain. Paused time doesn't count, so EXP/hr only covers your farming. The time without EXP before it paused is taken back off the clock too, so the timer jumps back a little. Don't want that (say, you're timing how long it takes to gather items)? Turn off **Pause the timer when no EXP comes in** in ⚙ Settings: the timer then keeps running until you press Pause (it still pauses when it can't see the game).
   - **One session, until you press Reset** (or close the overlay): changing maps doesn't pause it or start from zero. EXP, mesos, potions and time all add up over the whole session.
5. **Want mesos tracked?** Open your inventory, on any tab, now and then. It saves the mesos it read: close the inventory and they stay (Details says **saved**), and the next time you open it, everything you made since counts, over the time that went by.
6. **Want potions counted?** Put them on your quickslot keys, as you normally would. See [Potions](#potions) below.

Within a few seconds it shows your level and how much EXP you have. The per-hour numbers fill in once you've gained a little EXP.

| Button | What it does |
|---|---|
| **Start / Pause / Resume** | Starts tracking. **Pause** stops it until you press **Resume**. |
| **Reset** | Starts a new session from zero (EXP, mesos, potions and time), and looks for the minimap, inventory and party list again (handy after moving them around) |
| **Don't log** | Keeps the current run out of the log, for example while you're testing a map or waiting for your party. Everything is still shown on screen. It turns itself off when you leave the map or stop getting EXP, so your next run is logged as usual. |
| **Select area** | Lets you drag a box around the EXP numbers, if it ever can't find them. The button then turns into **Follow game**, which goes back to finding them by itself. |
| **View capture** | Shows exactly what it read from your screen |
| **PQ mode** | For party quests (in the **...** menu). See [PQ mode](#pq-mode) below. |
| **Share** | Makes a picture of your session (EXP/hr, mesos/hr, the map) and copies it, to paste into Discord. See [Sharing your session](#sharing-your-session) below. |
| **⚙** | Settings |
| **>** | Opens the log |
| **Compact** | A much smaller window with just EXP/hr, when you'll level, the last 5 minutes, mesos/hr and Start/Pause. The button then says **Full**, to bring everything back. Shift+4 or double-clicking the big number does the same. |

### PQ mode

A party quest goes through several maps, and a stage can go minutes without EXP until it's cleared. Normally the overlay pauses after 2 minutes without EXP, which could spoil a PQ, so turn on **PQ mode** in the **...** menu (it then says **PQ mode: on**) before you start:

- **It only pauses by itself after 10 minutes without EXP**, so the EXP you get when a stage is cleared counts.
- **The log puts the PQ on one line called "Party Quest"**, whatever maps it went through. Right-click it and choose **Rename map** to call it, say, "Kerning PQ".
- The status at the top says **PQ** while it's tracking.

It turns itself off when you close the overlay, so your normal farming isn't affected if you forget. To turn it off sooner, choose **PQ mode: on** in the menu again.

### Potions

The overlay reads the **count on each quickslot key** that has a potion on it (like the 163 under an Orange Potion), every few seconds. It knows the potions by their pictures (the game's own) and uses their **NPC shop price** from [meowdb](https://meowdb.com/msclassic/npc-shops/item-efficiency/consumables):

- **Two tiles under the top three** show them: a **red** one for your HP potion and a **blue** one for your MP potion, each with the potion's picture, how many are left (red once it's down to **Warn at**), and how many you've used this session and what they cost ("27 used · -4,050"). With more than one of a kind on your keys, it shows the one you've used the most. A tile says **Not on quickslot** when there's no potion of its kind on your keys.
- **A count that goes down** is potions used: their price comes off your profit.
- **A count that goes up** is potions picked up (or bought): their price covers some of that cost.
- **Details** shows both, like `-1,000 / +100` (mesos), and **Profit / hr**: mesos made, less what potions cost, per hour.
- A count has to be read the same twice in a row before it counts (three times for a big change), so a misread doesn't show up as potions used. A change of more than 100 at once (a trip to storage, or moving potions to another key) starts counting afresh.
- **A sound when potions run low:** while tracking, each time you use a potion that's down to **15 or fewer** on your quickslot, the overlay plays a sound and says which potion and how many are left. Change the number with ⚙ > **Warn at**, how loud it is with **Volume** (**Test** plays it), or turn it off with **Sound when potions run low**.
- **Changing prices:** ⚙ > **Potion prices** > **Change...**: set what a potion is worth to you, for example its free market price. **Shop prices** puts them all back. Elixirs aren't sold in NPC shops, so they start at 0 (left out) until you set a price.

It knows the Red, Orange, White and Blue Potions, the Elixirs, and the foods NPC shops sell (Apple, Meat, Lemon, Hamburger, Pure Water and the rest: the list is in ⚙ > Potion prices). A potion only on the inventory's Use tab, not on a quickslot key, isn't counted. **This is new:** if it gets a count wrong, please send a screenshot (PNG) of the game with your quickslot in a [bug report](../../issues).

### High levels: an EXP bar with only a %

From about level 58 the game stops showing the EXP number and shows only the %, like `EXP. [88.50%]`. The overlay reads that too. The % alone doesn't say how much EXP that is, so the first time it sees it, it asks **what level you are** (if it saw your level before the number went away, it already knows and doesn't ask). From then on:

- It works out your EXP from the % and the EXP your level needs, so EXP/hr, time to level, the log and the share card all work as before.
- It counts your level up by itself each time you level up, and remembers it for next time.
- Wrong level? Choose **Set your level...** in the **...** menu.

The bar shows the % to two decimals, so at high levels each step is a bit over 100 EXP: single kills can add up in small jumps, but over a few minutes the numbers are just as right. The **% of a level per hour** doesn't depend on the level at all.

### Sharing your session

Click **Share** (bottom right) to show off how your farming is going. It makes a picture card in the overlay's gold-and-dark look with:

- your **EXP per hour**, big and glowing, with the trend line of your session
- your **mesos per hour** (if your inventory was open) and how long you've been tracking
- the **map** you're on, your **level**, **class** and **party size** (in PQ mode it says "Party Quest")
- how much of a level you're getting per hour

It's **copied straight away**: click in Discord's message box and press **Ctrl+V** (**Cmd+V** on a Mac), then Enter. It also opens in a window, where **Copy again** copies it again and **Show file** shows the saved picture (`share-card.png` in the data folder), in case you'd rather drag it in. The card never shows your character's name, and nothing is sent anywhere by the overlay: you choose where to paste it.

## Hotkeys

They work while MapleStory (or the overlay) is the window in front, so you don't have to click away from the game:

| Keys | What they do |
|---|---|
| **Shift+1** | Start / Pause |
| **Shift+2** | Reset |
| **Shift+3** | Don't log |
| **Shift+4** | Compact / Full |

The status line says what happened, for example "Shift+1: paused." While the hotkeys are on, those keys go to the overlay only, so Shift+1 won't type **!** in the game's chat. If that gets in your way, change them (or turn them off) in ⚙: click one, then press the keys you want. Backspace turns one off.

## The log

Click **>** at the top right of the overlay to open the log. It's the table on the right in the close-up picture above.

- **After 5 minutes of non-stop farming**, it adds a line for that map, your level and your party size.
- **Every 5 more minutes** it updates that line, so the numbers get more accurate the longer you farm.
- **Time** shows how long a line is based on. It grows by 5 minutes with each update.
- **Class** is read from the status bar (never your character's name). Different classes get separate lines.
- **15-minute runs:** under the log it also counts toward 15 minutes of non-stop farming on one map with the same party size ("15-min run: 7 of 15 min"). A level-up doesn't stop it; a break, a new map or a new party size starts it over. Finished runs are saved separately in your log file.
- **Greyed-out lines** were changed outside the overlay. Every line the overlay writes is sealed, so a line edited or added by hand is easy to spot. Deleting a line, or renaming a map in the overlay, is fine.
- **Taking a break restarts the 5-minute timer.** A break means no EXP for 2 minutes (you can change this in ⚙). Changing maps or party size restarts it too.
- **Don't want a run logged?** Press **Don't log**. It switches back on its own when that run ends.
- **Solo** means just you. **4ppl** means a party of 4.
- **?** under Mesos/hr means your inventory wasn't open.
- **Right-click a line** to:
  - **Copy line**, to paste it into Discord or anywhere else
  - **Rename map**, if it read the name wrong (it remembers the fix for next time)
  - **Delete entry**
- **Playing in a party?** A map's party sizes on one day share one line (e.g. **4–5ppl ▸**), with the numbers over all that time. Click it to see a line for each party size.
- **Notes:** click a line and write whatever you like about it in the box under the log: the party, the pots, the loot, why you left. A ✎ in the **Note** column marks the lines that have one. Notes save as you type, and **they only ever stay on your PC**, in your log file, and are never sent anywhere. Renaming a map, updating the overlay, or farming more on a line keeps its note. Deleting a line deletes its note too, and asks you first.
- **Can't see a whole column?** Drag the lines between the column titles to make columns narrower or wider. While the log is open, you can also make the window bigger by dragging its edge. It remembers both.

## Settings (⚙)

- **Pause the timer when no EXP comes in** (on by default). Off: the timer keeps running through breaks, without ever jumping back, until you press Pause. Not seeing the game still pauses it.
- **Pause tracking after no EXP for...** How long you can go without EXP before it pauses by itself. This also restarts the log's 5-minute timer. The default is 2 minutes (120 s). (If you had the old default of 15 seconds, it's 2 minutes now; change it back here if you liked it.)
- **Potion prices.** What each potion is worth, for **Profit / hr**. See [Potions](#potions).
- **Sound when potions run low** (on by default) and **Warn at** (15 to start with): a sound each time you use a potion that's down to that many on your quickslot. **Volume** sets how loud (70% to start with; your computer's volume still applies), and **Test** plays it.
- **Window transparency.** Makes the overlay see-through, up to 40%. (More and it could fade out of sight, with Settings in it.)
- **Size.** Makes the text and the whole window smaller or bigger, from 60% to 200%. The smallest text stops at a readable size, so it never gets too small to read. It's sized for each screen, so a window moved to a screen with different Windows scaling (like a 5K and a 1440p screen) looks the same size on both.
- **Hotkeys.** Turn them on or off, and change them. See [Hotkeys](#hotkeys).
- **Always on top of other windows.** Keeps the overlay above the game. It's on by default.
- **Check for updates when it starts.** On by default. See [Updates](#updates).
- **Open data folder.** Opens the folder where your log and settings are saved.
- **Check for updates.** Checks right now.
- **Report a bug.** See below.

## How accurate is it?

It double-checks everything it reads before counting it:

- **EXP:** the number and the % have to agree with each other, and with the EXP your level needs. (At high levels the bar shows only the %, which is read the same careful way.)
- **Mesos:** a new amount has to show up in several readings in a row.
- **Sudden jumps:** an EXP jump or a level-up has to be confirmed before it counts. A mesos amount that looks like an extra or missing digit is ignored.
- **Dying:** the EXP you lose isn't taken off your EXP/hr. It says how much you lost, then carries on from there.
- **When in doubt, it waits.** If it can't read something clearly, it skips it instead of guessing.

Every version is tested against thousands of misread numbers, and against real screenshots of the game pasted over many different backgrounds at different window sizes.

## Something not working?

**Did it close by itself?** Open it again: it says it closed unexpectedly, and offers to save what happened. You can also do it any time in ⚙ with **Save logs**: it makes one zip (in the `logs` folder of the data folder) with `overlay.log` (what it was doing), `errors.log` and `crash.log` (where it was when it closed). Send that zip, or attach it to a bug report.

**Click View capture first.** It shows exactly what the overlay read, with a box around every digit:

![View capture](docs/screenshot-capture.png)

| Problem | Try this |
|---|---|
| An error pops up when you open Maple Classic Exp Overlay.exe | Extract the zip first (step 3 above). It can't run from inside the zip or away from its folder. |
| "MapleStory window not found" | Start the game first. If it's minimized, bring it back up. |
| "Can't find the EXP bar" | Make sure nothing covers the EXP bar at the bottom of the game, including the overlay. If the game window is very small, make it bigger. |
| View capture shows the wrong part of the screen | If the button says **Follow game**, click it. |
| Mesos says "open inventory" | Open your inventory, and make sure the mesos at its bottom aren't hidden. In small game windows the chat bar can cover them, so drag the inventory up a bit. If it still doesn't show, stand still for a moment so the inventory stops being see-through. |
| The log says "Map not read yet" | Make sure the minimap is open at the top left of the game, and the overlay isn't covering it. |
| The map name is wrong | Right-click the log line and choose **Rename map**. |
| "This window is covering..." | Drag the overlay to another spot. |
| Numbers stopped updating, or anything else | Please report it (see below). |

**To report a bug,** click **Report a bug** in ⚙ (or **Something's wrong? Report a bug** in View capture):
1. Your browser opens a bug report on GitHub, already filled in with your version and what the overlay was reading. Nothing personal is included, and nothing is sent until you click Submit.
2. A folder opens with **bug-report.png** (what the overlay read: the EXP bar, mesos, class and map name) and **bug-report.txt** (how it's doing: your screen and game window size, what it found, what it last said, and any errors). Drag both into the report. Neither has your character name or Windows user name. It also asks if you want to save a small picture of the whole game window: that one can show chat and names, so it's saved only if you say yes, and you choose whether to attach it.
3. Write a sentence about what went wrong, and click **Submit**. (You need a free GitHub account.)

## Is it safe? Is it allowed?

- **It only looks at your screen, like a screen recorder.** It never touches the game's files or memory, and never presses keys or clicks for you.
- **It only goes online for one thing:** asking GitHub whether there's a newer version when it starts. Nothing about who you are is sent, and it can be turned off in ⚙. See [Privacy](#privacy).
- **Your antivirus might warn about it.** Antivirus programs sometimes flag small new programs by mistake. All of the code is public right here, so anyone can check what it does.
- **It isn't made by or affiliated with Nexon.** Like any third-party tool, you use it at your own risk.

## Privacy

- **Your log, your notes and your settings stay on your PC**, in `%APPDATA%\MapleEXP` (`~/Library/Application Support/MapleEXP` on a Mac). Notes are part of your log file: they are never sent anywhere, and the overlay's tests check that.
- **A copy of your log is kept for each day** (the last 7 days), in the `backups` folder next to it, so if anything ever goes wrong there's a recent one. To go back to one, close the overlay and copy it over `exp_log.json`.
- **The update check** (on by default, can be turned off in ⚙) asks GitHub for the newest version and what's new in it. Nothing about you is sent.
- **Nothing from your log is ever sent anywhere**, including your 15-minute runs. There's no sharing and no website.
- **Bug reports** only go to GitHub if you click Submit there yourself.

## Where the download comes from

Downloads on the [Releases page](../../releases) are built by GitHub from the code in this repository ([Build workflow](.github/workflows/build.yml)), not on anyone's own PC. Each build:

- installs exact package files, each checked against its SHA-256 ([requirements-build.txt](requirements-build.txt)),
- runs all the tests,
- records a signed **attestation**: which workflow built which file, from which commit,
- puts the zip's **SHA-256** on the release page (`SHA256SUMS.txt`).

**Check your download** with the free [GitHub CLI](https://cli.github.com):

```
gh attestation verify "the zip you downloaded.zip" --repo guddevbaddev/Maple-Classic-Exp-Overlay
```

It tells you whether that exact file was built here, and from which commit. Or compare the file's SHA-256 with `SHA256SUMS.txt` on its release page (in PowerShell: `Get-FileHash "the zip you downloaded.zip"`).

The same zip is also kept on the page of the build that made it (Actions, the run, the file at the bottom; you need a GitHub account to download it). Build runs since October 17 keep it exactly as it is, so the SHA-256 GitHub shows there is the zip's own, the same as on the release page.

**Versions up to v0.9.9-beta** were released by the original author, [beanguri](https://github.com/beanguri), from [their repository](https://github.com/beanguri/Maple-Classic-Exp-Overlay). This copy's releases start at v0.9.10-beta. Their repository also has the code of their best-maps website, which this copy doesn't include or use.

### Code signing policy

This copy's downloads aren't code-signed yet, so Windows warns about them (see [How to install](#how-to-install)). The Build workflow can sign them with free code signing from [SignPath Foundation](https://signpath.org) once that's set up; only builds made by the Build workflow from this repository would be signed.

- Committers and reviewers: [guddevbaddev](https://github.com/guddevbaddev)
- Approvers: [guddevbaddev](https://github.com/guddevbaddev)
- Privacy policy: see [Privacy](#privacy) above. In short: your log and notes stay on your PC, and the overlay only contacts another system to check GitHub for a newer version (can be turned off in Settings).

**Credits:** based on [Maple Classic Exp Overlay](https://github.com/beanguri/Maple-Classic-Exp-Overlay) by [beanguri](https://github.com/beanguri) (MIT License). The typeface is [Manrope](https://github.com/googlefonts/manrope) (SIL Open Font License, included as `assets/fonts/OFL.txt`).

## Updates

This is a beta, and I'm still adding features and fixing things.

**New name:** since v0.9.3 it's called Maple Classic Exp Overlay. It used to be Maple EXP/hr. Your log and settings carry over.

**When a new version is out,** the overlay tells you when you start it, and shows what's new. Click **Get the update** to open the download page, or **Not now** / **Skip this version** if you'd rather wait.

**To update:** click **Update now** in the window that says a new version is out (from 0.9.13-beta on). It downloads the new version from this page, checks its SHA-256, and restarts the overlay as the new version; nothing is installed if the check fails. On a Mac, macOS may ask for Screen Recording again afterwards. Or, as before, download the newest zip from the [download page](../../releases/latest) and use it instead of the old folder. Your log, notes and settings stay, because they're saved separately (⚙ → **Open data folder** shows where).

**To remove it:** delete its folder. To also delete your log and settings, delete the folder that **Open data folder** opens.

See [CHANGELOG.md](CHANGELOG.md) for what changed in each version.

---

<details>
<summary><b>For developers</b></summary>

**Run from source.** You need Python 3.10 or newer, and [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) for map names.

```
py -3 -m pip install -r requirements.txt
run.bat
```

**On macOS** (the Mac download, or from source, with the game running through CrossOver, Whisky, Parallels or a game stream): macOS support was written by thanhphamvan, who tried it on a real Mac with the game. I don't own a Mac, so I can't test it myself: GitHub's automatic tests run on a real Mac, but not with the game. If you try it, please tell me how it goes.

**How to run it on a Mac:** `brew install tesseract`, then `python3 -m pip install -r requirements.txt` and `python3 maple_exp.py`. The first time, allow your Terminal (or Python) in **System Settings > Privacy & Security > Screen Recording**, then start it again. The window is found by "MapleStory" in its title; if it isn't, use **Select area**. Hotkeys aren't available on macOS yet.

Everything that differs between Windows and macOS (finding the game window, screen scaling, hotkeys, the one-copy-at-a-time lock) is in `platforms/`: one `Platform` interface in `base.py`, one implementation per OS, and `create_platform()` picks the one for the OS it's on.

**Build the download** (puts `Maple-Classic-Exp-Overlay-v<version>.zip` in `release/`, and a copy to use right away in the project folder: `Maple Classic Exp Overlay.exe` with its `_internal` folder):

```
py -3 -m pip install -r requirements.txt pyinstaller
py -3 build.py
```

**Tests use their own data folder:** with `MAPLE_EXP_DATA` set, the overlay keeps its log and settings there, away from your real ones.

**Run the tests:**

```
py -3 tests/test_logic.py
py -3 tests/test_screen.py
py -3 tests/test_potions.py
py -3 tests/test_ui.py     # opens the real window for a few seconds (the notes box)
```

To build with exactly the packages the releases use: `py -3 -m pip install --require-hashes -r requirements-build.txt`.

**The Mac download** is built the same way on a Mac: `brew install tesseract dylibbundler`, `python3 -m pip install --require-hashes -r requirements-build-mac.txt`, then `python3 build.py`. It makes `release/Maple-Classic-Exp-Overlay-v<version>-mac.zip`, with the app and its own copy of Tesseract (and the libraries it needs), signed ad hoc. The Build workflow does this too, after the Windows build, and adds the Mac zip to the same draft release.

GitHub runs the logic tests on every push ([Tests workflow](.github/workflows/tests.yml)). The [Build workflow](.github/workflows/build.yml) builds the download on GitHub (Actions tab, **Build**, **Run workflow**), runs all the tests first, and signs the .exe once code signing is set up. Pushing a version tag also attests the zip and drafts the release with it, and so does **Run workflow** on `main` with **release** ticked (it makes the tag `v` + `VERSION` itself, once the build has passed); releases are only ever made those ways.

**How it reads the screen:**
- It finds the `MapleStory.exe` window, then the EXP numbers (like `12,345 [12.34%]`) in the status bar.
- Each digit is resized to a standard size and compared against saved examples of the game's font in `assets/`.
- A reading only counts if the EXP and % agree with how much EXP that level needs, so misreads are ignored.
- Mesos are read the same way. The mesos box is found by its outline, which also works while the inventory is see-through.
- The party size is the number of HP bars in the party list.
- Potions (`potions.py`): the quickslot is always the same distance from the EXP number, at the UI's scale, so only its 8 keys are looked at. A key's count is read with the game's own item-count digits, from the key's left edge; the potion is told by the colour of its body (the key's name covers the top of the picture). Pictures, digits and prices are in `assets/potions/`.
- Map names are read with Tesseract.
- Settings, the log and `errors.log` are saved in `%APPDATA%\MapleEXP` (`~/Library/Application Support/MapleEXP` on macOS; from its old name, Maple EXP/hr, so updates keep them).

</details>

## Credits

- The Classic World EXP table is from [meowdb](https://meowdb.com/msclassic/guides/exp-table-level-1-to-100). It's used to work out your level.
- Potion prices (NPC shops) are from [meowdb](https://meowdb.com/msclassic/npc-shops/item-efficiency/consumables). The potion pictures and the item-count digits are the game's own, from [maplestory.io](https://maplestory.io).
- Map names are read with [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (Apache 2.0 license), which is included in the download.

## License

[MIT](LICENSE): free to use, change and share.
