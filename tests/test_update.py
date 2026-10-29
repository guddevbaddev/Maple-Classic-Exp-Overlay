"""Tests for updater.py: Update now downloads only this repository's release files, installs
nothing unless the SHA-256 matches, and swaps the new version in (for real on Windows and macOS).

Run from the project folder:  py -3 tests/test_update.py
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

os.environ["MAPLE_EXP_DATA"] = tempfile.mkdtemp()           # never touch your real data
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import updater as u  # noqa: E402

failures = 0
REPO = "guddevbaddev/Maple-Classic-Exp-Overlay"
MAC = sys.platform == "darwin"


def check(name, ok):
    global failures
    print(("PASS " if ok else "FAIL ") + name)
    failures += not ok


class Reply:
    def __init__(self, data, length=True):
        self.data, self.pos = data, 0
        self.headers = {"Content-Length": str(len(data))} if length else {}

    def read(self, n=-1):
        n = len(self.data) - self.pos if n < 0 else n
        out = self.data[self.pos:self.pos + n]
        self.pos += len(out)
        return out

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


def serve(files):
    """A stand-in for urlopen: the files by their download address, and the addresses asked for."""
    asked = []

    def opener(url):
        asked.append(url)
        return Reply(files[url])
    return opener, asked


def program_zip(version_text, mac=False):
    """A zip laid out like the Build workflow's: a "Maple Classic Exp Overlay" folder with the program."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        if mac:
            z.writestr(f"{u.NAME}/{u.NAME}.app/Contents/MacOS/{u.NAME}", version_text)
            z.writestr(f"{u.NAME}/{u.NAME}.app/Contents/Resources/version.txt", version_text)
        else:
            z.writestr(f"{u.NAME}/{u.NAME}.exe", version_text)
            z.writestr(f"{u.NAME}/_internal/version.txt", version_text)
        z.writestr(f"{u.NAME}/READ ME FIRST.txt", "read me")
    return buf.getvalue()


# ---- which files: this repository's release only
release = {"assets": [
    {"name": "Maple-Classic-Exp-Overlay-v9.9.9-beta.zip",
     "browser_download_url": f"https://github.com/{REPO}/releases/download/v9.9.9-beta/Maple-Classic-Exp-Overlay-v9.9.9-beta.zip"},
    {"name": "SHA256SUMS.txt", "browser_download_url": f"https://github.com/{REPO}/releases/download/v9.9.9-beta/SHA256SUMS.txt"},
    {"name": "evil.zip", "browser_download_url": "https://example.com/evil.zip"},
    {"name": "fork.zip", "browser_download_url": "https://github.com/someone/fork/releases/download/v1/fork.zip"}]}
assets = u.release_assets(release, REPO)
check(f"only files from this repository's own releases are used ({sorted(assets)})",
      sorted(assets) == ["Maple-Classic-Exp-Overlay-v9.9.9-beta.zip", "SHA256SUMS.txt"])
check("the right file for each OS", u.asset_names("1.0", False)[0] == "Maple-Classic-Exp-Overlay-v1.0.zip"
      and u.asset_names("1.0", True)[0] == "Maple-Classic-Exp-Overlay-v1.0-mac.zip")
sums = "a" * 64 + "  Maple-Classic-Exp-Overlay-v1.0.zip\n" + "b" * 64 + " *Maple-Classic-Exp-Overlay-v1.0-mac.zip\n"
check("SHA256SUMS.txt is read for each file", u.expected_sha256(sums, "Maple-Classic-Exp-Overlay-v1.0.zip") == "a" * 64
      and u.expected_sha256(sums, "Maple-Classic-Exp-Overlay-v1.0-mac.zip") == "b" * 64
      and u.expected_sha256(sums, "other.zip") is None and u.expected_sha256("not-a-hash  x.zip", "x.zip") is None)

# ---- download, check, unpack (on a Mac with ditto, which only it has)
version = "9.9.9-beta"
zip_name, sums_name = u.asset_names(version, MAC)
good = program_zip("new version", MAC)
base = f"https://github.com/{REPO}/releases/download/v{version}/"
assets = {zip_name: base + zip_name, sums_name: base + sums_name}
files = {base + zip_name: good, base + sums_name: f"{hashlib.sha256(good).hexdigest()}  {zip_name}\n".encode()}
opener, asked = serve(files)
seen = []
if sys.platform in ("win32", "darwin") or not MAC:
    new, workdir = u.prepare(version, assets, opener, lambda d, t: seen.append((d, t)), MAC)
    check(f"a good download is checked and unpacked ({new.name})",
          new.name == (f"{u.NAME}.app" if MAC else u.NAME) and new.exists() and seen and seen[-1][0] == seen[-1][1])
    check("...and only this release's two files were downloaded", sorted(asked) == sorted(assets.values()))
    inside = (new / "Contents" / "Resources" / "version.txt") if MAC else (new / "_internal" / "version.txt")
    check("...with the new version in it", inside.read_text() == "new version")

bad_files = dict(files)
bad_files[base + zip_name] = program_zip("tampered", MAC)
opener, _ = serve(bad_files)
before = set(Path(tempfile.gettempdir()).glob("maple-exp-update-*"))
try:
    u.prepare(version, assets, opener, None, MAC)
    check("a download that doesn't match its SHA-256 is refused", False)
except u.UpdateError as e:
    check(f"a download that doesn't match its SHA-256 is refused ({e})", "SHA-256" in str(e))
check("...and nothing is left behind", set(Path(tempfile.gettempdir()).glob("maple-exp-update-*")) <= before)
try:
    u.prepare(version, {sums_name: base + sums_name}, serve(files)[0], None, MAC)
    check("a release without this OS's zip is refused", False)
except u.UpdateError:
    check("a release without this OS's zip is refused", True)
try:
    u.download("x", Path(tempfile.mkdtemp()) / "big", lambda url: Reply(b"x" * 2000), max_bytes=1000)
    check("a download bigger than it could be is stopped", False)
except u.UpdateError:
    check("a download bigger than it could be is stopped", True)

buf = io.BytesIO()
with zipfile.ZipFile(buf, "w") as z:
    z.writestr("../../outside.txt", "nope")
slip = Path(tempfile.mkdtemp()) / "slip.zip"
slip.write_bytes(buf.getvalue())
try:
    u.unpack(slip, Path(tempfile.mkdtemp()) / "into", mac=False)
    check("a zip with a file outside its folder is refused", False)
except u.UpdateError:
    check("a zip with a file outside its folder is refused", True)

# ---- where it's installed, and when it can't update itself
tmp = Path(tempfile.mkdtemp())
check("running from source, there's nothing to update in place", u.installed_location(tmp / "python", frozen=False) is None)
check("the Windows download's folder is what's updated",
      u.installed_location(tmp / f"{u.NAME}.exe", frozen=True, mac=False) == tmp)
app = tmp / f"{u.NAME}.app"
check("the Mac app is what's updated",
      u.installed_location(app / "Contents" / "MacOS" / u.NAME, frozen=True, mac=True) == app)
check("...but not an app macOS runs from a read-only copy (opened straight from Downloads)",
      u.installed_location(Path("/private/var/folders/x/AppTranslocation/y") / f"{u.NAME}.app" / "Contents" / "MacOS" / u.NAME,
                           frozen=True, mac=True) is None)

# ---- the real swap, on Windows and macOS: old version installed, new one unpacked, overlay closed
if sys.platform in ("win32", "darwin"):
    root = Path(tempfile.mkdtemp())
    finished = subprocess.Popen([sys.executable, "-c", "pass"])
    finished.wait()                                             # (a process that has closed)
    log = root / "update.log"
    work = root / "work"
    if MAC:
        installed = root / "Applications" / f"{u.NAME}.app"
        (installed / "Contents" / "Resources").mkdir(parents=True)
        (installed / "Contents" / "Resources" / "version.txt").write_text("old")
        (installed / "Contents" / "Resources" / "only-old.txt").write_text("old")
        new = work / "new" / u.NAME / f"{u.NAME}.app"
        (new / "Contents" / "Resources").mkdir(parents=True)
        (new / "Contents" / "Resources" / "version.txt").write_text("new")
        (new / "Contents" / "Frameworks").mkdir()
        (new / "Contents" / "Frameworks" / "link").symlink_to("../Resources/version.txt")
        ran = u.start_install(new, installed, work, log, pid=finished.pid, relaunch=False, wait=True)
        print(f"     (the script: exit {ran.returncode}, {ran.stderr.decode(errors='replace').strip()[-800:]!r})")
        check("on a Mac the new app replaces the old one", (installed / "Contents" / "Resources" / "version.txt").read_text() == "new"
              and not (installed / "Contents" / "Resources" / "only-old.txt").exists())
        check("...keeping its links", (installed / "Contents" / "Frameworks" / "link").is_symlink())
        check("...with nothing left over", not installed.with_name(installed.name + ".old").exists() and not work.exists())

        # The release's own signature stays (macOS keeps Screen Recording for that signer); only an
        # app whose signature doesn't check out is signed again on this Mac.
        def real_app(where, signer):
            (where / "Contents" / "MacOS").mkdir(parents=True)
            run = where / "Contents" / "MacOS" / "run"
            shutil.copyfile("/usr/bin/true", run)          # (its contents only: not macOS's system flags)
            run.chmod(0o755)
            (where / "Contents" / "Info.plist").write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n<plist version="1.0"><dict>'
                "<key>CFBundleIdentifier</key><string>test.overlay.bundle</string>"
                "<key>CFBundleExecutable</key><string>run</string></dict></plist>\n")
            if signer:
                subprocess.run(["codesign", "--force", "--sign", "-", "--identifier", signer, str(where)],
                               check=True, capture_output=True)
        signed_as = lambda app: next((line.split("=", 1)[1] for line in subprocess.run(
            ["codesign", "-dv", str(app)], capture_output=True, text=True).stderr.splitlines()
            if line.startswith("Identifier=")), None)
        for signer, name in (("the.release.signer", "a signed release keeps its own signature"),
                             (None, "an unsigned one is signed on this Mac, so it runs")):
            root3 = Path(tempfile.mkdtemp())
            installed3, work3 = root3 / f"{u.NAME}.app", root3 / "work"
            real_app(installed3, "old.version")
            real_app(work3 / "new" / u.NAME / f"{u.NAME}.app", signer)
            u.start_install(work3 / "new" / u.NAME / f"{u.NAME}.app", installed3, work3, root3 / "u.log",
                            pid=finished.pid, relaunch=False, wait=True)
            ok = subprocess.run(["codesign", "--verify", "--deep", "--strict", str(installed3)]).returncode == 0
            check(f"{name} ({signed_as(installed3)})",
                  ok and signed_as(installed3) == (signer or "test.overlay.bundle"))
    else:
        installed = root / "Games" / u.NAME
        (installed / "_internal").mkdir(parents=True)
        (installed / f"{u.NAME}.exe").write_text("old")
        (installed / "_internal" / "version.txt").write_text("old")
        (installed / "_internal" / "only-old.txt").write_text("old")
        (installed / "a note you put here.txt").write_text("mine")
        new = work / "new" / u.NAME
        (new / "_internal").mkdir(parents=True)
        (new / f"{u.NAME}.exe").write_text("new")
        (new / "_internal" / "version.txt").write_text("new")
        ran = u.start_install(new, installed, work, log, pid=finished.pid, relaunch=False, wait=True)
        print(f"     (the script: exit {ran.returncode}, {ran.stdout.decode(errors='replace').strip()[-600:]!r}, "
              f"{ran.stderr.decode(errors='replace').strip()[-1500:]!r})")
        check("on Windows the new version's files replace the old ones",
              (installed / f"{u.NAME}.exe").read_text() == "new" and (installed / "_internal" / "version.txt").read_text() == "new")
        check("..._internal as a whole (nothing old left in it)", not (installed / "_internal" / "only-old.txt").exists())
        check("...other files in the folder are left alone", (installed / "a note you put here.txt").read_text() == "mine")
        check("...with nothing left over", not (installed / "_internal.old").exists()
              and not (installed / f"{u.NAME}.exe.old").exists() and not work.exists())
    check(f"the update is noted in the log ({log.read_text(errors='replace').strip() if log.exists() else 'no log'})",
          log.exists() and "updated" in log.read_text(errors="replace"))

    # ...and the way a real update starts it: in the background, while the overlay is still open
    import time
    root2 = Path(tempfile.mkdtemp())
    log2, work2 = root2 / "update.log", root2 / "work"
    overlay = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(3)"])     # stands in for the overlay
    if MAC:
        installed2 = root2 / f"{u.NAME}.app"
        (installed2 / "Contents").mkdir(parents=True)
        (installed2 / "Contents" / "v.txt").write_text("old")
        new2 = work2 / "new" / u.NAME / f"{u.NAME}.app"
        (new2 / "Contents").mkdir(parents=True)
        (new2 / "Contents" / "v.txt").write_text("new")
        target = installed2 / "Contents" / "v.txt"
    else:
        installed2 = root2 / u.NAME
        (installed2 / "_internal").mkdir(parents=True)
        (installed2 / f"{u.NAME}.exe").write_text("old")
        new2 = work2 / "new" / u.NAME
        (new2 / "_internal").mkdir(parents=True)
        (new2 / f"{u.NAME}.exe").write_text("new")
        target = installed2 / f"{u.NAME}.exe"
    started = u.start_install(new2, installed2, work2, log2, pid=overlay.pid, relaunch=False)
    check("in the background, the installer is still running (waiting for the overlay to close)", started is None)
    check("...and changes nothing while the overlay is open", target.read_text() == "old")
    overlay.wait()
    for _ in range(120):
        if log2.exists() and "updated" in log2.read_text(errors="replace"):
            break
        time.sleep(0.25)
    check(f"...then, once it has closed, puts the new version in ({log2.read_text(errors='replace').strip() if log2.exists() else 'no log'})",
          target.read_text() == "new")
else:
    print("     (not Windows or macOS: the real swap isn't tested here)")

print("\nALL PASSED" if not failures else f"\n{failures} FAILED")
sys.exit(1 if failures else 0)
