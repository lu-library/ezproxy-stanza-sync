"""
Run:   python gui.py
Pack:  pyinstaller --onedir --windowed gui.py
"""

import tkinter as tk
from tkinter import scrolledtext
import subprocess
import threading
import sys
import os
import re
import webbrowser
from datetime import datetime, date

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------
T = {
    "bg":          "#1a1b26",
    "surface":     "#24283b",
    "surface2":    "#2e3354",
    "border":      "#414868",
    "accent":      "#7aa2f7",
    "green":       "#9ece6a",
    "red":         "#f7768e",
    "yellow":      "#e0af68",
    "cyan":        "#7dcfff",
    "purple":      "#bb9af7",
    "text":        "#e8eaf6",
    "subtext":     "#9aa5ce",
    "btn":         "#364180",
    "btn_hover":   "#4a5aaa",
    "btn_active":  "#1e2240",
    "btn_text":    "#ffffff",
    "btn_dis":     "#555c7a",
    "log_bg":      "#13141f",
    "stop":        "#5a1f2a",
    "stop_hover":  "#7a2535",
    "ts":          "#565f89",
    "lv_info":     "#7aa2f7",
    "lv_success":  "#9ece6a",
    "lv_warning":  "#e0af68",
    "lv_error":    "#f7768e",
    "lv_debug":    "#7dcfff",
    "lv_critical": "#ff9e64",
    "ln_stdout":   "#e8eaf6",
    "ln_stderr":   "#e0af68",
    "ln_info":     "#7aa2f7",
    "ln_ok":       "#9ece6a",
    "ln_err":      "#f7768e",
    "ln_warn":     "#e0af68",
    "ln_note":     "#bb9af7",
    "ln_missing":  "#f7768e",
    "ln_link":     "#7dcfff",
}

APP_TITLE  = "Ezproxy Stanza Updates Management Tool"
APP_W, APP_H = 1000, 700
FONT_BTN   = ("Segoe UI", 13, "bold")
FONT_TIP   = ("Segoe UI", 11)
FONT_LOG   = ("Consolas", 11)
FONT_HDR   = ("Segoe UI", 15, "bold")
FONT_SUB   = ("Segoe UI", 11)
FONT_ENTRY = ("Consolas", 12)

_LINK_RE  = re.compile(
    r'(https?://[^\s\'"<>]+'
    r'|(?:[A-Za-z]:\\|/)[^\s\'"<>:*?|]+'
    r'|stanzas/[^\s\'"<>]+)'
)
_LEVEL_RE = re.compile(r'\|\s*(DEBUG|INFO|SUCCESS|WARNING|ERROR|CRITICAL)\s*\|')


def make_btn(parent, text, command, *, bg=None, hover=None,
             font=None, padx=20, pady=8) -> tk.Button:
    """
    Flat tk.Button that swaps background on hover.
    Simulates rounded feel via flat relief + generous padding.
    """
    bg    = bg    or T["btn"]
    hover = hover or T["btn_hover"]
    b = tk.Button(
        parent, text=text,
        font=font or FONT_BTN,
        fg=T["btn_text"], bg=bg,
        activeforeground=T["btn_text"], activebackground=hover,
        relief="flat",
        padx=padx, pady=pady,
        bd=0, cursor="hand2",
        command=command,
    )
    b.bind("<Enter>", lambda e: b.configure(bg=hover)  if str(b["state"]) != "disabled" else None)
    b.bind("<Leave>", lambda e: b.configure(bg=bg)     if str(b["state"]) != "disabled" else None)
    return b


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(f"{APP_W}x{APP_H}")
        self.minsize(900, 600)
        self.configure(bg=T["bg"])

        self._proc: subprocess.Popen | None = None
        self._stop_flag = threading.Event()
        self._all_btns: list[tk.Button] = []

        self._build_ui()
        self._log_info("Application initialized and ready.")

    # -----------------------------------------------------------------------
    # Layout helpers
    # -----------------------------------------------------------------------
    def _section(self) -> tk.Frame:
        """Full-width surface card."""
        outer = tk.Frame(self, bg=T["surface"])
        outer.pack(fill="x", padx=28, pady=(0, 6))
        inner = tk.Frame(outer, bg=T["surface"])
        inner.pack(fill="x", padx=18, pady=14)
        return inner

    def _cmd_col(self, parent, label, tip, cmd):
        """Button (top) + tip label (bottom), expands to fill equal width."""
        col = tk.Frame(parent, bg=T["surface"])
        col.pack(side="left", fill="x", expand=True, padx=(0, 8))
        b = make_btn(col, label, lambda c=cmd, l=label: self._run(c, l))
        b.pack(anchor="w")
        tk.Label(col, text=tip, font=FONT_TIP,
                 fg=T["subtext"], bg=T["surface"],
                 justify="left", anchor="w").pack(anchor="w", pady=(6, 0))
        self._all_btns.append(b)
        return b

    # -----------------------------------------------------------------------
    # UI
    # -----------------------------------------------------------------------
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=T["bg"])
        hdr.pack(fill="x", padx=28, pady=(16, 8))
        tk.Label(hdr, text=APP_TITLE,
                 font=FONT_HDR, fg=T["accent"], bg=T["bg"]).pack(side="left")

        # ── Section 1: Sync | Pack ────────────────────────────────────────
        s1 = self._section()
        self._cmd_col(s1, "Sync",
                      "Sync recent OCLC updates  —  run this weekly",
                      ["uv", "run", "-m", "src.cli", "stanza", "sync"])
        self._cmd_col(s1, "Pack",
                      "Zip config.txt + stanzas/  into ez-config-DATE.zip",
                      ["uv", "run", "-m", "src.cli", "pack"])

        # ── Section 2: Audit ─────────────────────────────────────────────
        s2 = self._section()
        self._audit_section(s2)

        # ── Section 3: Render | Load DB | Check ──────────────────────────
        s3 = self._section()
        self._cmd_col(s3, "Render",
                      "Render config.txt from Jinja2 templates",
                      ["uv", "run", "-m", "src.cli", "stanza", "render"])
        self._cmd_col(s3, "Load DB",
                      "Populate stanzas.db from config.txt",
                      ["uv", "run", "-m", "src.cli", "stanza", "loaddb"])
        self._cmd_col(s3, "Check",
                      "Verify IncludeFile entries match the DB",
                      ["uv", "run", "-m", "src.cli", "stanza", "check"])

        # ── Status bar ───────────────────────────────────────────────────
        sbar = tk.Frame(self, bg=T["bg"])
        sbar.pack(fill="x", padx=28, pady=(8, 0))

        tk.Label(sbar, text="OUTPUT LOG",
                 font=("Segoe UI", 9, "bold"),
                 fg=T["border"], bg=T["bg"]).pack(side="left")

        self._status_lbl = tk.Label(
            sbar, text="●  Ready",
            font=FONT_SUB, fg=T["green"], bg=T["bg"])
        self._status_lbl.pack(side="left", padx=12)

        # Stop — only shown while Audit runs
        self._stop_btn = tk.Button(
            sbar, text="■  Stop",
            font=("Segoe UI", 10, "bold"),
            fg=T["red"], bg=T["stop"],
            activebackground=T["stop_hover"], activeforeground=T["red"],
            relief="flat", padx=12, pady=2,
            command=self._stop,
        )
        # packed/unpacked dynamically — do NOT pack here

        clear_lbl = tk.Label(sbar, text="Clear log",
                             font=FONT_SUB, fg=T["subtext"],
                             bg=T["bg"], cursor="hand2")
        clear_lbl.pack(side="right", padx=4)
        clear_lbl.bind("<Button-1>", lambda _: self._clear_log())

        # Divider + log
        tk.Frame(self, bg=T["border"], height=1).pack(
            fill="x", padx=28, pady=(6, 0))
        self._log = scrolledtext.ScrolledText(
            self, font=FONT_LOG, wrap="word",
            bg=T["log_bg"], fg=T["ln_stdout"],
            insertbackground=T["text"],
            selectbackground=T["accent"],
            relief="flat", borderwidth=0,
            padx=12, pady=10, spacing1=1, spacing3=3,
        )
        self._log.pack(fill="both", expand=True, padx=28, pady=(0, 16))
        self._log.configure(state="disabled")
        self._setup_log_tags()

    # -----------------------------------------------------------------------
    # Audit section: top row = date + button, bottom row = description
    # -----------------------------------------------------------------------
    def _audit_section(self, parent: tk.Frame):
        today = date.today()

        # Top row
        top = tk.Frame(parent, bg=T["surface"])
        top.pack(fill="x")

        # Date inputs (left) — no expand, so Audit button follows immediately
        date_area = tk.Frame(top, bg=T["surface"])
        date_area.pack(side="left")

        tk.Label(date_area, text="Check date:",
                 font=FONT_TIP, fg=T["subtext"],
                 bg=T["surface"]).pack(side="left", padx=(0, 10))

        self._y_var = tk.StringVar(value=str(today.year))
        self._m_var = tk.StringVar(value=f"{today.month:02d}")
        self._d_var = tk.StringVar(value=f"{today.day:02d}")

        def ebox(var, w):
            return tk.Entry(
                date_area, textvariable=var, width=w,
                font=FONT_ENTRY, fg=T["text"], bg=T["surface2"],
                insertbackground=T["text"], relief="flat", justify="center",
                highlightthickness=1,
                highlightbackground=T["border"],
                highlightcolor=T["accent"],
            )

        y_e = ebox(self._y_var, 5)
        m_e = ebox(self._m_var, 3)
        d_e = ebox(self._d_var, 3)
        sep = dict(font=FONT_TIP, fg=T["subtext"], bg=T["surface"])
        y_e.pack(side="left")
        tk.Label(date_area, text="–", **sep).pack(side="left", padx=3)
        m_e.pack(side="left")
        tk.Label(date_area, text="–", **sep).pack(side="left", padx=3)
        d_e.pack(side="left")

        y_e.bind("<Tab>",    lambda e: (m_e.focus_set(), "break"))
        m_e.bind("<Tab>",    lambda e: (d_e.focus_set(), "break"))
        d_e.bind("<Return>", lambda e: self._run_audit())

        # Audit button — immediately after the date inputs
        audit_b = make_btn(top, "Audit", self._run_audit)
        audit_b.pack(side="left", padx=(20, 0))
        self._all_btns.append(audit_b)

        # Bottom row: tip + validation error
        bottom = tk.Frame(parent, bg=T["surface"])
        bottom.pack(fill="x", pady=(8, 0))

        tk.Label(bottom,
                 text="Full historical update check  —  "
                      "defaults to today, or pick an earlier date",
                 font=FONT_TIP, fg=T["subtext"], bg=T["surface"],
                 justify="left", anchor="w").pack(side="left")

        self._date_err = tk.Label(
            parent, text="",
            font=("Segoe UI", 10, "bold"),
            fg=T["red"], bg=T["surface"], anchor="w")
        self._date_err.pack(fill="x", pady=(2, 0))

    # -----------------------------------------------------------------------
    # Audit: validate → run
    # -----------------------------------------------------------------------
    def _run_audit(self):
        if self._proc is not None:
            self._log_err("A task is already running — wait or press Stop.")
            return
        try:
            y = int(self._y_var.get())
            chosen = date(y, int(self._m_var.get()), int(self._d_var.get()))
        except ValueError:
            self._date_err.configure(
                text="⚠  Invalid date — enter integers for year, month, and day")
            return
        if y < 2006:
            self._date_err.configure(
                text="⚠  Year must be 2006 or later")
            return
        if chosen > date.today():
            self._date_err.configure(
                text=f"⚠  {chosen} is in the future — use today or an earlier date")
            return
        self._date_err.configure(text="")
        ds = chosen.strftime("%Y-%m-%d")
        self._run(["uv", "run", "-m", "src.cli", "stanza", "audit", ds],
                  f"Audit  ({ds})", show_stop=True)

    # -----------------------------------------------------------------------
    # Generic run
    # -----------------------------------------------------------------------
    def _run(self, cmd: list[str], label: str, show_stop: bool = False):
        if self._proc is not None:
            self._log_err("A task is already running — wait or press Stop.")
            return

        self._stop_flag.clear()
        self._stopped_by_user = False
        self._set_btns_enabled(False)
        if show_stop:
            self._stop_btn.pack(side="left", padx=(8, 0))
        self._set_status(f"●  Running: {label}", T["yellow"])
        self._log_info(f"▶  {label}   [{' '.join(cmd)}]")

        def worker():
            try:
                cwd = (getattr(sys, "_MEIPASS", None)
                       or os.path.dirname(os.path.abspath(__file__)))

                # start_new_session=True puts the child in its own process group
                # so we can kill uv + the Python it spawns in one shot
                proc = subprocess.Popen(
                    cmd, cwd=cwd,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, bufsize=1,
                    start_new_session=True,
                )
                self._proc = proc

                for raw in proc.stdout:
                    if self._stop_flag.is_set():
                        break
                    self._append_smart(raw.rstrip())

                if self._stop_flag.is_set():
                    # Kill the entire process group (uv + child Python)
                    try:
                        if sys.platform == "win32":
                            subprocess.call(
                                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                            )
                        else:
                            import signal
                            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    except Exception:
                        try:
                            proc.kill()
                        except Exception:
                            pass
                    try:
                        proc.stdout.close()
                        proc.stderr.close()
                    except Exception:
                        pass
                    proc.wait()
                    self._stopped_by_user = True
                    return

                for raw in proc.stderr.read().splitlines():
                    if raw.strip():
                        self._append_smart(raw, force="stderr")

                proc.wait()
                code = proc.returncode
                if code == 0:
                    self._log_ok(f"✔  {label} — done (exit 0)")
                    self.after(0, lambda: self._set_status(
                        "●  Done  ✔", T["green"]))
                else:
                    self._log_err(f"✘  {label} — exited with code {code}")
                    self.after(0, lambda: self._set_status(
                        f"●  Failed (exit {code})", T["red"]))

            except FileNotFoundError:
                self._log_err(f"Command not found: '{cmd[0]}'. "
                              "Make sure 'uv' is installed and on your PATH.")
                self.after(0, lambda: self._set_status(
                    "●  Error — command not found", T["red"]))
            finally:
                self._proc = None
                self.after(0, self._task_finished)

        threading.Thread(target=worker, daemon=True).start()

    # -----------------------------------------------------------------------
    # Stop
    # -----------------------------------------------------------------------
    def _stop(self):
        """Signal the worker to stop. UI feedback happens in _task_finished."""
        if self._proc is not None:
            self._stop_flag.set()
            try:
                self._proc.terminate()   # gentle nudge; worker will SIGKILL
            except Exception:
                pass
        self._log_err("⏹  Audit termination requested. The process may take a few seconds (or up to a minute) to stop completely.")

    def _task_finished(self):
        self._set_btns_enabled(True)
        self._stop_btn.pack_forget()
        if getattr(self, "_stopped_by_user", False):
            self._set_status("●  Stopped", T["yellow"])
            self._stopped_by_user = False

    def _set_btns_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for b in self._all_btns:
            b.configure(
                state=state,
                bg=T["btn"] if enabled else T["btn_active"],
                cursor="hand2" if enabled else "arrow",
            )

    # -----------------------------------------------------------------------
    # Log
    # -----------------------------------------------------------------------
    def _setup_log_tags(self):
        lg = self._log
        for name, fg in [
            ("ts",      T["ts"]),      ("stdout",  T["ln_stdout"]),
            ("stderr",  T["ln_stderr"]),("info",   T["ln_info"]),
            ("ok",      T["ln_ok"]),   ("err",     T["ln_err"]),
            ("warn",    T["ln_warn"]), ("note",    T["ln_note"]),
            ("missing", T["ln_missing"]),
        ]:
            lg.tag_config(name, foreground=fg)
        lg.tag_config("link", foreground=T["ln_link"], underline=True)
        for lvl, fg, bg in [
            ("info",     T["lv_info"],     "#1a2040"),
            ("success",  T["lv_success"],  "#1a2a10"),
            ("warning",  T["lv_warning"],  "#2a2010"),
            ("error",    T["lv_error"],    "#2a1015"),
            ("debug",    T["lv_debug"],    "#101a2a"),
            ("critical", T["lv_critical"], "#2a1500"),
        ]:
            lg.tag_config(f"lv_{lvl}", foreground=fg, background=bg,
                          font=(FONT_LOG[0], FONT_LOG[1] - 1, "bold"))

    def _append_smart(self, text: str, force: str | None = None):
        def write():
            self._log.configure(state="normal")
            self._log.insert(
                "end", f" {datetime.now().strftime('%H:%M:%S')} ", "ts")
            body, body_tag = text, "stdout"
            m = _LEVEL_RE.search(text)
            if m and not force:
                lvl    = m.group(1)
                lv_tag = f"lv_{lvl.lower()}"
                self._log.insert("end", f" {lvl:<8}", lv_tag)
                self._log.insert("end", "  ")
                body     = text[m.end():].lstrip()
                body_tag = lv_tag
            else:
                if force:
                    body_tag = force
                elif re.search(r'\bFILE NOT IN DB\b', text, re.I):
                    body_tag = "missing"
                elif re.search(r'\bmismatch\b', text, re.I):
                    body_tag = "note"
                elif re.search(r'\b(ERROR|FAIL|✘)\b', text, re.I):
                    body_tag = "err"
                elif re.search(r'\b(WARNING|WARN|NOTE)\b', text, re.I):
                    body_tag = "warn"
            self._insert_links(body, body_tag)
            self._log.insert("end", "\n")
            self._log.see("end")
            self._log.configure(state="disabled")
        self.after(0, write)

    def _insert_links(self, text: str, base: str):
        last = 0
        for m in _LINK_RE.finditer(text):
            if m.start() > last:
                self._log.insert("end", text[last:m.start()], base)
            url = m.group(0)
            tag = f"lnk_{abs(hash(url + str(m.start())))}"
            self._log.tag_config(tag, foreground=T["ln_link"], underline=True)
            self._log.tag_bind(tag, "<Button-1>",
                               lambda e, u=url: self._open(u))
            self._log.tag_bind(tag, "<Enter>",
                               lambda e: self._log.configure(cursor="hand2"))
            self._log.tag_bind(tag, "<Leave>",
                               lambda e: self._log.configure(cursor=""))
            self._log.insert("end", url, (tag, "link"))
            last = m.end()
        if last < len(text):
            self._log.insert("end", text[last:], base)

    @staticmethod
    def _open(url: str):
        if url.startswith("http"):
            webbrowser.open(url)
        else:
            p = os.path.abspath(url)
            if sys.platform == "win32":
                os.startfile(p)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", p])
            else:
                subprocess.Popen(["xdg-open", p])

    def _log_line(self, text: str, tag: str):
        def write():
            self._log.configure(state="normal")
            self._log.insert(
                "end", f" {datetime.now().strftime('%H:%M:%S')} ", "ts")
            self._insert_links(text, tag)
            self._log.insert("end", "\n")
            self._log.see("end")
            self._log.configure(state="disabled")
        self.after(0, write)

    def _log_info(self, msg): self._log_line(msg, "info")
    def _log_ok(self,   msg): self._log_line(msg, "ok")
    def _log_err(self,  msg): self._log_line(msg, "err")

    def _clear_log(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")

    def _set_status(self, text: str, colour: str):
        self._status_lbl.configure(text=text, fg=colour)


if __name__ == "__main__":
    app = App()
    app.mainloop()