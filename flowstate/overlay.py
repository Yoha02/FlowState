"""Floating always-on-top overlay — persists over all windows.

Starts compact (just status bar + demo button). Expands automatically
when the agent produces content (handoff, plan, actions).

Connects to the FlowState SSE stream in a background thread.
"""

import json
import threading
import tkinter as tk
from tkinter import font as tkfont
from urllib.request import urlopen, Request

API_BASE = "http://localhost:8000"

# Dusk palette
COLORS = {
    "bg": "#0a0a12",
    "surface": "#111120",
    "card": "#1c1c32",
    "border": "#2e2e48",
    "text": "#ffffff",
    "muted": "#a0a0b8",
    "accent": "#2eeab8",
    "blue": "#7cb8ff",
    "calm": "#2eeab8",
    "elevated": "#fdd44b",
    "stressed": "#ff9633",
    "critical": "#ff5555",
}

# Size presets
MINIMIZED_W, MINIMIZED_H = 200, 32
COMPACT_W, COMPACT_H = 280, 120
EXPANDED_W, EXPANDED_H = 340, 520


class FlowStateOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FlowState")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.75)
        self.root.configure(bg=COLORS["bg"])

        # Position bottom-right, start compact
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self._anchor_x = screen_w - EXPANDED_W - 20
        self._anchor_y = screen_h - COMPACT_H - 60
        self.root.geometry(f"{COMPACT_W}x{COMPACT_H}+{self._anchor_x}+{self._anchor_y}")
        self._is_expanded = False
        self._is_minimized = False

        # Resize handle state
        self._resize_x = 0
        self._resize_y = 0

        # Drag state
        self._drag_x = 0
        self._drag_y = 0

        # Data state
        self.state_label = "calm"
        self.stress = 0.0
        self.fatigue = 0.0
        self.consecutive = 0
        self.showing_plan = False
        self.handoff_pending = False

        # Fonts
        self.font_mono = tkfont.Font(family="Consolas", size=9)
        self.font_mono_sm = tkfont.Font(family="Consolas", size=8)
        self.font_title = tkfont.Font(family="Segoe UI", size=11, weight="bold")
        self.font_btn = tkfont.Font(family="Consolas", size=9)

        self._build_ui()
        self._start_sse_listener()

    # ── UI Construction ──

    def _build_ui(self):
        root = self.root

        # Title bar (always visible, draggable)
        title_bar = tk.Frame(root, bg=COLORS["surface"], height=32)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)
        for w in (title_bar,):
            w.bind("<Button-1>", self._start_drag)
            w.bind("<B1-Motion>", self._on_drag)

        self.status_dot = tk.Canvas(title_bar, width=10, height=10,
                                     bg=COLORS["surface"], highlightthickness=0)
        self.status_dot.pack(side="left", padx=(10, 4))
        self._dot_id = self.status_dot.create_oval(1, 1, 9, 9, fill=COLORS["calm"], outline="")

        title_lbl = tk.Label(title_bar, text="FlowState", font=self.font_title,
                             fg=COLORS["text"], bg=COLORS["surface"])
        title_lbl.pack(side="left", padx=4)
        title_lbl.bind("<Button-1>", self._start_drag)
        title_lbl.bind("<B1-Motion>", self._on_drag)

        self.state_badge = tk.Label(title_bar, text="CALM", font=self.font_mono_sm,
                                     fg=COLORS["calm"], bg=COLORS["surface"])
        self.state_badge.pack(side="right", padx=10)

        close_btn = tk.Label(title_bar, text="\u2715", font=self.font_mono,
                             fg=COLORS["muted"], bg=COLORS["surface"], cursor="hand2")
        close_btn.pack(side="right", padx=(0, 4))
        close_btn.bind("<Button-1>", lambda e: self.root.destroy())

        # Minimize button
        self.min_btn = tk.Label(title_bar, text="\u2014", font=self.font_mono,
                                fg=COLORS["muted"], bg=COLORS["surface"], cursor="hand2")
        self.min_btn.pack(side="right", padx=(0, 2))
        self.min_btn.bind("<Button-1>", lambda e: self._minimize())

        # Metrics row (compact — always visible)
        self.metrics_frame = tk.Frame(root, bg=COLORS["bg"], padx=12, pady=6)
        self.metrics_frame.pack(fill="x")
        self._build_bar(self.metrics_frame, "stress")
        self._build_bar(self.metrics_frame, "fatigue")
        self.consecutive_label = tk.Label(self.metrics_frame, text="consecutive: 0/3",
                                           font=self.font_mono_sm, fg=COLORS["muted"],
                                           bg=COLORS["bg"], anchor="w")
        self.consecutive_label.pack(fill="x", pady=(2, 0))

        # ── Expandable section (hidden initially) ──
        self.expand_frame = tk.Frame(root, bg=COLORS["bg"])
        # NOT packed yet — shown on expand

        tk.Frame(self.expand_frame, bg=COLORS["border"], height=1).pack(fill="x")

        # Action feed
        feed_frame = tk.Frame(self.expand_frame, bg=COLORS["bg"])
        feed_frame.pack(fill="both", expand=True)

        self.feed_text = tk.Text(feed_frame, bg=COLORS["bg"], fg=COLORS["muted"],
                                  font=self.font_mono_sm, wrap="word",
                                  relief="flat", borderwidth=0, padx=12, pady=8,
                                  state="disabled", cursor="arrow",
                                  selectbackground=COLORS["card"])
        self.feed_text.pack(fill="both", expand=True)
        self.feed_text.tag_configure("action", foreground=COLORS["text"])
        self.feed_text.tag_configure("plan", foreground=COLORS["accent"])
        self.feed_text.tag_configure("done", foreground=COLORS["calm"])
        self.feed_text.tag_configure("header", foreground=COLORS["blue"])

        # ── Button area (always at bottom) ──
        self.btn_sep = tk.Frame(root, bg=COLORS["border"], height=1)
        self.btn_sep.pack(fill="x", side="bottom")
        self.btn_frame = tk.Frame(root, bg=COLORS["bg"], padx=12, pady=8)
        self.btn_frame.pack(fill="x", side="bottom")

        self.demo_btn = self._make_button(self.btn_frame, "Start", self._start_demo)
        self.demo_btn.pack(fill="x")

        self.handoff_frame = tk.Frame(self.btn_frame, bg=COLORS["bg"])
        self.approve_btn = self._make_button(self.handoff_frame, "Approve Takeover",
                                              self._approve_handoff, accent=True)
        self.reject_btn = self._make_button(self.handoff_frame, "Reject",
                                             self._reject_handoff)
        self.approve_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.reject_btn.pack(side="right", fill="x", expand=True, padx=(4, 0))

        self.confirm_btn = self._make_button(self.btn_frame, "Confirm Plan",
                                              self._confirm_plan, accent=True)

        # ── Resize grip (bottom-right corner) ──
        grip = tk.Label(root, text="\u25e2", font=("Consolas", 8),
                        fg=COLORS["muted"], bg=COLORS["bg"], cursor="size_nw_se")
        grip.place(relx=1.0, rely=1.0, anchor="se")
        grip.bind("<Button-1>", self._start_resize)
        grip.bind("<B1-Motion>", self._on_resize)

    def _build_bar(self, parent, name):
        row = tk.Frame(parent, bg=COLORS["bg"])
        row.pack(fill="x", pady=1)
        tk.Label(row, text=name, font=self.font_mono_sm, fg=COLORS["muted"],
                 bg=COLORS["bg"], width=7, anchor="w").pack(side="left")
        bar_bg = tk.Canvas(row, height=4, bg=COLORS["border"], highlightthickness=0)
        bar_bg.pack(side="left", fill="x", expand=True, padx=(4, 0))
        bar_fill = bar_bg.create_rectangle(0, 0, 0, 4, fill=COLORS["calm"], outline="")
        if name == "stress":
            self._stress_bar_bg = bar_bg
            self._stress_bar_fill = bar_fill
        else:
            self._fatigue_bar_bg = bar_bg
            self._fatigue_bar_fill = bar_fill

    def _make_button(self, parent, text, command, accent=False):
        fg = COLORS["bg"] if accent else COLORS["muted"]
        bg = COLORS["accent"] if accent else COLORS["card"]
        btn = tk.Label(parent, text=text, font=self.font_btn, fg=fg, bg=bg,
                       padx=12, pady=6, cursor="hand2", relief="flat", borderwidth=0)
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", lambda e: btn.configure(
            bg=COLORS["calm"] if accent else COLORS["border"]))
        btn.bind("<Leave>", lambda e: btn.configure(bg=bg))
        return btn

    # ── Expand / Collapse ──

    def _expand(self):
        if self._is_expanded:
            return
        self._is_expanded = True
        self.expand_frame.pack(fill="both", expand=True, before=self.btn_sep)
        # Grow window downward from current position
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        self.root.geometry(f"{EXPANDED_W}x{EXPANDED_H}+{x}+{y}")

    def _collapse(self):
        if not self._is_expanded or self._is_minimized:
            return
        self._is_expanded = False
        self.expand_frame.pack_forget()
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        self.root.geometry(f"{COMPACT_W}x{COMPACT_H}+{x}+{y}")

    def _minimize(self):
        """Collapse to just the title bar strip."""
        if self._is_minimized:
            self._restore()
            return
        self._is_minimized = True
        self._was_expanded = self._is_expanded
        self._is_expanded = False
        self.expand_frame.pack_forget()
        self.metrics_frame.pack_forget()
        self.btn_frame.pack_forget()
        self.btn_sep.pack_forget()
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        self.root.geometry(f"{MINIMIZED_W}x{MINIMIZED_H}+{x}+{y}")
        self.min_btn.configure(text="\u25a1")  # restore icon

    def _restore(self):
        """Restore from minimized to previous size."""
        self._is_minimized = False
        self.metrics_frame.pack(fill="x", after=self.root.winfo_children()[0])
        self.btn_sep.pack(fill="x", side="bottom")
        self.btn_frame.pack(fill="x", side="bottom")
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        if self._was_expanded:
            self._is_expanded = False  # let _expand re-pack
            self._expand()
        else:
            self.root.geometry(f"{COMPACT_W}x{COMPACT_H}+{x}+{y}")
        self.min_btn.configure(text="\u2014")  # minimize icon

    # ── Drag ──

    def _start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag(self, event):
        x = self.root.winfo_x() + event.x - self._drag_x
        y = self.root.winfo_y() + event.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    # ── Resize ──

    def _start_resize(self, event):
        self._resize_x = event.x_root
        self._resize_y = event.y_root

    def _on_resize(self, event):
        dx = event.x_root - self._resize_x
        dy = event.y_root - self._resize_y
        self._resize_x = event.x_root
        self._resize_y = event.y_root
        new_w = max(220, self.root.winfo_width() + dx)
        new_h = max(100, self.root.winfo_height() + dy)
        self.root.geometry(f"{new_w}x{new_h}")

    # ── SSE Listener ──

    def _start_sse_listener(self):
        threading.Thread(target=self._sse_loop, daemon=True).start()

    def _sse_loop(self):
        import time
        while True:
            try:
                req = Request(f"{API_BASE}/status/stream")
                req.add_header("Accept", "text/event-stream")
                req.add_header("Cache-Control", "no-cache")
                with urlopen(req, timeout=120) as resp:
                    event_type = ""
                    data_buf = ""
                    for raw_line in resp:
                        line = raw_line.decode("utf-8", errors="replace").rstrip("\n\r")
                        if line.startswith("event:"):
                            event_type = line.split(":", 1)[1].strip()
                        elif line.startswith("data:"):
                            data_buf = line.split(":", 1)[1].strip()
                        elif line == "":
                            if event_type and data_buf:
                                self._dispatch(event_type, data_buf)
                            event_type = ""
                            data_buf = ""
            except Exception:
                time.sleep(2)

    def _dispatch(self, event_type: str, data_str: str):
        try:
            data = json.loads(data_str) if data_str else {}
        except json.JSONDecodeError:
            return
        self.root.after(0, self._handle_event, event_type, data)

    # ── Event Handling ──

    def _handle_event(self, event_type: str, data: dict):
        if event_type == "status_update":
            self.state_label = data.get("state", "calm")
            self.stress = data.get("stress", 0.0)
            self.fatigue = data.get("fatigue", 0.0)
            self.consecutive = data.get("consecutive", 0)
            self._update_status()

        elif event_type == "handoff_trigger":
            self.handoff_pending = True
            if self._is_minimized:
                self._restore()
            self._expand()
            self._add_feed_line("Handoff requested — approve or reject", "header")
            self._show_handoff_buttons()

        elif event_type == "plan_proposal":
            plan = data.get("plan", "")
            self.showing_plan = True
            if self._is_minimized:
                self._restore()
            self._expand()
            self._add_feed_line("--- Agent Plan ---", "header")
            for line in plan.split("\n"):
                self._add_feed_line(line, "plan")
            self._add_feed_line("", "plan")
            self._show_confirm_button()

        elif event_type == "action":
            step = data.get("step", "")
            self._expand()
            self._add_feed_line(f"> {step}", "action")

        elif event_type == "done":
            msg = data.get("message", "Done")
            self._add_feed_line(f"[DONE] {msg}", "done")
            self._show_demo_button()
            self.handoff_pending = False
            self.showing_plan = False
            # Collapse after 5 seconds
            self.root.after(5000, self._collapse)

        elif event_type == "task_context":
            task_type = data.get("task_type", "unknown")
            summary = data.get("summary", "")
            self._expand()
            self._add_feed_line(f"[Context] {task_type}: {summary[:80]}", "header")

    def _update_status(self):
        color = COLORS.get(self.state_label, COLORS["calm"])
        self.status_dot.itemconfig(self._dot_id, fill=color)
        self.state_badge.configure(text=self.state_label.upper(), fg=color)
        self._update_bar(self._stress_bar_bg, self._stress_bar_fill, self.stress, color)
        self._update_bar(self._fatigue_bar_bg, self._fatigue_bar_fill, self.fatigue, COLORS["blue"])
        self.consecutive_label.configure(text=f"consecutive: {self.consecutive}/3")

    def _update_bar(self, canvas, rect_id, value, color):
        canvas.update_idletasks()
        w = canvas.winfo_width()
        fill_w = max(1, int(w * value))
        canvas.coords(rect_id, 0, 0, fill_w, 4)
        canvas.itemconfig(rect_id, fill=color)

    def _add_feed_line(self, text, tag="action"):
        self.feed_text.configure(state="normal")
        self.feed_text.insert("end", text + "\n", tag)
        self.feed_text.see("end")
        self.feed_text.configure(state="disabled")

    # ── Button visibility ──

    def _show_demo_button(self):
        self.handoff_frame.pack_forget()
        self.confirm_btn.pack_forget()
        self.demo_btn.pack(fill="x")

    def _show_handoff_buttons(self):
        self.demo_btn.pack_forget()
        self.confirm_btn.pack_forget()
        self.handoff_frame.pack(fill="x")

    def _show_confirm_button(self):
        self.demo_btn.pack_forget()
        self.handoff_frame.pack_forget()
        self.confirm_btn.pack(fill="x")

    # ── API calls ──

    def _start_demo(self):
        self._add_feed_line("Starting demo escalation...", "header")
        self._expand()
        self._api_post("/demo/start")

    def _approve_handoff(self):
        self._add_feed_line("Handoff approved", "done")
        self._api_post("/handoff/respond", {"approved": True})
        self.handoff_pending = False

    def _reject_handoff(self):
        self._add_feed_line("Handoff rejected", "action")
        self._api_post("/handoff/respond", {"approved": False})
        self._show_demo_button()
        self.handoff_pending = False

    def _confirm_plan(self):
        self._add_feed_line("Plan confirmed — executing...", "done")
        self._api_post("/plan/confirm")
        self._show_demo_button()
        self.showing_plan = False

    def _api_post(self, path, body=None):
        def _do():
            try:
                data = json.dumps(body).encode() if body else b"{}"
                req = Request(f"{API_BASE}{path}", data=data, method="POST")
                req.add_header("Content-Type", "application/json")
                with urlopen(req, timeout=5):
                    pass
            except Exception:
                pass
        threading.Thread(target=_do, daemon=True).start()

    def run(self):
        self.root.mainloop()


def main():
    overlay = FlowStateOverlay()
    overlay.run()


if __name__ == "__main__":
    main()
