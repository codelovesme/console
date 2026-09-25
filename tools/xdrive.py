"""An X display driven the way a person drives it — keys, clicks, the
focus — and read back: screenshots, window titles. ctypes on libX11 and
libXtst, so it needs nothing installed but X itself (Xvfb in CI).

    import xdrive
    xdrive.click(300, 200); xdrive.focus_under_pointer()
    xdrive.type_text("echo hi\n"); xdrive.key("ctrl+shift+t")
    xdrive.titles()   # every top-level window's name
"""
import ctypes, ctypes.util, sys, time
x11 = ctypes.cdll.LoadLibrary("libX11.so.6")
xtst = ctypes.cdll.LoadLibrary("libXtst.so.6")
x11.XOpenDisplay.restype = ctypes.c_void_p
x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
x11.XDefaultRootWindow.restype = ctypes.c_ulong
x11.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
x11.XGetImage.restype = ctypes.c_void_p
x11.XGetImage.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_int, ctypes.c_uint, ctypes.c_uint, ctypes.c_ulong, ctypes.c_int]
x11.XGetPixel.restype = ctypes.c_ulong
x11.XGetPixel.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
x11.XStringToKeysym.restype = ctypes.c_ulong
x11.XStringToKeysym.argtypes = [ctypes.c_char_p]
x11.XKeysymToKeycode.restype = ctypes.c_ubyte
x11.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
x11.XFlush.argtypes = [ctypes.c_void_p]
xtst.XTestFakeKeyEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
xtst.XTestFakeButtonEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
xtst.XTestFakeMotionEvent.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ulong]

class XImage(ctypes.Structure):
    _fields_ = [("width", ctypes.c_int), ("height", ctypes.c_int), ("xoffset", ctypes.c_int), ("format", ctypes.c_int),
                ("data", ctypes.POINTER(ctypes.c_ubyte)), ("byte_order", ctypes.c_int), ("bitmap_unit", ctypes.c_int),
                ("bitmap_bit_order", ctypes.c_int), ("bitmap_pad", ctypes.c_int), ("depth", ctypes.c_int),
                ("bytes_per_line", ctypes.c_int), ("bits_per_pixel", ctypes.c_int)]

d = x11.XOpenDisplay(None)
if not d:
    raise SystemExit("no X display (run under xvfb-run)")
root = x11.XDefaultRootWindow(d)

def shot(path, w=1280, h=800):
    """The screen (cropped to what is drawn) as a PNG; needs PIL."""
    from PIL import Image
    img = x11.XGetImage(d, root, 0, 0, w, h, 0xFFFFFFFF, 2)
    xi = ctypes.cast(img, ctypes.POINTER(XImage)).contents
    raw = ctypes.string_at(xi.data, xi.bytes_per_line * xi.height)
    im = Image.frombuffer("RGBX", (xi.width, xi.height), raw, "raw", "BGRX", xi.bytes_per_line, 1).convert("RGB")
    bbox = im.point(lambda v: 255 if v else 0).getbbox()
    (im.crop(bbox) if bbox else im).save(path)

MODS = {"ctrl": "Control_L", "shift": "Shift_L", "alt": "Alt_L"}

def key(spec):
    parts = spec.split("+")
    mods, name = parts[:-1], parts[-1]
    codes = [x11.XKeysymToKeycode(d, x11.XStringToKeysym(MODS[m].encode())) for m in mods]
    code = x11.XKeysymToKeycode(d, x11.XStringToKeysym(name.encode()))
    for c in codes:
        xtst.XTestFakeKeyEvent(d, c, 1, 0)
    xtst.XTestFakeKeyEvent(d, code, 1, 0)
    xtst.XTestFakeKeyEvent(d, code, 0, 0)
    for c in reversed(codes):
        xtst.XTestFakeKeyEvent(d, c, 0, 0)
    x11.XFlush(d)
    time.sleep(0.05)


NAMES = {" ": "space", "=": "equal", "$": "shift+dollar", "_": "shift+underscore", ".": "period", "/": "slash",
         "-": "minus", "&": "shift+ampersand", "~": "shift+asciitilde", "\n": "Return", "'": "apostrophe",
         ":": "shift+colon", "|": "shift+bar", ">": "shift+greater", "\\": "backslash", ";": "semicolon",
         "[": "bracketleft", "]": "bracketright", '"': "shift+quotedbl", "(": "shift+parenleft",
         ")": "shift+parenright", "<": "shift+less", "*": "shift+asterisk", "#": "shift+numbersign",
         "!": "shift+exclam", "?": "shift+question", "%": "shift+percent", ",": "comma", "+": "shift+plus"}

def type_text(text):
    for ch in text:
        if ch in NAMES:
            key(NAMES[ch])
        elif ch.isupper():
            key("shift+" + ch)
        else:
            key(ch)

def click(x, y, button=1):
    xtst.XTestFakeMotionEvent(d, -1, x, y, 0)
    xtst.XTestFakeButtonEvent(d, button, 1, 0)
    xtst.XTestFakeButtonEvent(d, button, 0, 0)
    x11.XFlush(d)
    time.sleep(0.05)

def focus_under_pointer():
    """No window manager: X's input focus put on the window under the
    pointer, as a click would with one."""
    x11.XSetInputFocus.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    x11.XQueryPointer.argtypes = [ctypes.c_void_p, ctypes.c_ulong] + [ctypes.POINTER(ctypes.c_ulong)] * 2 + [ctypes.POINTER(ctypes.c_int)] * 4 + [ctypes.POINTER(ctypes.c_uint)]
    r, child = ctypes.c_ulong(), ctypes.c_ulong()
    ints = [ctypes.c_int() for _ in range(4)]
    mask = ctypes.c_uint()
    x11.XQueryPointer(d, root, ctypes.byref(r), ctypes.byref(child), *[ctypes.byref(i) for i in ints], ctypes.byref(mask))
    x11.XSetInputFocus(d, child.value or 1, 1, 0)
    x11.XFlush(d)
    time.sleep(0.2)

def titles():
    """The names of the top-level windows."""
    x11.XQueryTree.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.POINTER(ctypes.c_ulong)), ctypes.POINTER(ctypes.c_uint)]
    x11.XFetchName.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(ctypes.c_char_p)]
    x11.XGetWMName.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p]
    r, parent = ctypes.c_ulong(), ctypes.c_ulong()
    children = ctypes.POINTER(ctypes.c_ulong)()
    n = ctypes.c_uint()
    x11.XQueryTree(d, root, ctypes.byref(r), ctypes.byref(parent), ctypes.byref(children), ctypes.byref(n))
    out = []
    atom = x11.XInternAtom
    atom.restype = ctypes.c_ulong
    atom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
    net_name, utf8 = atom(d, b"_NET_WM_NAME", 0), atom(d, b"UTF8_STRING", 0)
    get = x11.XGetWindowProperty
    get.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_long, ctypes.c_long, ctypes.c_int, ctypes.c_ulong,
                    ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.POINTER(ctypes.c_ubyte))]
    for i in range(n.value):
        t, f, items, after = ctypes.c_ulong(), ctypes.c_int(), ctypes.c_ulong(), ctypes.c_ulong()
        data = ctypes.POINTER(ctypes.c_ubyte)()
        if get(d, children[i], net_name, 0, 1024, 0, utf8, ctypes.byref(t), ctypes.byref(f), ctypes.byref(items), ctypes.byref(after), ctypes.byref(data)) == 0 and data and items.value:
            out.append(ctypes.string_at(data, items.value).decode("utf-8", "replace"))
            continue
        name = ctypes.c_char_p()
        if x11.XFetchName(d, children[i], ctypes.byref(name)) and name.value:
            out.append(name.value.decode("utf-8", "replace"))
    return out
