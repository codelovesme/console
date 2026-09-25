# console — the codelovesme console

A terminal in a window of its own, written in the `code` language. Tabs,
splits, scrollback, copy and paste — and every key reaches the program
inside **whole**: Ctrl+Tab is not Tab, Ctrl+J is not Enter, Ctrl+1 is not 1.
So the [ide](https://github.com/codelovesme/ide) (or any editor that asks
for these keys) gets them all, here or over ssh.

```sh
cdlvsm install console
cdlvsm console               # a window; its terminals start where you are
cdlvsm console ~/project     # …or there
cdlvsm console -e htop       # a window running a program, not a shell
```

`console -e program [arg…]` (or `--`, as xterm and GNOME Terminal take it)
opens a window whose terminal runs that program instead of the shell, named
after it (`CONSOLE_TITLE` names it otherwise), in the folder you are in; the
window closes when the program ends. cdlvsm puts the console in the
desktop's applications menu when it installs it, and opens terminal apps —
the ide — in it: its release's `app.info` says it runs programs
(`runs-programs=-e`). `console --desktop` adds a menu entry by hand.

Linux, X11 or Wayland.

## Keys

The console's own keys are all Ctrl+Shift+something, so that everything
else goes to the program in the terminal.

| | |
|---|---|
| Ctrl+Shift+T / Ctrl+Shift+W | A new tab / close this one |
| Ctrl+Shift+PgDn / PgUp (or → / ←) | Next / previous tab, round |
| Ctrl+Shift+D / Ctrl+Shift+E | A new terminal on the right / below |
| Ctrl+Shift+] / Ctrl+Shift+[ | The next / previous terminal shown gets the keys |
| Ctrl+Shift+C / Ctrl+Shift+V | Copy the selection / paste |
| Shift+PgUp / Shift+PgDn, Ctrl+Shift+↑ / ↓ | Scroll back / forward a page, a line |
| Ctrl+Shift+Home / End | The oldest line kept / back to the live screen |
| Ctrl+Shift+= / Ctrl+Shift+- / Ctrl+Shift+0 | Bigger / smaller letters / back to font.size |
| Ctrl+Shift+, | settings.json, in your `$EDITOR`, in a new tab |
| Ctrl+Shift+Q | Close everything |

The mouse: the wheel scrolls back, a drag selects (and copies on release),
a click on a tab shows it. A program that asks for the mouse (vim, htop,
less) gets it instead.

`keybindings.json`, beside `settings.json`, changes them — VS Code's way:

```json
[
  { "key": "ctrl+alt+n", "command": "tab.new" },
  { "key": "ctrl+shift+t", "command": "-tab.new" }
]
```

A later entry wins; `-command` takes that key's default away; a key with a
space is a chord.

## Settings

`settings.json` in `$XDG_CONFIG_HOME/codelovesme-console/`
(`~/.config/codelovesme-console/` when that is not set). Ctrl+Shift+,
opens it in your `$EDITOR`; closing that tab applies it.

```json
{
  "font.family": "",
  "font.bold": "",
  "font.size": 15,
  "terminal.shell": "",
  "terminal.scrollback": 5000,
  "window.cols": 110,
  "window.rows": 32,
  "split.size": 50,
  "tabs.alwaysShow": false
}
```

`font.family` is a font file (TTF or OTF); empty is the system's monospace.
`terminal.shell` empty is `$SHELL`. A value that is wrong falls back to its
default.

## How it is built

| gene | what it is |
|---|---|
| `app` | **all the state**, and what each event does to it: keys, the mouse, a terminal's output, the window's size |
| `keys` | the key table: defaults + keybindings.json, chords |
| `layout` | where each group of tabs goes (the ide's 9-slot layout) |
| `tabs` | what is open where: tabs in groups in slots (the ide's) |
| `render` | the whole window from the state, as overlays of styled spans |
| `settings` | settings.json read and checked |

Organelles: `window` (a desktop window as a screen of letters: keys in,
spans drawn, the clipboard), `pty` (the terminals — keys sent the way
their program asked, scrollback, title, mouse), `fs`, `json`, `strings`,
`env`.

## Developing

```sh
curl -sSf https://raw.githubusercontent.com/codelovesme/cdlvsm/main/install.sh | sh
cdlvsm install euglena
cdlvsm euglena install      # the organelles pinned in .code/lock.json
tools/organelles.sh         # …laid out where the console links them from
cdlvsm euglena test
cdlvsm euglena run
```

Tests: [tests/console.code](tests/console.code) drives the console on a
window that draws into memory — a real shell typed into, tabs, a split,
scrolling back, a selection, keybindings, settings. In a real window:
`xvfb-run -a python3 tools/smoke.py` (from a checkout) or
`xvfb-run -a python3 tools/smoke.py <bundle>/console` — keys pressed on an
X display by [tools/xdrive.py](tools/xdrive.py), what happened read back
from the window's title and from a program inside (Ctrl+Tab arrives as
`ESC [ 9 ; 5 u`).

## Releasing

A `v*` tag runs [the release workflow](.github/workflows/release.yml):
the above on a clean machine, then [tools/package.sh](tools/package.sh)
builds the console as a program and lays out
`console-<tag>-x86_64-linux.tar.gz` (the program, [its launcher](bin/console),
its organelles), smoke-tests it under Xvfb, and publishes it.
