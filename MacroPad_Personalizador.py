"""MacroPad Personalizador para Windows. Requer apenas Python 3 e Tkinter."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk


APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "MacroPad_Personalizador_config.json"

COLORS = {
    "bg": "#0b111b", "surface": "#111a27", "panel": "#151f2e",
    "tile": "#202d40", "tile_hover": "#2a3c54", "accent": "#65d6b3",
    "accent_dark": "#214c45", "blue": "#76aaff", "text": "#edf3fa",
    "muted": "#9aabc0", "line": "#2a394d", "warn_bg": "#2a261b",
    "warn": "#f0d18b",
}

MEDIA_ACTIONS = {
    "Aumentar volume": 0xAF,
    "Diminuir volume": 0xAE,
    "Silenciar / ativar som": 0xAD,
    "Faixa anterior": 0xB1,
    "Reproduzir / pausar": 0xB3,
    "Próxima faixa": 0xB0,
    "Parar mídia": 0xB2,
}
MEDIA_ICONS = {"Aumentar volume": "🔉", "Diminuir volume": "🔈",
               "Silenciar / ativar som": "🔇", "Faixa anterior": "⏮",
               "Reproduzir / pausar": "⏯", "Próxima faixa": "⏭", "Parar mídia": "⏹"}


def action_caption(item: dict, limit: int = 16) -> str:
    """Compact, recognizable label for assigned actions on the virtual device."""
    value = str(item.get("value", "")).strip()
    if item.get("mode") == "Mídia" and value in MEDIA_ICONS:
        return f"{MEDIA_ICONS[value]}  {value[:limit]}"
    return value[:limit]

WH_KEYBOARD_LL = 13
WM_KEYDOWN, WM_KEYUP = 0x0100, 0x0101
WM_SYSKEYDOWN, WM_SYSKEYUP = 0x0104, 0x0105
LLKHF_INJECTED = 0x10
KEYEVENTF_KEYUP, KEYEVENTF_UNICODE = 0x0002, 0x0004
INPUT_KEYBOARD = 1

ULONG_PTR = ctypes.c_size_t


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", wintypes.DWORD), ("scanCode", wintypes.DWORD),
                ("flags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD)]


class INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", INPUT_UNION)]


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class MSG(ctypes.Structure):
    _fields_ = [("hwnd", wintypes.HWND), ("message", wintypes.UINT),
                ("wParam", ULONG_PTR), ("lParam", ctypes.c_ssize_t),
                ("time", wintypes.DWORD), ("pt", POINT),
                ("lPrivate", wintypes.DWORD)]


user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, ULONG_PTR, ctypes.c_ssize_t)

user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
user32.SetWindowsHookExW.restype = ctypes.c_void_p
user32.CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int, ULONG_PTR, ctypes.c_ssize_t]
user32.CallNextHookEx.restype = ctypes.c_ssize_t
user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
user32.GetMessageW.argtypes = [ctypes.POINTER(MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = wintypes.BOOL
user32.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
user32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]
user32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, ULONG_PTR, ctypes.c_ssize_t]
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HMODULE
kernel32.GetCurrentThreadId.restype = wintypes.DWORD
user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
user32.SendInput.restype = wintypes.UINT


VK_NAMES = {
    0x08: "BACKSPACE", 0x09: "TAB", 0x0D: "ENTER", 0x10: "SHIFT",
    0x11: "CTRL", 0x12: "ALT", 0x13: "PAUSE", 0x14: "CAPSLOCK",
    0x1B: "ESC", 0x20: "SPACE", 0x21: "PAGEUP", 0x22: "PAGEDOWN",
    0x23: "END", 0x24: "HOME", 0x25: "LEFT", 0x26: "UP",
    0x27: "RIGHT", 0x28: "DOWN", 0x2C: "PRINTSCREEN", 0x2D: "INSERT",
    0x2E: "DELETE", 0x5B: "LWIN", 0x5C: "RWIN", 0x5D: "MENU",
    0x6A: "NUM*", 0x6B: "NUM+", 0x6D: "NUM-", 0x6E: "NUM.",
    0x6F: "NUM/", 0x90: "NUMLOCK", 0x91: "SCROLLLOCK",
    0xA0: "LSHIFT", 0xA1: "RSHIFT", 0xA2: "LCTRL", 0xA3: "RCTRL",
    0xA4: "LALT", 0xA5: "RALT", 0xAD: "VOLUME_MUTE",
    0xAE: "VOLUME_DOWN", 0xAF: "VOLUME_UP", 0xB0: "MEDIA_NEXT",
    0xB1: "MEDIA_PREV", 0xB2: "MEDIA_STOP", 0xB3: "MEDIA_PLAY_PAUSE",
    0xB4: "MAIL", 0xB5: "MEDIA_SELECT", 0xB6: "APP1", 0xB7: "APP2",
    0xBA: ";", 0xBB: "=", 0xBC: ",", 0xBD: "-", 0xBE: ".",
    0xBF: "/", 0xC0: "`", 0xDB: "[", 0xDC: "\\", 0xDD: "]",
    0xDE: "'", 0xE2: "\\", 0x5F: "SLEEP",
}
for i in range(1, 25):
    VK_NAMES[0x6F + i] = f"F{i}"
for i in range(10):
    VK_NAMES[0x60 + i] = f"NUM{i}"

VK_VALUES = {name: vk for vk, name in VK_NAMES.items()}
VK_VALUES.update({
    "CONTROL": 0x11, "COMMAND": 0x5B, "WIN": 0x5B,
    "RETURN": 0x0D, "ESCAPE": 0x1B, "PGUP": 0x21, "PGDN": 0x22,
    "PRIOR": 0x21, "NEXT": 0x22, "DEL": 0x2E, "INS": 0x2D,
    "LEFTCTRL": 0xA2, "RIGHTCTRL": 0xA3, "LEFTSHIFT": 0xA0,
    "RIGHTSHIFT": 0xA1, "LEFTALT": 0xA4, "RIGHTALT": 0xA5,
})


def vk_name(vk: int) -> str:
    if vk in VK_NAMES:
        return VK_NAMES[vk]
    if 0x30 <= vk <= 0x39 or 0x41 <= vk <= 0x5A:
        return chr(vk)
    return f"VK 0x{vk:02X}"


def is_modifier(vk: int) -> bool:
    return vk in (0x10, 0x11, 0x12, 0x5B, 0x5C, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5)


def format_trigger(vks: list[int]) -> str:
    return "+".join(vk_name(vk) for vk in vks)


def make_key(vk: int, flags: int = 0, scan: int = 0) -> INPUT:
    item = INPUT()
    item.type = INPUT_KEYBOARD
    item.ki = KEYBDINPUT(vk, scan, flags, 0, 0)
    return item


def send_inputs(items: list[INPUT]) -> None:
    if items:
        arr = (INPUT * len(items))(*items)
        sent = user32.SendInput(len(arr), arr, ctypes.sizeof(INPUT))
        if sent != len(arr):
            raise ctypes.WinError(ctypes.get_last_error())


def send_text(text: str) -> None:
    items: list[INPUT] = []
    units = text.encode("utf-16-le", errors="replace")
    for i in range(0, len(units), 2):
        code = units[i] | (units[i + 1] << 8)
        items.append(make_key(0, KEYEVENTF_UNICODE, code))
        items.append(make_key(0, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, code))
        if len(items) >= 128:
            send_inputs(items)
            items.clear()
    send_inputs(items)


def parse_shortcut(value: str) -> list[int]:
    names = [part.strip().upper() for part in value.split("+") if part.strip()]
    if not names:
        raise ValueError("Digite um atalho, por exemplo CTRL+SHIFT+S.")
    codes = []
    for name in names:
        if len(name) == 1 and name.isalnum():
            codes.append(ord(name))
        elif name in VK_VALUES:
            codes.append(VK_VALUES[name])
        else:
            raise ValueError(f"Tecla desconhecida: {name}")
    if len(set(codes)) != len(codes):
        raise ValueError("O atalho contém uma tecla repetida.")
    return codes


def send_shortcut(value: str) -> None:
    codes = parse_shortcut(value)
    items = [make_key(vk) for vk in codes]
    items.extend(make_key(vk, KEYEVENTF_KEYUP) for vk in reversed(codes))
    send_inputs(items)


def send_media_action(value: str) -> None:
    vk = MEDIA_ACTIONS[value]
    send_inputs([make_key(vk), make_key(vk, KEYEVENTF_KEYUP)])


class MacroPadApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("MacroPad Studio")
        root.geometry("1160x780")
        root.minsize(1000, 680)
        root.configure(bg=COLORS["bg"])
        self.maps: dict[str, dict[str, str | int | list[int]]] = {}
        self.pressed: set[int] = set()
        self.capture_active: set[int] = set()
        self.capture_order: list[int] = []
        self.suppressed_keyups: set[int] = set()
        self.active_triggers: list[tuple[set[int], dict[str, str | int | list[int]]]] = []
        self.capture_pending = False
        self.selected_slot = 0
        self.selected_control: tuple[str, int | str] = ("key", 0)
        self.layout_size = 12
        self.active_layer = 1
        self.hook = None
        self.hook_thread_id = 0
        self.hook_ready = threading.Event()
        self.running = False
        self.callback_ref = HOOKPROC(self._hook_callback)
        self._load_config()
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.start_hook()

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=22)
        outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 16))
        brand = tk.Frame(header, bg=COLORS["bg"])
        brand.pack(side="left", fill="x", expand=True)
        tk.Label(brand, text="M", bg=COLORS["accent_dark"], fg=COLORS["accent"],
                 font=("Segoe UI", 15, "bold"), width=3, height=1).pack(side="left", padx=(0, 12))
        title_block = tk.Frame(brand, bg=COLORS["bg"])
        title_block.pack(side="left", fill="x")
        tk.Label(title_block, text="MACROPAD STUDIO", bg=COLORS["bg"], fg=COLORS["text"],
                 font=("Segoe UI", 20, "bold")).pack(anchor="w")
        tk.Label(title_block, text="Personalize seus atalhos e comandos", bg=COLORS["bg"], fg=COLORS["muted"],
                 font=("Segoe UI", 10)).pack(anchor="w", pady=(1, 0))
        tk.Label(header, text="●  CAPTURA GLOBAL ATIVA", bg=COLORS["accent_dark"], fg=COLORS["accent"],
                 font=("Segoe UI", 9, "bold"), padx=12, pady=8).pack(side="right", anchor="center")

        topbar = ttk.Frame(outer)
        topbar.pack(fill="x", pady=(0, 12))
        ttk.Label(topbar, text="DISPOSITIVO").pack(side="left")
        tk.Label(topbar, text="MacroPad Multimídia  ·  USB 514C:4155", bg=COLORS["surface"], fg=COLORS["text"],
                 font=("Segoe UI", 10, "bold"), padx=10, pady=6).pack(side="left", padx=(8, 18))
        ttk.Label(topbar, text="LAYOUT").pack(side="left")
        layout_labels = {3: "3 teclas  ·  3 × 1", 6: "6 teclas  ·  3 × 2",
                         9: "9 teclas  ·  3 × 3", 12: "12 teclas  ·  3 × 4",
                         15: "15 teclas  ·  5 × 3"}
        self.layout_var = tk.StringVar(value=layout_labels.get(self.layout_size, layout_labels[12]))
        self.layout_combo = ttk.Combobox(topbar, textvariable=self.layout_var,
            values=("3 teclas  ·  3 × 1", "6 teclas  ·  3 × 2", "9 teclas  ·  3 × 3",
                    "12 teclas  ·  3 × 4", "15 teclas  ·  5 × 3"),
            state="readonly", width=20)
        self.layout_combo.pack(side="left", padx=(10, 20))
        self.layout_combo.bind("<<ComboboxSelected>>", self._layout_changed)
        ttk.Label(topbar, text="CAMADA").pack(side="left", padx=(0, 8))
        self.layer_buttons: list[tk.Button] = []
        for layer in range(1, 4):
            selected = layer == self.active_layer
            button = tk.Button(topbar, text=f"● {layer}" if selected else str(layer), width=4,
                command=lambda n=layer: self._select_layer(n),
                bg=COLORS["accent_dark"] if selected else COLORS["tile"],
                fg=COLORS["accent"] if selected else COLORS["muted"],
                activebackground=COLORS["tile_hover"], activeforeground=COLORS["text"],
                relief="flat", bd=0, font=("Segoe UI", 9, "bold"), cursor="hand2")
            button.pack(side="left", padx=2)
            self.layer_buttons.append(button)
        self.layer_status_var = tk.StringVar(value=f"Camada {self.active_layer} ativa")
        ttk.Label(topbar, textvariable=self.layer_status_var).pack(side="left", padx=(8, 0))
        notice = tk.Label(outer,
            text="MODO GLOBAL  ·  Eventos iguais de outros teclados também podem acionar estes macros.",
            bg=COLORS["warn_bg"], fg=COLORS["warn"], padx=12, pady=8, anchor="w", wraplength=1000,
            font=("Segoe UI", 9))
        notice.pack(fill="x", pady=(0, 16))

        body = ttk.Frame(outer)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        visual = ttk.LabelFrame(body, text="PAINEL MULTIMÍDIA  /  CLIQUE EM UMA TECLA OU NO KNOB", padding=16)
        visual.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self.knob_frame = tk.LabelFrame(visual, text="KNOB MULTIMÍDIA  ·  GIRO / CLIQUE", bg=COLORS["surface"], fg=COLORS["text"],
                                       padx=8, pady=6, font=("Segoe UI", 9, "bold"),
                                       bd=1, relief="solid", highlightbackground=COLORS["line"])
        self.knob_frame.pack(fill="x", pady=(0, 10))
        self.knob_buttons_frame = tk.Frame(self.knob_frame, bg=COLORS["surface"])
        self.knob_buttons_frame.pack(fill="x")
        self.grid_frame = tk.Frame(visual, bg=COLORS["surface"], padx=12, pady=12)
        self.grid_frame.pack(fill="both", expand=True)
        self.key_buttons: list[tk.Button] = []
        self.knob_buttons: list[tk.Button] = []

        editor = ttk.LabelFrame(body, text="CONFIGURAR TECLA", padding=14)
        editor.grid(row=0, column=1, sticky="nsew")
        self.selected_title = tk.StringVar(value="Selecione uma tecla")
        ttk.Label(editor, textvariable=self.selected_title, font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 12))
        ttk.Label(editor, text="GATILHO FÍSICO · TECLA OU KNOB").pack(anchor="w")
        self.trigger_var = tk.StringVar(value="(não definido)")
        trigger_row = ttk.Frame(editor)
        trigger_row.pack(fill="x", pady=(4, 12))
        tk.Label(trigger_row, textvariable=self.trigger_var, bg=COLORS["surface"], fg=COLORS["blue"],
                 font=("Segoe UI", 10, "bold"), padx=9, pady=8, anchor="w").pack(side="left", fill="x", expand=True)
        tk.Button(trigger_row, text="⦿  CAPTURAR", command=self.begin_capture,
                  bg=COLORS["accent"], fg=COLORS["bg"], activebackground="#8ce6ca",
                  activeforeground=COLORS["bg"], relief="flat", bd=0,
                  font=("Segoe UI", 9, "bold"), padx=10, pady=8, cursor="hand2").pack(side="left", padx=(8, 0))

        ttk.Label(editor, text="TIPO DE AÇÃO").pack(anchor="w", pady=(4, 0))
        self.mode_var = tk.StringVar(value="Texto")
        self.mode_buttons: dict[str, tk.Button] = {}
        mode_row = tk.Frame(editor, bg=COLORS["panel"])
        mode_row.pack(fill="x", pady=(6, 9))
        for index, (mode, label) in enumerate((("Atalho", "⌨  Atalho"), ("Texto", "Aa  Texto"),
                                               ("Mídia", "♫  Mídia"), ("Camada", "⇄  Camada"))):
            button = tk.Button(mode_row, text=label, command=lambda m=mode: self._set_mode(m),
                               bg=COLORS["tile"], fg=COLORS["muted"], activebackground=COLORS["tile_hover"],
                               activeforeground=COLORS["text"], relief="flat", bd=0,
                               font=("Segoe UI", 9, "bold"), padx=8, pady=9, cursor="hand2", wraplength=120)
            button.grid(row=index // 2, column=index % 2, sticky="ew", padx=2, pady=2)
            self.mode_buttons[mode] = button
        mode_row.columnconfigure(0, weight=1)
        mode_row.columnconfigure(1, weight=1)
        self.action_var = tk.StringVar()
        ttk.Entry(editor, textvariable=self.action_var).pack(fill="x")
        self.action_var.trace_add("write", lambda *_: self._update_action_preview())
        self.action_preview = tk.StringVar(value="Ação configurada: —")
        preview_card = tk.Frame(editor, bg=COLORS["surface"], padx=10, pady=9)
        preview_card.pack(fill="x", pady=(8, 8))
        tk.Label(preview_card, text="CONFIGURAÇÃO ATUAL", bg=COLORS["surface"], fg=COLORS["muted"],
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")
        tk.Label(preview_card, textvariable=self.action_preview, bg=COLORS["surface"], fg=COLORS["text"],
                 wraplength=280, justify="left", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(4, 0))
        self.action_picker_button = tk.Button(editor, text="⌨  ESCOLHER NO TECLADO VIRTUAL",
                  command=self._open_virtual_keyboard, bg=COLORS["tile"], fg=COLORS["text"],
                  activebackground=COLORS["tile_hover"], activeforeground=COLORS["text"],
                  relief="flat", bd=0, font=("Segoe UI", 9, "bold"), padx=8, pady=9,
                  cursor="hand2")
        self.action_picker_button.pack(fill="x", pady=(0, 8))
        self.action_hint = tk.StringVar(value="Texto livre para digitar quando a tecla for pressionada.")
        ttk.Label(editor, textvariable=self.action_hint, wraplength=300).pack(anchor="w", pady=(0, 10))
        tk.Button(editor, text="SALVAR CONFIGURAÇÃO", command=self.save_mapping,
                  bg=COLORS["accent"], fg=COLORS["bg"], activebackground="#8ce6ca",
                  activeforeground=COLORS["bg"], relief="flat", bd=0,
                  font=("Segoe UI", 10, "bold"), padx=10, pady=10,
                  cursor="hand2").pack(fill="x", pady=(0, 7))
        tk.Button(editor, text="Limpar este controle", command=self.remove_mapping,
                  bg=COLORS["tile"], fg=COLORS["muted"], activebackground=COLORS["tile_hover"],
                  activeforeground=COLORS["text"], relief="flat", bd=0,
                  font=("Segoe UI", 9), padx=8, pady=8,
                  cursor="hand2").pack(fill="x")
        ttk.Separator(editor).pack(fill="x", pady=14)
        ttk.Label(editor, text="Capture o gatilho físico. A ação salva aparece na tecla visual e neste painel.",
                  wraplength=300).pack(anchor="w")

        self.status_var = tk.StringVar(value="Pronto. Selecione uma tecla visual e defina sua ação.")
        ttk.Label(outer, textvariable=self.status_var, wraplength=900).pack(anchor="w", pady=(12, 0))
        ttk.Label(outer, text="As camadas 1–3 são do app. Associe um evento da tecla física de troca para sincronizá-las; feche o app para parar a captura.",
                  foreground=COLORS["muted"]).pack(anchor="w", pady=(4, 0))
        self._refresh_grid()
        self._select_slot(0)

    def _open_virtual_keyboard(self) -> None:
        window = tk.Toplevel(self.root)
        window.title("Escolher atalho")
        window.resizable(False, False)
        window.configure(bg=COLORS["bg"])
        window.transient(self.root)
        window.grab_set()
        panel = ttk.Frame(window, padding=14)
        panel.pack(fill="both", expand=True)
        ttk.Label(panel, text="Clique nos modificadores e depois na tecla principal.",
                  font=("Segoe UI", 12, "bold")).pack(anchor="w")
        preview = tk.StringVar(value="Atalho: —")
        ttk.Label(panel, textvariable=preview, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(5, 10))
        selected_modifiers: set[str] = set()
        modifier_buttons: dict[str, tk.Button] = {}
        modifiers = ttk.Frame(panel)
        modifiers.pack(anchor="w", pady=(0, 10))

        def show_preview(main_key: str = "") -> str:
            order = ("CTRL", "SHIFT", "ALT", "WIN")
            parts = [name for name in order if name in selected_modifiers]
            if main_key:
                parts.append(main_key)
            value = "+".join(parts)
            preview.set(f"Atalho: {value or '—'}")
            return value

        def toggle_modifier(name: str) -> None:
            if name in selected_modifiers:
                selected_modifiers.remove(name)
            else:
                selected_modifiers.add(name)
            modifier_buttons[name].configure(relief="sunken" if name in selected_modifiers else "raised",
                                             bg=COLORS["accent_dark"] if name in selected_modifiers else COLORS["tile"],
                                             fg=COLORS["accent"] if name in selected_modifiers else COLORS["text"])
            show_preview()

        for name in ("CTRL", "SHIFT", "ALT", "WIN"):
            button = tk.Button(modifiers, text=name, width=9, bg=COLORS["tile"], fg=COLORS["text"],
                               activebackground=COLORS["tile_hover"], relief="flat", bd=0,
                               command=lambda n=name: toggle_modifier(n))
            button.pack(side="left", padx=3)
            modifier_buttons[name] = button

        key_rows = [
            ["ESC", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "BACK"],
            ["TAB", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "[", "]", "\\"],
            ["CAPS", "A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'", "ENTER"],
            ["SHIFT", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", "SHIFT"],
            ["SPACE", "HOME", "END", "PGUP", "PGDN", "LEFT", "DOWN", "UP", "RIGHT"],
        ]
        key_frame = ttk.Frame(panel)
        key_frame.pack(fill="x")
        key_alias = {"ESC": "ESC", "BACK": "BACKSPACE", "CAPS": "CAPSLOCK",
                     "ENTER": "RETURN", "SPACE": "SPACE", "PGUP": "PAGEUP", "PGDN": "PAGEDOWN"}

        def choose_key(label: str) -> None:
            key_name = key_alias.get(label, label)
            value = show_preview(key_name)
            self.mode_var.set("Atalho")
            self.action_var.set(value)
            self._update_action_hint()
            window.destroy()

        for row_index, row in enumerate(key_rows):
            row_frame = ttk.Frame(key_frame)
            row_frame.pack(anchor="w", pady=2)
            for label in row:
                width = 7 if label in ("SPACE", "ENTER", "SHIFT", "CAPS", "BACK", "TAB") else 4
                tk.Button(row_frame, text=label, width=width, height=2, bg=COLORS["tile"], fg=COLORS["text"],
                          activebackground=COLORS["blue"], activeforeground=COLORS["bg"], relief="flat",
                          cursor="hand2", command=lambda key=label: choose_key(key)).pack(side="left", padx=2)
        ttk.Button(panel, text="Cancelar", command=window.destroy).pack(anchor="e", pady=(12, 0))

    def _set_mode(self, mode: str) -> None:
        self.mode_var.set(mode)
        self._update_action_hint()

    def _update_action_hint(self, _event=None) -> None:
        mode = self.mode_var.get()
        hints = {"Texto": "Texto livre para digitar quando a tecla for pressionada.",
                 "Atalho": "Clique nos modificadores e na tecla principal no teclado virtual.",
                 "Mídia": "Escolha um controle de volume ou reprodução para enviar ao Windows.",
                 "Camada": "Digite 1, 2 ou 3 para trocar a camada ativa do aplicativo."}
        self.action_hint.set(hints.get(mode, ""))
        if mode == "Mídia":
            self.action_picker_button.configure(text="♫  ESCOLHER AÇÃO MULTIMÍDIA",
                                                command=self._open_media_picker, state="normal")
        elif mode == "Atalho":
            self.action_picker_button.configure(text="⌨  ESCOLHER NO TECLADO VIRTUAL",
                                                command=self._open_virtual_keyboard, state="normal")
        else:
            self.action_picker_button.configure(text="Escolha Atalho ou Mídia para abrir um seletor",
                                                state="disabled")
        for name, button in self.mode_buttons.items():
            selected = name == mode
            button.configure(bg=COLORS["accent_dark"] if selected else COLORS["tile"],
                             fg=COLORS["accent"] if selected else COLORS["muted"])
        self._update_action_preview()

    def _open_media_picker(self) -> None:
        window = tk.Toplevel(self.root)
        window.title("Ações multimídia")
        window.resizable(False, False)
        window.configure(bg=COLORS["bg"])
        window.transient(self.root)
        window.grab_set()
        panel = ttk.Frame(window, padding=18)
        panel.pack(fill="both", expand=True)
        ttk.Label(panel, text="CONTROLES MULTIMÍDIA", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(panel, text="Clique em uma ação para atribuí-la ao controle selecionado.").pack(anchor="w", pady=(3, 12))
        cards = tk.Frame(panel, bg=COLORS["bg"])
        cards.pack(fill="both", expand=True)
        actions = (("🔉", "Aumentar volume"), ("🔈", "Diminuir volume"),
                   ("🔇", "Silenciar / ativar som"), ("⏮", "Faixa anterior"),
                   ("⏯", "Reproduzir / pausar"), ("⏭", "Próxima faixa"),
                   ("⏹", "Parar mídia"))

        def choose(action: str) -> None:
            self.mode_var.set("Mídia")
            self.action_var.set(action)
            self._update_action_hint()
            window.destroy()

        for index, (icon, action) in enumerate(actions):
            button = tk.Button(cards, text=f"{icon}\n{action}", command=lambda a=action: choose(a),
                               bg=COLORS["tile"], fg=COLORS["text"], activebackground=COLORS["tile_hover"],
                               activeforeground=COLORS["accent"], relief="flat", bd=0,
                               font=("Segoe UI", 10, "bold"), width=21, height=4,
                               wraplength=145, cursor="hand2", highlightthickness=1,
                               highlightbackground=COLORS["line"])
            button.grid(row=index // 3, column=index % 3, padx=5, pady=5, sticky="nsew")
        for col in range(3):
            cards.columnconfigure(col, weight=1)
        ttk.Button(panel, text="Cancelar", command=window.destroy).pack(anchor="e", pady=(10, 0))

    def _update_action_preview(self) -> None:
        value = self.action_var.get().strip()
        mode = self.mode_var.get()
        if not value:
            label = "Ação configurada: —"
        elif mode == "Atalho":
            label = f"Atalho configurado: {value}"
        elif mode == "Mídia":
            label = f"Controle multimídia: {value}"
        elif mode == "Camada":
            label = f"Trocar para camada: {value}"
        else:
            label = f"Texto configurado: {value[:30]}"
        self.action_preview.set(label)

    @staticmethod
    def _map_key(layer: int, slot: int) -> str:
        return f"{layer}:key:{slot}"

    @staticmethod
    def _knob_key(layer: int, action: str) -> str:
        return f"{layer}:knob:{action}"

    def _control_key(self, control: tuple[str, int | str] | None = None) -> str:
        kind, value = control or self.selected_control
        return self._map_key(self.active_layer, int(value)) if kind == "key" else self._knob_key(self.active_layer, str(value))

    def _load_config(self) -> None:
        try:
            raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if raw.get("version") == 4:
                self.layout_size = int(raw.get("layout", 12))
                self.active_layer = max(1, min(3, int(raw.get("active_layer", 1))))
                self.maps = {str(key): dict(value) for key, value in raw.get("mappings", {}).items()}
            elif raw.get("version") == 3:
                self.layout_size = int(raw.get("layout", 12))
                self.active_layer = max(1, min(3, int(raw.get("active_layer", 1))))
                for key, value in raw.get("mappings", {}).items():
                    parts = str(key).split(":")
                    new_key = f"{parts[0]}:key:{parts[1]}" if len(parts) == 2 else str(key)
                    item = dict(value)
                    if "trigger_vks" not in item and "trigger_vk" in item:
                        item["trigger_vks"] = [int(item.pop("trigger_vk"))]
                    self.maps[new_key] = item
            elif raw.get("version") == 2:
                self.layout_size = int(raw.get("layout", 12))
                self.maps = {self._map_key(1, int(slot)):
                             {"trigger_vks": [int(value.get("trigger_vk", 0))],
                              "mode": value.get("mode", "Texto"), "value": value.get("value", "")}
                             for slot, value in raw.get("mappings", {}).items()}
            elif raw.get("version") == 1:
                self.maps = {self._map_key(1, slot):
                             {"trigger_vks": [int(vk)], **value}
                             for slot, (vk, value) in enumerate(raw.get("mappings", {}).items())}
        except FileNotFoundError:
            self.maps = {}
        except Exception as exc:
            messagebox.showwarning("Configuração", f"Não foi possível ler o arquivo de associações:\n{exc}")

    def _save_config(self) -> None:
        payload = {"version": 4, "layout": self.layout_size, "active_layer": self.active_layer,
                   "mappings": self.maps}
        temp = CONFIG_PATH.with_suffix(".tmp")
        temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temp, CONFIG_PATH)

    def _refresh_grid(self) -> None:
        for widget in self.knob_buttons_frame.winfo_children():
            widget.destroy()
        self.knob_buttons.clear()
        knob_specs = (("ccw", "↶  GIRO À ESQUERDA", "Diminuir volume"),
                      ("press", "●  CLIQUE", "Silenciar / ativar som"),
                      ("cw", "GIRO À DIREITA  ↷", "Aumentar volume"))
        for action, label, suggestion in knob_specs:
            item = self.maps.get(self._knob_key(self.active_layer, action))
            caption = label
            if item:
                caption += f"\n{format_trigger([int(v) for v in item['trigger_vks']])}"
                caption += f"\n{action_caption(item, 14)}"
            else:
                caption += f"\nSugestão · {suggestion}"
            selected = self.selected_control == ("knob", action)
            button = tk.Button(self.knob_buttons_frame, text=caption,
                command=lambda a=action: self._select_control(("knob", a)),
                bg=COLORS["accent_dark"] if selected else (COLORS["tile"] if item else COLORS["surface"]),
                fg=COLORS["accent"] if selected else (COLORS["text"] if item else COLORS["muted"]),
                activebackground=COLORS["tile_hover"], activeforeground=COLORS["text"],
                relief="flat", bd=0, font=("Segoe UI", 9, "bold"),
                justify="center", wraplength=150, width=19, height=4, cursor="hand2",
                highlightthickness=2 if selected else 1,
                highlightbackground=COLORS["accent"] if selected else COLORS["line"],
                highlightcolor=COLORS["accent"])
            button.pack(side="left", expand=True, fill="x", padx=4, pady=3)
            self.knob_buttons.append(button)

        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        self.key_buttons.clear()
        columns = 5 if self.layout_size == 15 else 3
        for slot in range(self.layout_size):
            item = self.maps.get(self._map_key(self.active_layer, slot))
            caption = f"{slot + 1:02d}"
            if item:
                caption += f"\n{format_trigger([int(v) for v in item['trigger_vks']])}"
                caption += f"\n{action_caption(item)}"
            else:
                caption += "\n+\nAdicionar ação"
            selected = self.selected_control == ("key", slot)
            button = tk.Button(self.grid_frame, text=caption, command=lambda s=slot: self._select_control(("key", s)),
                bg=COLORS["accent_dark"] if selected else (COLORS["tile"] if item else COLORS["surface"]),
                fg=COLORS["accent"] if selected else (COLORS["text"] if item else COLORS["muted"]),
                activebackground=COLORS["tile_hover"], activeforeground=COLORS["text"],
                relief="flat", bd=0, font=("Segoe UI", 11, "bold"),
                justify="center", wraplength=130, width=16, height=5, cursor="hand2",
                highlightthickness=2 if selected else 1,
                highlightbackground=COLORS["accent"] if selected else COLORS["line"],
                highlightcolor=COLORS["accent"])
            button.grid(row=slot // columns, column=slot % columns, padx=6, pady=6, sticky="nsew")
            self.key_buttons.append(button)
        for col in range(columns):
            self.grid_frame.columnconfigure(col, weight=1)

    def _select_slot(self, slot: int) -> None:
        self._select_control(("key", slot))

    def _select_control(self, control: tuple[str, int | str]) -> None:
        self.capture_pending = False
        self.capture_active.clear()
        self.capture_order.clear()
        self.selected_control = control
        kind, value = control
        if kind == "key":
            self.selected_slot = int(value)
            title = f"Tecla {self.selected_slot + 1:02d}"
        else:
            labels = {"ccw": "Giro à esquerda", "press": "Clique", "cw": "Giro à direita"}
            title = f"Knob 1 · {labels[str(value)]}"
        item = self.maps.get(self._control_key(control), {})
        self.selected_title.set(f"Camada {self.active_layer} · {title}")
        trigger_vks = [int(v) for v in item.get("trigger_vks", [])]
        self.trigger_var.set(format_trigger(trigger_vks) if trigger_vks else "(não definido)")
        self.mode_var.set(str(item.get("mode", "Texto")))
        self.action_var.set(str(item.get("value", "")))
        self.captured_vks = trigger_vks or None
        self._update_action_hint()
        self.status_var.set(f"Editando {title}. Clique em Capturar e use o controle físico correspondente.")
        if hasattr(self, "grid_frame"):
            self._refresh_grid()

    def _layout_changed(self, _event=None) -> None:
        self.layout_size = int(self.layout_var.get().split()[0])
        if self.selected_control[0] == "key":
            self.selected_slot = min(self.selected_slot, self.layout_size - 1)
            self.selected_control = ("key", self.selected_slot)
        self._save_config()
        self._refresh_grid()
        self._select_control(self.selected_control)

    def _select_layer(self, layer: int) -> None:
        self.capture_pending = False
        self.active_layer = layer
        self.capture_active.clear()
        self.capture_order.clear()
        self.layer_status_var.set(f"Camada {layer} ativa")
        for number, button in enumerate(self.layer_buttons, 1):
            selected = number == layer
            button.configure(text=f"● {number}" if selected else str(number),
                             bg=COLORS["accent_dark"] if selected else COLORS["tile"],
                             fg=COLORS["accent"] if selected else COLORS["muted"])
        self._save_config()
        self._refresh_grid()
        self._select_control(self.selected_control)

    def begin_capture(self) -> None:
        self.capture_pending = True
        self.capture_active.clear()
        self.capture_order.clear()
        self.captured_vks = None
        self.trigger_var.set("Pressione a combinação…")
        self.status_var.set("Aguardando a combinação completa. Pressione e solte todas as teclas do gatilho, como Ctrl+A.")

    def save_mapping(self) -> None:
        trigger_vks = getattr(self, "captured_vks", None)
        if not trigger_vks:
            messagebox.showinfo("Gatilho", "Clique em Capturar e pressione a combinação completa do botão físico.")
            return
        value = self.action_var.get()
        if not value:
            messagebox.showinfo("Ação", "Digite o texto ou atalho a enviar.")
            return
        mode = self.mode_var.get()
        if mode == "Atalho":
            try:
                parse_shortcut(value)
            except ValueError as exc:
                messagebox.showerror("Atalho inválido", str(exc))
                return
        elif mode == "Mídia":
            if value not in MEDIA_ACTIONS:
                messagebox.showerror("Ação multimídia inválida", "Escolha uma ação no seletor multimídia.")
                return
        elif mode == "Camada":
            if value not in ("1", "2", "3"):
                messagebox.showerror("Camada inválida", "Digite 1, 2 ou 3.")
                return
        trigger_key = tuple(sorted(trigger_vks))
        current_key = self._control_key()
        for other_key, item in self.maps.items():
            if other_key != current_key and int(other_key.split(":")[0]) == self.active_layer:
                other_trigger = tuple(sorted(int(v) for v in item.get("trigger_vks", [])))
                if other_trigger == trigger_key:
                    messagebox.showerror("Gatilho já usado", f"{format_trigger(trigger_vks)} já está associado a outro controle nesta camada.")
                    return
        self.maps[current_key] = {"trigger_vks": list(trigger_vks), "mode": mode, "value": value}
        try:
            self._save_config()
        except OSError as exc:
            messagebox.showerror("Salvar", f"Não foi possível salvar a associação:\n{exc}")
            return
        self._refresh_grid()
        self._select_control(self.selected_control)
        self.status_var.set(f"Configuração salva para {self.selected_title.get()}.")

    def remove_mapping(self) -> None:
        map_key = self._control_key()
        if map_key not in self.maps:
            return
        del self.maps[map_key]
        self._save_config()
        self._refresh_grid()
        self._select_control(self.selected_control)
        self.status_var.set(f"Configuração removida de {self.selected_title.get()}.")

    def start_hook(self) -> None:
        self.running = True
        thread = threading.Thread(target=self._hook_loop, name="MacroPadKeyboardHook", daemon=True)
        thread.start()
        self.hook_ready.wait(timeout=3)
        if self.hook is None:
            self.status_var.set("Não foi possível ativar a captura global do teclado.")

    def _hook_loop(self) -> None:
        self.hook_thread_id = kernel32.GetCurrentThreadId()
        self.hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self.callback_ref, kernel32.GetModuleHandleW(None), 0)
        self.hook_ready.set()
        if not self.hook:
            return
        msg = MSG()
        while self.running and user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        if self.hook:
            user32.UnhookWindowsHookEx(self.hook)
            self.hook = None

    def _hook_callback(self, n_code: int, w_param: int, l_param: int) -> int:
        if n_code < 0:
            return user32.CallNextHookEx(self.hook, n_code, w_param, l_param)
        info = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
        if info.flags & LLKHF_INJECTED:
            return user32.CallNextHookEx(self.hook, n_code, w_param, l_param)
        down = w_param in (WM_KEYDOWN, WM_SYSKEYDOWN)
        up = w_param in (WM_KEYUP, WM_SYSKEYUP)
        if not down and not up:
            return user32.CallNextHookEx(self.hook, n_code, w_param, l_param)
        vk = int(info.vkCode)
        if self.capture_pending:
            if down and vk not in self.capture_active:
                self.capture_active.add(vk)
                self.capture_order.append(vk)
                preview = list(self.capture_order)
                self.root.after(0, self._capture_preview, preview)
            elif up and vk in self.capture_active:
                self.capture_active.discard(vk)
                if not self.capture_active and self.capture_order:
                    captured = list(self.capture_order)
                    self.capture_order.clear()
                    self.capture_pending = False
                    self.root.after(0, self._captured, captured)
            return 1

        layer_prefix = f"{self.active_layer}:"
        layer_maps = [(item, {int(v) for v in item.get("trigger_vks", [])})
                      for key, item in self.maps.items()
                      if key.startswith(layer_prefix) or item.get("mode") == "Camada"]
        if down:
            if vk in self.pressed:
                if vk in self.suppressed_keyups:
                    return 1
                return user32.CallNextHookEx(self.hook, n_code, w_param, l_param)
            self.pressed.add(vk)
            current = set(self.pressed)
            matching = next(((item, trigger) for item, trigger in layer_maps
                             if trigger and trigger == current), None)
            longer_match_exists = any(trigger > current for _, trigger in layer_maps)
            if matching and not longer_match_exists:
                item, trigger = matching
                self.suppressed_keyups.add(vk)
                self.active_triggers.append((trigger, item))
                return 1
            return user32.CallNextHookEx(self.hook, n_code, w_param, l_param)

        if up:
            self.pressed.discard(vk)
            swallow = vk in self.suppressed_keyups
            self.suppressed_keyups.discard(vk)
            still_active = []
            for trigger, item in self.active_triggers:
                if trigger.isdisjoint(self.pressed):
                    self.root.after(0, self._run_action, item)
                else:
                    still_active.append((trigger, item))
            self.active_triggers = still_active
            if swallow:
                return 1
        return user32.CallNextHookEx(self.hook, n_code, w_param, l_param)

    def _capture_preview(self, vks: list[int]) -> None:
        self.trigger_var.set(format_trigger(vks))
        self.status_var.set("Capturando combinação. Solte todas as teclas para concluir.")

    def _captured(self, vks: list[int]) -> None:
        self.captured_vks = vks
        self.trigger_var.set(format_trigger(vks))
        self.status_var.set(f"Gatilho capturado: {format_trigger(vks)}. Defina a ação e salve a tecla.")

    def _run_action(self, action: dict[str, str | int | list[int]]) -> None:
        try:
            if action["mode"] == "Texto":
                send_text(str(action["value"]))
            elif action["mode"] == "Atalho":
                send_shortcut(str(action["value"]))
            elif action["mode"] == "Mídia":
                send_media_action(str(action["value"]))
            elif action["mode"] == "Camada":
                self._select_layer(int(action["value"]))
                return
            self.status_var.set(f"Ação enviada: {action['mode']} — {action['value']}")
        except Exception as exc:
            self.status_var.set(f"Falha ao enviar ação: {exc}")

    def close(self) -> None:
        self.running = False
        if self.hook_thread_id:
            user32.PostThreadMessageW(self.hook_thread_id, 0x0012, 0, 0)  # WM_QUIT
        self.root.after(100, self.root.destroy)


def main() -> None:
    if os.name != "nt":
        raise SystemExit("Este aplicativo funciona apenas no Windows.")
    root = tk.Tk()
    try:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=COLORS["bg"])
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=("Segoe UI", 9))
        style.configure("TLabelframe", background=COLORS["surface"], foreground=COLORS["text"],
                        bordercolor=COLORS["line"], relief="solid", borderwidth=1)
        style.configure("TLabelframe.Label", background=COLORS["surface"], foreground=COLORS["muted"],
                        font=("Segoe UI", 9, "bold"))
        style.configure("TButton", background=COLORS["tile"], foreground=COLORS["text"],
                        borderwidth=0, padding=(9, 6), font=("Segoe UI", 9, "bold"))
        style.map("TButton", background=[("active", COLORS["tile_hover"]), ("disabled", COLORS["surface"])],
                  foreground=[("disabled", COLORS["muted"]), ("active", COLORS["text"])])
        style.configure("TCombobox", fieldbackground=COLORS["surface"], background=COLORS["tile"],
                        foreground=COLORS["text"], arrowcolor=COLORS["accent"], padding=5)
        style.map("TCombobox", fieldbackground=[("readonly", COLORS["surface"])],
                  foreground=[("readonly", COLORS["text"])])
        style.configure("TEntry", fieldbackground=COLORS["surface"], foreground=COLORS["text"],
                        insertcolor=COLORS["text"], bordercolor=COLORS["line"], padding=8)
        style.configure("TSeparator", background=COLORS["line"])
    except tk.TclError:
        pass
    MacroPadApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
