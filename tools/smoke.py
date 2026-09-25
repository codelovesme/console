"""The console in a real window, on an X display (Xvfb in CI): keys
pressed, what it did read back from the window's title and a file a program
inside wrote.

    xvfb-run -a python3 tools/smoke.py              # from a checkout
    xvfb-run -a python3 tools/smoke.py <bundle>/console

Exits non-zero, saying what, if anything is not as it should be.
"""
import os, shutil, subprocess, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xdrive

app = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
work = tempfile.mkdtemp(prefix="console-smoke-")
config = tempfile.mkdtemp(prefix="console-smoke-config-")
os.makedirs(config + "/codelovesme-console")
open(config + "/codelovesme-console/settings.json", "w").write('{ "terminal.shell": "/bin/sh", "window.cols": 80, "window.rows": 24 }\n')
env = dict(os.environ, XDG_CONFIG_HOME=config, CONSOLE_DIR=work)
if len(sys.argv) > 1:
    argv, cwd = [os.path.abspath(sys.argv[1]), work], work
else:
    argv, cwd = [shutil.which("cdlvsm"), "euglena", "run"], app
log = open(work + "/console.log", "w")
proc = subprocess.Popen(argv, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT)

failures = []
def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)

def wait_title(part, seconds=10):
    end = time.time() + seconds
    while time.time() < end:
        if any(part in t for t in xdrive.titles()):
            return True
        time.sleep(0.2)
    return False

check(wait_title("— console", 30), "a window opens, titled after its terminal")
xdrive.click(200, 150)
xdrive.focus_under_pointer()
xdrive.type_text("printf '\\033]2;smoke-title\\007'\n")
check(wait_title("smoke-title — console"), "keys reach the shell, and the title it sets is the window's")

# A program that asks for kitty's keys, and writes what one key press was.
xdrive.type_text("sh -c \"printf '\\033[>1u'; stty raw -echo; head -c 6 | od -An -c > keys.txt\"\n")
time.sleep(1.0)
xdrive.key("ctrl+Tab")
end = time.time() + 5
seen = ""
while time.time() < end:
    try:
        seen = open(work + "/keys.txt").read()
    except OSError:
        seen = ""
    if seen.strip():
        break
    time.sleep(0.2)
check(seen.split() == ["033", "[", "9", ";", "5", "u"], "ctrl+tab reaches the program inside whole: " + " ".join(seen.split()))

xdrive.key("ctrl+shift+t")
check(wait_title("Terminal 2 — console"), "ctrl+shift+t: a new tab, with the keys")
xdrive.key("ctrl+shift+Page_Down")
check(wait_title("smoke-title — console"), "ctrl+shift+pagedown: round to the first tab")

xdrive.key("ctrl+shift+q")
try:
    proc.wait(10)
    check(True, "ctrl+shift+q closes the console")
except subprocess.TimeoutExpired:
    proc.kill()
    check(False, "ctrl+shift+q closes the console")
# console -e program: a window running that, not a shell, called after it,
# closing when it ends (a bundle only: the checkout has no launcher).
if len(sys.argv) > 1:
    marker = work + "/ran-by-e.txt"
    run = subprocess.Popen([os.path.abspath(sys.argv[1]), "-e", "sh", "-c", "echo \"it's run\" > " + marker + "; sleep 3"], cwd=work, env=env, stdout=log, stderr=subprocess.STDOUT)
    check(wait_title("sh — console", 30), "console -e: a window titled after the program")
    end = time.time() + 10
    while time.time() < end and not os.path.exists(marker):
        time.sleep(0.2)
    check(os.path.exists(marker) and open(marker).read() == "it's run\n", "console -e: the program runs, its arguments whole")
    try:
        run.wait(15)
        check(True, "console -e: the window closes when the program ends")
    except subprocess.TimeoutExpired:
        run.kill()
        check(False, "console -e: the window closes when the program ends")

if failures:
    print(open(work + "/console.log").read()[-2000:])
shutil.rmtree(work, ignore_errors=True)
shutil.rmtree(config, ignore_errors=True)
sys.exit(1 if failures else 0)
