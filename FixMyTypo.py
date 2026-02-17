import time
import keyboard
import pyperclip
import sys
import tkinter as tk
from tkinter import ttk

"""
FixMyTypo - lightweight clipboard-based keyboard-layout fixer.

This script listens for a double-press of a physical key (by default
`caps lock`) and converts selected text between Hebrew and English
keyboard layouts. The conversion is done via character mapping tables
and a simple heuristic that counts Hebrew vs English characters to
determine direction.
"""

def fixTheTypoFunction(text):
    """Convert mistyped text between Hebrew and English layouts.

    Heuristic: count how many characters belong to English vs Hebrew
    maps and convert in the direction of the minority-to-majority mapping.
    This keeps punctuation and digits unchanged where mappings are absent.
    """
    HE_TO_EN = {
        # bottom row
        'ז': 'z', 'ס': 'x', 'ב': 'c', 'ה': 'v', 'נ': 'b',
        'מ': 'n', 'צ': 'm', 'ת': ',', 'ץ': '.', '.': '/',
        # middle row
        'ש': 'a', 'ד': 's', 'ג': 'd', 'כ': 'f', 'ע': 'g',
        'י': 'h', 'ח': 'j', 'ל': 'k', 'ך': 'l', 'ף': ';',
        ',': "'",
        # top row
        '/': 'q', "'": 'w', 'ק': 'e', 'ר': 'r', 'א': 't',
        'ט': 'y', 'ו': 'u', 'ן': 'i', 'ם': 'o', 'פ': 'p',
        ']': '[', '[': ']',
        # numbers row
        '1': '1', '2': '2', '3': '3', '4': '4', '5': '5',
        '6': '6', '7': '7', '8': '8', '9': '9', '0': '0',
        '-': '-', '=': '='
    }

    EN_TO_HE ={ 
        # bottom row
        'z': 'ז', 'Z': 'ז',
        'x': 'ס', 'X': 'ס',
        'c': 'ב', 'C': 'ב',
        'v': 'ה', 'V': 'ה',
        'b': 'נ', 'B': 'נ',
        'n': 'מ', 'N': 'מ',
        'm': 'צ', 'M': 'צ',
        ',': 'ת', '<': 'ת',
        '.': 'ץ', '>': 'ץ',
        '/': '.', '?': '.',
        # middle row
        'a': 'ש', 'A': 'ש',
        's': 'ד', 'S': 'ד',
        'd': 'ג', 'D': 'ג',
        'f': 'כ', 'F': 'כ',
        'g': 'ע', 'G': 'ע',
        'h': 'י', 'H': 'י',
        'j': 'ח', 'J': 'ח',
        'k': 'ל', 'K': 'ל',
        'l': 'ך', 'L': 'ך',
        ';': 'ף', ':': 'ף',
        "'": ',', '"': ',',
        # top row
        'q': '/', 'Q': '/',
        'w': "'", 'W': "'",
        'e': 'ק', 'E': 'ק',
        'r': 'ר', 'R': 'ר',
        't': 'א', 'T': 'א',
        'y': 'ט', 'Y': 'ט',
        'u': 'ו', 'U': 'ו',
        'i': 'ן', 'I': 'ן',
        'o': 'ם', 'O': 'ם',
        'p': 'פ', 'P': 'פ',
        '[': ']', '{': ']',
        ']': '[', '}': '[',
        # numbers row
        '1': '1', '!': '!',
        '2': '2', '@': '@',
        '3': '3', '#': '#',
        '4': '4', '$': '$',
        '5': '5', '%': '%',
        '6': '6', '^': '^',
        '7': '7', '&': '&',
        '8': '8', '*': '*',
        '9': '9', '(': '(',
        '0': '0', ')': ')',
        '-': '-', '_': '_',
        '=': '=', '+': '+'
    }

    count_EN = sum(1 for ch in text if ch in EN_TO_HE)
    count_HE = sum(1 for ch in text if ch in HE_TO_EN)

    result = []
    if count_EN < count_HE:
        for ch in text:
            if ch in HE_TO_EN:
                result.append(HE_TO_EN[ch])
            else:
                result.append(ch)
        return ("".join(result))
    else:
        for ch in text:
            if ch in EN_TO_HE:
                result.append(EN_TO_HE[ch])
            else:
                result.append(ch)
        return ("".join(result))


def log(*a):
    print(*a, file=sys.stdout, flush=True)

# which physical key we use as the double-tap trigger
TRIGGER_KEY = 'caps lock'

_is_running = False
_last_trigger_time = 0.0
_last_run_time = 0.0
_trigger_pressed = False
enabled = True

def _copy_selection_with_fallbacks():
    before = pyperclip.paste()
    keyboard.press_and_release('ctrl+c')
    time.sleep(0.12)
    mid = pyperclip.paste()
    if mid != before and mid != "":
        return mid

    keyboard.press_and_release('ctrl+insert')
    time.sleep(0.12)
    after = pyperclip.paste()
    if after != before and after != "":
        return after
    return ""


# ---- Windows master-volume helpers (pycaw) ----
# Audio helpers removed: minimal build does not include volume control.


def _paste_and_restore(original_clip, text):
    """Temporarily replace clipboard content, paste, then restore.

    Uses a short sleep to allow target applications to receive the
    synthetic paste event. This is a pragmatic approach that works with
    many apps but is not guaranteed for every program that hooks the
    clipboard in unusual ways.
    """
    pyperclip.copy(text)
    time.sleep(0.02)
    keyboard.press_and_release('ctrl+v')
    time.sleep(0.08)
    pyperclip.copy(original_clip)

def _handle_hotkey():
    global _is_running, enabled, _last_run_time

    """Perform the clipboard conversion operation.

    Steps:
    1. Debounce to avoid repeated activations.
    2. Snapshot master volume (best-effort) to restore later if it
       appears the conversion caused an accidental volume change.
    3. Copy selected text, convert it, paste the result and restore
       the original clipboard contents.
    4. Check the volume and restore if it decreased.

    The function is defensive: failures in any single step will not
    crash the application.
    """
    if not enabled or _is_running:
        return

    now = time.time()
    if now - _last_run_time < 0.5:
        return
    _last_run_time = now

    # (no volume snapshot in minimal build)

    _is_running = True
    try:
        original = pyperclip.paste()
        selected = _copy_selection_with_fallbacks()
        if not selected:
            return

        fixed = fixTheTypoFunction(selected)
        if fixed == selected:
            return

        _paste_and_restore(original, fixed)

        # short delay to allow target app to process paste
        time.sleep(0.06)

    except Exception as e:
        log("[error]", e)
    finally:
        _is_running = False

def _trigger_hook(e):
    """Detect double-press of the configured trigger key and run.

    Minimal behavior: if the configured `TRIGGER_KEY` is pressed twice
    within ~0.35s the conversion flow (`_handle_hotkey`) is invoked.
    """
    global _last_trigger_time, _trigger_pressed

    # normalize event name for comparison
    name = (getattr(e, 'name', '') or '').lower().replace('_', ' ')
    if name != TRIGGER_KEY:
        return

    if e.event_type == 'down':
        # ignore auto-repeat 'down' events while key remains pressed
        if _trigger_pressed:
            return
        _trigger_pressed = True
        now = time.time()
        if now - _last_trigger_time < 0.35:
            # double-press detected → perform conversion
            _handle_hotkey()
        _last_trigger_time = now
    elif e.event_type == 'up':
        _trigger_pressed = False

# Media handler removed in minimal build (no volume/media interception)

def register_hotkeys():
    # Minimal hotkey registration: only the low-level trigger hook is needed
    keyboard.hook(_trigger_hook)

def run_gui():
    global enabled
    root = tk.Tk()
    root.title("Typo Fixer")
    root.geometry("180x140")
    root.resizable(False, False)

    style = ttk.Style()
    try:
        style.theme_use('clam')
    except Exception:
        pass

    status_var = tk.StringVar(value="Status: ON")
    def update_button_look():
        if enabled:
            toggle_btn.config(text="ON", bg="#22c55e", activebackground="#16a34a")
            status_var.set("Status: ON")
        else:
            toggle_btn.config(text="OFF", bg="#ef4444", activebackground="#b91c1c")
            status_var.set("Status: OFF")

    def toggle():
        global enabled
        enabled = not enabled
        update_button_look()

    def quit_app():
        root.destroy()
        sys.exit(0)

    # Informational label that shows the trigger key in the preferred
    # user-facing format (title-cased).
    ttk.Label(root, text=f"Double‑{TRIGGER_KEY.title()} to convert",justify="center").pack(pady=(8, 4))

    toggle_btn = tk.Button(root, text="ON", width=10, height=1,font=("Segoe UI", 12, "bold"))
    toggle_btn.pack(pady=4)
    toggle_btn.configure(command=toggle)

    ttk.Label(root, textvariable=status_var).pack()

    btn_frame = ttk.Frame(root)
    btn_frame.pack(pady=(6, 8))
    ttk.Button(btn_frame, text="Exit", command=quit_app).pack(padx=5)

    update_button_look()
    root.mainloop()

def main():
    register_hotkeys()
    run_gui()

if __name__ == "__main__":
    main()
