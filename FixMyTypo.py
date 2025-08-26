import time
import keyboard
import pyperclip
import sys
import tkinter as tk
from tkinter import ttk

def fixTheTypoFunction(text):
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

_is_running = False
_last_shift_time = 0.0
enabled = True 

def _copy_selection_with_fallbacks():
    before = pyperclip.paste()
    keyboard.press_and_release('ctrl+c')
    time.sleep(0.12)
    mid = pyperclip.paste()
    if mid != before and mid != "":
        log("[copy] used Ctrl+C")
        return mid

    keyboard.press_and_release('ctrl+insert')
    time.sleep(0.12)
    after = pyperclip.paste()
    if after != before and after != "":
        log("[copy] used Ctrl+Insert")
        return after
    log("[copy] no selection or app blocked copy")
    return ""

def _paste_and_restore(original_clip, text):
    pyperclip.copy(text)
    time.sleep(0.02)
    keyboard.press_and_release('ctrl+v')
    time.sleep(0.08)
    pyperclip.copy(original_clip)

def _handle_hotkey():
    global _is_running, enabled
    if not enabled or _is_running:
        return

    _is_running = True
    try:
        keyboard.release('shift')
        time.sleep(0.01)

        original = pyperclip.paste()
        selected = _copy_selection_with_fallbacks()
        if not selected:
            return

        fixed = fixTheTypoFunction(selected)
        if fixed == selected:
            return

        _paste_and_restore(original, fixed)

        keyboard.release('shift')
        time.sleep(0.01)

    except Exception as e:
        log("[error]", e)
    finally:
        _is_running = False

def _shift_hook(e):
    global _last_shift_time
    if e.name == 'shift' and e.event_type == 'down':
        now = time.time()
        if now - _last_shift_time < 0.35:
            log("[trigger] double-shift (manual detector)")
            _handle_hotkey()
        _last_shift_time = now

def register_hotkeys():
    keyboard.add_hotkey('shift, shift', _handle_hotkey,suppress=True, trigger_on_release=True)
    log("[hotkey] registered: 'shift, shift'")
    keyboard.hook(_shift_hook)

def run_gui():
    global enabled
    root = tk.Tk()
    root.title("Typo Fixer")
    root.geometry("220x140")
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

    ttk.Label(root, text="Double‑Shift to convert",justify="center").pack(pady=(8, 4))

    toggle_btn = tk.Button(root, text="ON", width=10, height=1,font=("Segoe UI", 12, "bold"))
    toggle_btn.pack(pady=4)
    toggle_btn.configure(command=toggle)

    ttk.Label(root, textvariable=status_var).pack()

    btn_frame = ttk.Frame(root)
    btn_frame.pack(pady=(6, 8))
    ttk.Button(btn_frame, text="Exit", command=quit_app).grid(row=0, column=0, padx=5)

    update_button_look()
    root.mainloop()

def main():
    log("Running. Try: Double‑Shift  |  Exit via window")
    register_hotkeys()
    run_gui()

if __name__ == "__main__":
    main()
