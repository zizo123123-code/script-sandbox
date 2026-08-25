"""
remote_session_ui.py
====================
ÙØ§Ø¬ÙØ© Tkinter ØªØ­Ø§ÙÙ ÙØ§ÙØ°Ø© Ø¬ÙØ³Ø© Ø§ÙØªØ­ÙÙ Ø¹Ù Ø¨ÙØ¹Ø¯ (Remote Desktop Session)
Ø§ÙÙÙ Ø¸Ø§ÙØ±Ø© ÙÙ ÙÙØ·Ø© Ø§ÙØ´Ø§Ø´Ø©:

  - ÙÙØ¯Ø± ÙÙÙ Ø§Ø³Ù Ø§ÙØ¬ÙØ³Ø© + ÙØ¤Ø´Ø± Ø­Ø§ÙØ© Ø§ÙØ§ØªØµØ§Ù (Connected + Ø§ÙØªØ§ÙÙØ±)
  - ÙØ§ÙÙØ© Ø§ÙØµÙØ§Ø­ÙØ§Øª (Permissions) ÙÙ ÙØ§Ø­Ø¯ Ø¨Ø¹ÙØ§ÙØ© ÙÙØ¹ÙÙ / ØºÙØ± ÙÙØ¹ÙÙ
  - Ø²Ø± Disconnect Ø£Ø­ÙØ± Ø¹Ø±ÙØ¶ ÙÙ Ø§ÙØ¢Ø®Ø±

Ø§ØªØ¨ÙÙ Ø¨Ø§ÙØ¸Ø¨Ø· Ø¹ÙÙ Ø§ÙØ¨ÙØ§ÙØ§Øª Ø§ÙÙÙ ÙÙ Ø§ÙØµÙØ±Ø©:
  Session  : "Just Sssssssss... (172025991)"  |  Connected 02:44:03
  Keys     : Keyboard & Mouse / Clipboard / Sound / File Transfer
             / Restart Remote Device / Video Recording / Block User Input
"""

import tkinter as tk
from tkinter import ttk

# ---------- Ø¨ÙØ§ÙØ§Øª Ø§ÙØ¬ÙØ³Ø© ÙÙ ÙÙØ·Ø© Ø§ÙØ´Ø§Ø´Ø© ----------
SESSION_TITLE = "Just Sssssssss... (172025991)"
CONNECTED_TEXT = "Connected 02:44:03"

# Ø§ÙØµÙØ§Ø­ÙØ§Øª: (Ø§ÙØ§Ø³Ù Ø¨Ø§ÙØ¸Ø¨Ø· Ø²Ù ÙØ§ Ø¸Ø§ÙØ±, ÙÙØ¹ÙÙØ© ÙÙØ§ ÙØ£)
PERMISSIONS = [
    ("Keyboard & Mouse", True),           # ÙÙØ­Ø© Ø§ÙÙÙØ§ØªÙØ­ ÙØ§ÙÙØ§ÙØ³
    ("Clipboard", True),                  # Ø§ÙØ­Ø§ÙØ¸Ø© ÙØ§ÙÙØ²Ø§ÙÙØ©
    ("Sound", True),                      # ÙÙÙ Ø§ÙØµÙØª
    ("File Transfer", True),              # ÙÙÙ Ø§ÙÙÙÙØ§Øª
    ("Restart Remote Device", False),     # Ø¥Ø¹Ø§Ø¯Ø© ØªØ´ØºÙÙ Ø§ÙØ¬ÙØ§Ø² Ø§ÙØ¨Ø¹ÙØ¯
    ("Video Recording", True),            # ØªØ³Ø¬ÙÙ Ø§ÙØ¬ÙØ³Ø© ÙÙØ¯ÙÙ
    ("Block User Input", False),          # Ø­Ø¸Ø± Ø¥Ø¯Ø®Ø§Ù Ø§ÙÙØ³ØªØ®Ø¯Ù
]

# ---------- Ø§ÙØ£ÙÙØ§Ù (Ø«ÙÙ Ø¯Ø§ÙÙ Ø´Ø¨Ù Ø§ÙÙÙØ·Ø©) ----------
BG        = "#1e1e2e"   # Ø§ÙØ®ÙÙÙØ© Ø§ÙØ±Ø¦ÙØ³ÙØ©
PANEL     = "#181825"   # Ø®ÙÙÙØ© Ø§ÙØ¨Ø·Ø§ÙØ§Øª
CARD      = "#26263a"   # ØµÙ Ø§ÙØµÙØ§Ø­ÙØ©
TEXT      = "#cdd6f4"   # ÙÙÙ Ø§ÙÙØµ Ø§ÙØ£Ø³Ø§Ø³Ù
MUTED     = "#7f849c"   # ÙØµ Ø«Ø§ÙÙÙ
GREEN     = "#4ade80"   # ÙÙØ¹ÙÙ / ÙØªØµÙ
RED       = "#ef4444"   # Ø²Ø± ÙØ·Ø¹ Ø§ÙØ§ØªØµØ§Ù
GRAY      = "#52525e"   # ØºÙØ± ÙÙØ¹ÙÙ


class RemoteSessionApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Remote Desktop Session")
        self.geometry("420x740")
        self.resizable(False, False)
        self.configure(bg=BG)

        self._build_header()
        self._build_permissions()
        self._build_disconnect()

    # ---------- 1) Ø§ÙÙÙØ¯Ø±: Ø§Ø³Ù Ø§ÙØ¬ÙØ³Ø© + Ø­Ø§ÙØ© Ø§ÙØ§ØªØµØ§Ù ----------
    def _build_header(self):
        header = tk.Frame(self, bg=PANEL, padx=16, pady=16)
        header.pack(fill="x")

        tk.Label(
            header, text=SESSION_TITLE,
            font=("Segoe UI", 13, "bold"), bg=PANEL, fg=TEXT,
            anchor="w",
        ).pack(fill="x")

        # ØµÙ Ø§ÙØ­Ø§ÙØ©: ÙÙØ·Ø© Ø®Ø¶Ø±Ø§Ø¡ + "Connected 02:44:03"
        status_row = tk.Frame(header, bg=PANEL)
        status_row.pack(fill="x", pady=(8, 0))

        dot = tk.Canvas(status_row, width=12, height=12, bg=PANEL,
                        highlightthickness=0)
        dot.create_oval(2, 2, 10, 10, fill=GREEN, outline="")
        dot.pack(side="left", padx=(0, 6))

        tk.Label(
            status_row, text=CONNECTED_TEXT,
            font=("Segoe UI", 10, "bold"), bg=PANEL, fg=GREEN,
        ).pack(side="left")

        tk.Label(
            header, text="Remote Desktop Session",
            font=("Segoe UI", 9), bg=PANEL, fg=MUTED,
            anchor="w",
        ).pack(fill="x", pady=(10, 0))

    # ---------- 2) ÙØ§ÙÙØ© Ø§ÙØµÙØ§Ø­ÙØ§Øª (Permissions) ----------
    def _build_permissions(self):
        wrapper = tk.Frame(self, bg=BG, padx=16, pady=16)
        wrapper.pack(fill="both", expand=True)

        tk.Label(
            wrapper, text="Permissions",
            font=("Segoe UI", 11, "bold"), bg=BG, fg=TEXT,
            anchor="w",
        ).pack(fill="x", pady=(0, 10))

        for name, enabled in PERMISSIONS:
            self._permission_row(wrapper, name, enabled)

    def _permission_row(self, parent, name: str, enabled: bool):
        row = tk.Frame(parent, bg=CARD, padx=12, pady=10)
        row.pack(fill="x", pady=3)

        # Ø¯Ø§Ø¦Ø±Ø© ÙÙÙÙ: Ø®Ø¶Ø±Ø§Ø¡ (ÙÙØ¹ÙÙ) / Ø±ÙØ§Ø¯ÙØ© (ÙØ´ ÙÙØ¹ÙÙ)
        dot = tk.Canvas(row, width=12, height=12, bg=CARD, highlightthickness=0)
        color = GREEN if enabled else GRAY
        dot.create_oval(2, 2, 10, 10, fill=color, outline="")
        dot.pack(side="left")

        tk.Label(
            row, text=name, font=("Segoe UI", 11), bg=CARD,
            fg=TEXT, anchor="w",
        ).pack(side="left", padx=(10, 0), fill="x", expand=True)

        status = "Enabled" if enabled else "Disabled"
        fg = GREEN if enabled else MUTED
        tk.Label(
            row, text=status, font=("Segoe UI", 9, "bold"), bg=CARD, fg=fg,
        ).pack(side="right")

    # ---------- 3) Ø²Ø± ÙØ·Ø¹ Ø§ÙØ§ØªØµØ§Ù ----------
    def _build_disconnect(self):
        footer = tk.Frame(self, bg=BG, padx=16, pady=16)
        footer.pack(fill="x", side="bottom")

        btn = tk.Button(
            footer, text="Disconnect", font=("Segoe UI", 13, "bold"),
            bg=RED, fg="white", activebackground="#dc2626", activeforeground="white",
            relief="flat", bd=0, cursor="hand2", pady=12,
            command=self.disconnect,
        )
        btn.pack(fill="x")

    # ---------- Ø³ÙÙÙ Ø²Ø± Disconnect ----------
    def disconnect(self):
        # ÙØ­Ø§ÙØ§Ø© ÙØ·Ø¹ Ø§ÙØ§ØªØµØ§Ù: ØªØ­ÙÙÙ Ø§ÙØ­Ø§ÙØ© ÙÙØ£Ø­ÙØ± ÙØªØ·ÙÙ Ø§ÙØ£Ø²Ø±Ø§Ø±
        self.title("Disconnected")
        for child in self.winfo_children():
            child.destroy()
        end = tk.Label(
            self, text="Disconnected", font=("Segoe UI", 16, "bold"),
            bg=BG, fg=RED,
        )
        end.pack(expand=True)


if __name__ == "__main__":
    app = RemoteSessionApp()
    app.mainloop()
