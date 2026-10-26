"""Updating the download in place: when a newer release is out and the player clicks Update now,
its zip for this OS is downloaded from this repository's GitHub release, checked against the
SHA-256 the release lists for it (SHA256SUMS.txt), unpacked, and swapped in by a small script
that runs once the overlay has closed, then starts the new version.

Only ever on a click, only from this repository's releases, and nothing is installed unless the
SHA-256 matches. The player's log, notes and settings live in the data folder, which this never
touches. Running from source (not the download) there's nothing to swap: Update now isn't offered.

Where it's installed:
- Windows: a folder with "<NAME>.exe" and _internal next to it. The new folder's files are copied
  over it (_internal is replaced as a whole, and put back if the copy fails).
- macOS: "<NAME>.app". The new app replaces it (the old one is put back if that fails).
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

NAME = "Maple Classic Exp Overlay"          # the program's folder and .exe, or the Mac app
ZIP_NAME = NAME.replace(" ", "-")
MAX_BYTES = 400_000_000                      # no download is anywhere near this big


class UpdateError(RuntimeError):
    """Something stopped the update. Nothing was changed."""


def asset_names(version, mac):
    """(the zip for this OS, the checksum file) as the Build workflow names them."""
    return f"{ZIP_NAME}-v{version}{'-mac' if mac else ''}.zip", "SHA256SUMS.txt"


def release_assets(release, repo):
    """{file name: download address} of a GitHub release (the API's JSON), keeping only files
    downloaded from this repository's own releases."""
    prefix = f"https://github.com/{repo}/releases/download/"
    out = {}
    for a in release.get("assets") or []:
        name, url = a.get("name"), a.get("browser_download_url")
        if isinstance(name, str) and isinstance(url, str) and url.startswith(prefix):
            out[name] = url
    return out


def expected_sha256(sums_text, name):
    """The SHA-256 SHA256SUMS.txt lists for that file, or None."""
    for line in sums_text.splitlines():
        parts = line.strip().split()
        if len(parts) == 2 and parts[1].lstrip("*") == name and len(parts[0]) == 64:
            try:
                int(parts[0], 16)
            except ValueError:
                continue
            return parts[0].lower()
    return None


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url, dest, opener, progress=None, max_bytes=MAX_BYTES):
    """Saves url to dest. opener(url) gives a response (the overlay's _github, or a stand-in in tests);
    progress(done, total) is told how far it's got (total is None if unknown)."""
    with opener(url) as r:
        total = r.headers.get("Content-Length") if getattr(r, "headers", None) else None
        total = int(total) if total and str(total).isdigit() else None
        if total and total > max_bytes:
            raise UpdateError(f"the download is too big ({total} bytes)")
        done = 0
        with open(dest, "wb") as f:
            while True:
                chunk = r.read(1 << 16)
                if not chunk:
                    break
                done += len(chunk)
                if done > max_bytes:
                    raise UpdateError("the download is too big")
                f.write(chunk)
                if progress:
                    progress(done, total)
    return dest


def unpack(zip_path, into, mac):
    """Unpacks the zip into `into`. On a Mac with ditto (Python's zipfile would lose the app's links
    and which files can run); elsewhere a file only goes where the zip says if that's inside `into`."""
    into = Path(into)
    into.mkdir(parents=True, exist_ok=True)
    if mac:
        run = subprocess.run(["ditto", "-x", "-k", str(zip_path), str(into)], capture_output=True)
        if run.returncode != 0:
            raise UpdateError(f"couldn't unpack it: {run.stderr.decode('utf-8', 'replace').strip()[:200]}")
        return into
    root = into.resolve()
    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            target = (root / info.filename).resolve()
            if root not in target.parents and target != root:
                raise UpdateError(f"the zip has a file outside its folder: {info.filename}")
        z.extractall(root)
    return into


def find_new_program(unpacked, mac):
    """Where the new version is in what was unpacked: the Mac app, or the folder with the .exe."""
    unpacked = Path(unpacked)
    if mac:
        found = sorted(unpacked.glob(f"*/{NAME}.app")) + sorted(unpacked.glob(f"{NAME}.app"))
    else:
        found = [p.parent for p in sorted(unpacked.glob(f"*/{NAME}.exe")) + sorted(unpacked.glob(f"{NAME}.exe"))]
    if not found:
        raise UpdateError("the download doesn't have the program in it")
    return found[0]


def installed_location(executable=None, frozen=None, mac=None):
    """What the update replaces: the download's folder (Windows) or its .app (macOS), or None when
    it isn't the download (running from source) or it can't be replaced where it is."""
    executable = Path(executable or sys.executable)
    frozen = getattr(sys, "frozen", False) if frozen is None else frozen
    mac = (sys.platform == "darwin") if mac is None else mac
    if not frozen:
        return None
    if mac:
        app = next((p for p in executable.parents if p.suffix == ".app"), None)
        # (macOS runs an app opened straight from Downloads from a hidden, read-only copy)
        if app is None or "AppTranslocation" in str(app) or not os.access(app.parent, os.W_OK):
            return None
        return app
    folder = executable.parent
    return folder if os.access(folder, os.W_OK) else None


def _ps_quote(text):
    return "'" + str(text).replace("'", "''") + "'"


def windows_script(pid, new_folder, install_folder, cleanup, log, relaunch=True):
    """PowerShell that waits for the overlay (pid) to close, puts the new version's files over the
    installed folder, and starts it again. _internal is moved aside first and put back if the copy
    fails, so a failed update leaves the old version working."""
    exe = Path(install_folder) / f"{NAME}.exe"
    return "\n".join([
        "$ErrorActionPreference = 'Stop'",
        f"$log = {_ps_quote(log)}",
        f"$src = {_ps_quote(new_folder)}",
        f"$dst = {_ps_quote(install_folder)}",
        f"$exe = {_ps_quote(exe)}",
        "$int = Join-Path $dst '_internal'",
        "$old = Join-Path $dst '_internal.old'",
        "$oldExe = $exe + '.old'",
        f"try {{ Wait-Process -Id {int(pid)} -Timeout 120 -ErrorAction SilentlyContinue }} catch {{}}",
        "Start-Sleep -Milliseconds 700",
        "try {",
        "  foreach ($p in @($old, $oldExe)) { if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Recurse -Force } }",
        "  if (Test-Path -LiteralPath $int) { Rename-Item -LiteralPath $int -NewName '_internal.old' }",
        "  if (Test-Path -LiteralPath $exe) { Copy-Item -LiteralPath $exe -Destination $oldExe -Force }",
        "  Copy-Item -Path (Join-Path $src '*') -Destination $dst -Recurse -Force",
        "  foreach ($p in @($old, $oldExe)) { if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Recurse -Force } }",
        "  Add-Content -LiteralPath $log ('[' + (Get-Date -Format s) + '] updated')",
        "} catch {",
        "  Add-Content -LiteralPath $log ('[' + (Get-Date -Format s) + '] update failed, the old version is kept: ' + $_)",
        "  if (Test-Path -LiteralPath $old) {",
        "    if (Test-Path -LiteralPath $int) { Remove-Item -LiteralPath $int -Recurse -Force }",
        "    Rename-Item -LiteralPath $old -NewName '_internal'",
        "  }",
        "  if (Test-Path -LiteralPath $oldExe) { Move-Item -LiteralPath $oldExe -Destination $exe -Force }",
        "}",
        f"if (${'true' if relaunch else 'false'}) {{ Start-Process -FilePath $exe }}",
        f"Remove-Item -LiteralPath {_ps_quote(cleanup)} -Recurse -Force -ErrorAction SilentlyContinue",
    ])


MAC_SCRIPT = """\
pid="$1"; new="$2"; app="$3"; cleanup="$4"; log="$5"; relaunch="$6"
while kill -0 "$pid" 2>/dev/null; do sleep 0.3; done
sleep 0.5
rm -rf "$app.old"
if mv "$app" "$app.old" && ditto "$new" "$app"; then
  rm -rf "$app.old"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] updated" >> "$log"
else
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] update failed" >> "$log"
  rm -rf "$app"; mv "$app.old" "$app"
fi
# Signed again here, as macOS sees it on this Mac (it can stop an app copied in from elsewhere on
# sight, "killed", before it runs a line). The download's SHA-256 was checked before any of this.
xattr -cr "$app" 2>/dev/null
codesign --force --deep --sign - "$app" >/dev/null 2>&1 || echo "[$(date '+%Y-%m-%d %H:%M:%S')] couldn't sign the app again" >> "$log"
if [ "$relaunch" = "1" ]; then open "$app"; fi
rm -rf "$cleanup"
rm -f "$0"
"""


def start_install(new_program, installed, workdir, log, pid=None, relaunch=True, wait=False):
    """Starts the script that swaps in the new version once this program (pid) has closed.
    wait=True (tests) runs it to the end first. Paths go to the script as arguments (Mac) or
    quoted inside it (PowerShell), never pieced into a shell command line."""
    pid = os.getpid() if pid is None else pid
    if sys.platform == "darwin":
        script = Path(workdir).parent / f"{Path(workdir).name}-install.sh"
        script.write_text(MAC_SCRIPT, encoding="utf-8")
        args = ["/bin/sh", str(script), str(pid), str(new_program), str(installed), str(workdir), str(log),
                "1" if relaunch else "0"]
        kw = {}
    elif sys.platform == "win32":
        import base64
        code = windows_script(pid, new_program, installed, workdir, log, relaunch)
        encoded = base64.b64encode(code.encode("utf-16-le")).decode("ascii")
        args = ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded]
        # No window, and its own process group, so it outlives the overlay. (Not DETACHED_PROCESS: with
        # no console at all PowerShell quits without running anything.)
        kw = {"creationflags": 0x08000000 | 0x00000200}             # CREATE_NO_WINDOW, CREATE_NEW_PROCESS_GROUP
    else:
        raise UpdateError("updating in place is only for the Windows and Mac downloads")
    # Started the same way either way (tests wait for it, to see how it went).
    out = subprocess.PIPE if wait else subprocess.DEVNULL
    proc = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=out, stderr=out,
                            start_new_session=(sys.platform == "darwin"), **kw)
    if wait:
        stdout, stderr = proc.communicate(timeout=300)
        return subprocess.CompletedProcess(args, proc.returncode, stdout, stderr)
    # It waits for the overlay to close, so it's still running now. If it isn't, it couldn't start:
    # say so (the overlay stays open) rather than close for an update that won't come.
    try:
        proc.wait(timeout=1.5)
        raise UpdateError(f"the installer stopped straight away (exit {proc.returncode})")
    except subprocess.TimeoutExpired:
        return None


def prepare(version, assets, opener, progress=None, mac=None, workdir=None):
    """Downloads and checks the new version, and unpacks it. Returns (the new program, the folder
    to remove afterwards). Raises UpdateError (nothing changed) if anything's off."""
    mac = (sys.platform == "darwin") if mac is None else mac
    zip_name, sums_name = asset_names(version, mac)
    if zip_name not in assets or sums_name not in assets:
        raise UpdateError(f"the release has no {zip_name} (or no {sums_name})")
    workdir = Path(workdir or tempfile.mkdtemp(prefix="maple-exp-update-"))
    try:
        sums = download(assets[sums_name], workdir / sums_name, opener, max_bytes=100_000)
        want = expected_sha256(sums.read_text(encoding="utf-8", errors="replace"), zip_name)
        if not want:
            raise UpdateError(f"{sums_name} doesn't list {zip_name}")
        zip_path = download(assets[zip_name], workdir / zip_name, opener, progress)
        got = sha256_of(zip_path)
        if got != want:
            raise UpdateError(f"the download doesn't match its SHA-256 (got {got[:12]}..., expected {want[:12]}...)")
        new = find_new_program(unpack(zip_path, workdir / "new", mac), mac)
        zip_path.unlink()
        return new, workdir
    except Exception:
        shutil.rmtree(workdir, ignore_errors=True)
        raise
