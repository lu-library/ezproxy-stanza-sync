"""
gui.py  —  EZ-Config Desktop Launcher

Development:  python gui.py            (run from project root)
Package:      pyinstaller --onedir --windowed --name EZ-Config gui.py
              then copy data/ into dist/EZ-Config/
"""

import tkinter as tk
from tkinter import scrolledtext
import threading
import sys
import os
import re
import webbrowser
from pathlib import Path
from datetime import datetime, date

# ---------------------------------------------------------------------------
# Resolve ROOT and fix sys.path so 'src' is importable in both modes
# ---------------------------------------------------------------------------
if getattr(sys, "frozen", False):
    # Running as PyInstaller bundle — exe lives in dist/EZ-Config/
    ROOT = Path(sys.executable).parent
else:
    # Running as plain script — gui.py is at src/gui.py, root is one level up
    ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------------------
# Lazy imports of your src modules (deferred so the window opens fast and
# errors show in the log rather than crashing before the window appears)
# ---------------------------------------------------------------------------
def _import_modules():
    """Import all src modules; return error string or None."""
    try:
        from src import main as _main
        from src import update_stanza as _update_stanza
        from src import generate_config as _generate_config
        from src.db import load_db as _db
        from src import zippack as _pack
        from src.db import check as _check
        return None
    except Exception as e:
        return str(e)

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


def make_btn(parent, text, command, *, font=None, padx=20, pady=8) -> tk.Button:
    bg    = T["btn"]
    hover = T["btn_hover"]
    b = tk.Button(
        parent, text=text,
        font=font or FONT_BTN,
        fg=T["btn_text"], bg=bg,
        activeforeground=T["btn_text"], activebackground=hover,
        relief="flat", padx=padx, pady=pady,
        bd=0, cursor="hand2",
        command=command,
    )
    b.bind("<Enter>", lambda e: b.configure(bg=hover) if str(b["state"]) != "disabled" else None)
    b.bind("<Leave>", lambda e: b.configure(bg=bg)    if str(b["state"]) != "disabled" else None)
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

        self._thread: threading.Thread | None = None
        self._stop_flag = threading.Event()
        self._stopped_by_user = False
        self._all_btns: list[tk.Button] = []

        self._build_ui()
        self._setup_loguru()
        self._log_info(f"Application initialized and ready. (root: {ROOT})")

        # Check imports after window is visible
        self.after(200, self._check_imports)

    def _setup_loguru(self):
        from loguru import logger

        logger.add(
            lambda msg: self._append_smart(msg.rstrip()),
            level="INFO",
            enqueue=True,
        )
    
    def _check_imports(self):
        err = _import_modules()
        if err:
            self._log_err(f"Import error — some buttons may not work: {err}")
        else:
            self._log_info("All modules loaded OK.")

    # -----------------------------------------------------------------------
    # Layout helpers
    # -----------------------------------------------------------------------
    def _section(self) -> tk.Frame:
        outer = tk.Frame(self, bg=T["surface"])
        outer.pack(fill="x", padx=28, pady=(0, 6))
        inner = tk.Frame(outer, bg=T["surface"])
        inner.pack(fill="x", padx=18, pady=14)
        return inner

    def _cmd_col(self, parent, label, tip, fn):
        col = tk.Frame(parent, bg=T["surface"])
        col.pack(side="left", fill="x", expand=True, padx=(0, 8))
        b = make_btn(col, label, fn)
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
        hdr = tk.Frame(self, bg=T["bg"])
        hdr.pack(fill="x", padx=28, pady=(16, 8))
        tk.Label(hdr, text=APP_TITLE,
                 font=FONT_HDR, fg=T["accent"], bg=T["bg"]).pack(side="left")

        # Section 1: Sync | Pack
        s1 = self._section()
        self._cmd_col(s1, "Sync",
                      "Sync recent OCLC updates  —  run this weekly",
                      self._do_sync)
        self._cmd_col(s1, "Pack",
                      "Zip config.txt + stanzas/  into ez-config-DATE.zip",
                      self._do_pack)
        self._cmd_col(s1, "Add Stanza",
                      "Manually insert a stanza entry into the DB",
                      self._do_add_stanza)

        # Section 2: Audit
        s2 = self._section()
        self._audit_section(s2)

        # Section 3: Render | Load DB | Check
        s3 = self._section()
        self._cmd_col(s3, "Render",
                      "Render config.txt from Jinja2 templates",
                      self._do_render)
        self._cmd_col(s3, "Load DB",
                      "Populate stanzas.db from config.txt",
                      self._do_loaddb)
        self._cmd_col(s3, "Check",
                      "Verify IncludeFile entries match the DB",
                      self._do_check)

        # Status bar
        sbar = tk.Frame(self, bg=T["bg"])
        sbar.pack(fill="x", padx=28, pady=(8, 0))
        tk.Label(sbar, text="OUTPUT LOG",
                 font=("Segoe UI", 9, "bold"),
                 fg=T["border"], bg=T["bg"]).pack(side="left")
        self._status_lbl = tk.Label(sbar, text="●  Ready",
                                    font=FONT_SUB, fg=T["green"], bg=T["bg"])
        self._status_lbl.pack(side="left", padx=12)
        self._stop_btn = tk.Button(
            sbar, text="■  Stop",
            font=("Segoe UI", 10, "bold"),
            fg=T["red"], bg=T["stop"],
            activebackground=T["stop_hover"], activeforeground=T["red"],
            relief="flat", padx=12, pady=2,
            command=self._stop,
        )
        clear_lbl = tk.Label(sbar, text="Clear log",
                             font=FONT_SUB, fg=T["subtext"],
                             bg=T["bg"], cursor="hand2")
        clear_lbl.pack(side="right", padx=4)
        clear_lbl.bind("<Button-1>", lambda _: self._clear_log())

        tk.Frame(self, bg=T["border"], height=1).pack(fill="x", padx=28, pady=(6, 0))
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
    # Audit section
    # -----------------------------------------------------------------------
    def _audit_section(self, parent: tk.Frame):
        today = date.today()
        top = tk.Frame(parent, bg=T["surface"])
        top.pack(fill="x")

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

        y_e, m_e, d_e = ebox(self._y_var, 5), ebox(self._m_var, 3), ebox(self._d_var, 3)
        sep = dict(font=FONT_TIP, fg=T["subtext"], bg=T["surface"])
        y_e.pack(side="left")
        tk.Label(date_area, text="–", **sep).pack(side="left", padx=3)
        m_e.pack(side="left")
        tk.Label(date_area, text="–", **sep).pack(side="left", padx=3)
        d_e.pack(side="left")

        y_e.bind("<Tab>",    lambda e: (m_e.focus_set(), "break"))
        m_e.bind("<Tab>",    lambda e: (d_e.focus_set(), "break"))
        d_e.bind("<Return>", lambda e: self._run_audit())

        audit_b = make_btn(top, "Audit", self._run_audit)
        audit_b.pack(side="left", padx=(20, 0))
        self._all_btns.append(audit_b)

        bottom = tk.Frame(parent, bg=T["surface"])
        bottom.pack(fill="x", pady=(8, 0))
        tk.Label(bottom,
                 text="Full historical update check  —  "
                      "defaults to today, or pick an earlier date",
                 font=FONT_TIP, fg=T["subtext"], bg=T["surface"],
                 justify="left", anchor="w").pack(side="left")

        self._date_err = tk.Label(parent, text="",
                                  font=("Segoe UI", 10, "bold"),
                                  fg=T["red"], bg=T["surface"], anchor="w")
        self._date_err.pack(fill="x", pady=(2, 0))

    # -----------------------------------------------------------------------
    # Button actions — each calls the src function directly in a thread
    # -----------------------------------------------------------------------
    def _do_sync(self):
        def task():
            from src import main as m
            m.run()
        self._run_task(task, "Sync")

    def _do_pack(self):
        def task():
            from src import zippack as p
            p.run()
        self._run_task(task, "Pack")

    def _do_render(self):
        def task():
            from src import generate_config as g
            g.run()
        self._run_task(task, "Render")

    def _do_loaddb(self):
        def task():
            from src import db as db
            db.load_db()
        self._run_task(task, "Load DB")

    def _do_check(self):
        def task():
            from src import db as db
            db.check()
        self._run_task(task, "Check")

    def _do_add_stanza(self):
        """Open the Add Stanza dialog."""
        AddStanzaDialog(self)

    def _run_audit(self):
        if self._thread and self._thread.is_alive():
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
            self._date_err.configure(text="⚠  Year must be 2006 or later")
            return
        if chosen > date.today():
            self._date_err.configure(
                text=f"⚠  {chosen} is in the future — use today or an earlier date")
            return
        self._date_err.configure(text="")
        ds = chosen.strftime("%Y-%m-%d")

        def task():
            import src.update_stanza as u
            u.run(ds)
        self._run_task(task, f"Audit  ({ds})", show_stop=True)

    # -----------------------------------------------------------------------
    # Generic task runner — captures stdout/stderr via redirect
    # -----------------------------------------------------------------------
    def _run_task(self, fn, label: str, show_stop: bool = False):
        if self._thread and self._thread.is_alive():
            self._log_err("A task is already running — wait or press Stop.")
            return

        self._stop_flag.clear()
        self._stopped_by_user = False
        self._set_btns_enabled(False)
        if show_stop:
            self._stop_btn.pack(side="left", padx=(8, 0))
        self._set_status(f"●  Running: {label}", T["yellow"])
        self._log_info(f"▶  {label}")

        import io, contextlib

        class StreamToLog(io.TextIOBase):
            """Redirect writes to the GUI log."""
            def __init__(self_, tag="stdout"):
                self_._tag = tag
            def write(self_, s):
                if s and s != "\n":
                    self._append_smart(s.rstrip(), force=self_._tag if self_._tag != "stdout" else None)
                return len(s)
            def flush(self_):
                pass

        def worker():
            stdout_redirect = StreamToLog("stdout")
            stderr_redirect = StreamToLog("stderr")
            try:
                with contextlib.redirect_stdout(stdout_redirect), \
                     contextlib.redirect_stderr(stderr_redirect):
                    fn()
                if not self._stopped_by_user:
                    self._log_ok(f"✔  {label} — done")
                    self.after(0, lambda: self._set_status("●  Done  ✔", T["green"]))
            except Exception as exc:
                self._log_err(f"✘  {label} — {exc}")
                self.after(0, lambda: self._set_status(f"●  Error", T["red"]))
            finally:
                self.after(0, self._task_finished)

        self._thread = threading.Thread(target=worker, daemon=True)
        self._thread.start()

    # -----------------------------------------------------------------------
    # Stop  (sets flag; your src code should check it if long-running)
    # -----------------------------------------------------------------------
    def _stop(self):
        self._stop_flag.set()
        self._stopped_by_user = True

    def _task_finished(self):
        self._set_btns_enabled(True)
        self._stop_btn.pack_forget()
        if self._stopped_by_user:
            self._log_err("⏹  Task terminated by user.")
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
            ("ts", T["ts"]), ("stdout", T["ln_stdout"]), ("stderr", T["ln_stderr"]),
            ("info", T["ln_info"]), ("ok", T["ln_ok"]), ("err", T["ln_err"]),
            ("warn", T["ln_warn"]), ("note", T["ln_note"]), ("missing", T["ln_missing"]),
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
            self._log.insert("end", f" {datetime.now().strftime('%H:%M:%S')} ", "ts")
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
            self._log.tag_bind(tag, "<Button-1>", lambda e, u=url: self._open(u))
            self._log.tag_bind(tag, "<Enter>",    lambda e: self._log.configure(cursor="hand2"))
            self._log.tag_bind(tag, "<Leave>",    lambda e: self._log.configure(cursor=""))
            self._log.insert("end", url, (tag, "link"))
            last = m.end()
        if last < len(text):
            self._log.insert("end", text[last:], base)

    @staticmethod
    def _open(url: str):
        import subprocess
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
            self._log.insert("end", f" {datetime.now().strftime('%H:%M:%S')} ", "ts")
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

# ---------------------------------------------------------------------------
# Add Stanza Dialog
# ---------------------------------------------------------------------------
class AddStanzaDialog(tk.Toplevel):
    def __init__(self, parent: App):
        super().__init__(parent)
        self._parent = parent
        self.title("Add Stanza Entry")
        self.configure(bg=T["bg"])
        self.resizable(False, False)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._cancel)

        self._filename_var = tk.StringVar()
        self._title_var    = tk.StringVar()
        self._section_var  = tk.StringVar(value="oclc")
        self._err_var      = tk.StringVar()

        self._build()
        self._center(parent)

    def _center(self, parent):
        self.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width()  // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px - w//2}+{py - h//2}")

    def _build(self):
        pad = dict(bg=T["bg"])
        outer = tk.Frame(self, bg=T["bg"], padx=28, pady=20)
        outer.pack(fill="both", expand=True)

        tk.Label(outer, text="Add Stanza Entry",
                 font=FONT_HDR, fg=T["accent"], **pad).grid(
                 row=0, column=0, columnspan=3, sticky="w", pady=(0, 16))

        # ── Filename row ──────────────────────────────────────────────────
        tk.Label(outer, text="File (.txt):", font=FONT_TIP,
                 fg=T["subtext"], **pad).grid(row=1, column=0, sticky="w", pady=6)

        fn_entry = tk.Entry(outer, textvariable=self._filename_var, width=28,
                            font=FONT_ENTRY, fg=T["text"], bg=T["surface2"],
                            insertbackground=T["text"], relief="flat",
                            highlightthickness=1,
                            highlightbackground=T["border"],
                            highlightcolor=T["accent"])
        fn_entry.grid(row=1, column=1, sticky="ew", padx=(10, 6), pady=6)

        browse_btn = make_btn(outer, "Browse…", self._browse,
                              padx=10, pady=4, font=FONT_TIP)
        browse_btn.grid(row=1, column=2, pady=6)

        # ── Title row ─────────────────────────────────────────────────────
        tk.Label(outer, text="Title:", font=FONT_TIP,
                 fg=T["subtext"], **pad).grid(row=2, column=0, sticky="w", pady=6)

        tk.Entry(outer, textvariable=self._title_var, width=36,
                 font=FONT_ENTRY, fg=T["text"], bg=T["surface2"],
                 insertbackground=T["text"], relief="flat",
                 highlightthickness=1,
                 highlightbackground=T["border"],
                 highlightcolor=T["accent"]).grid(
                 row=2, column=1, columnspan=2, sticky="ew", padx=(10, 0), pady=6)

        # ── Section radio buttons ─────────────────────────────────────────
        tk.Label(outer, text="Section:", font=FONT_TIP,
                 fg=T["subtext"], **pad).grid(row=3, column=0, sticky="w", pady=6)

        radio_frame = tk.Frame(outer, **pad)
        radio_frame.grid(row=3, column=1, columnspan=2, sticky="w", padx=(10, 0))
        for val in ("oclc", "alumni", "custom" ):
            tk.Radiobutton(
                radio_frame, text=val, variable=self._section_var, value=val,
                font=FONT_TIP, fg=T["text"], bg=T["bg"],
                selectcolor=T["surface2"],
                activebackground=T["bg"], activeforeground=T["accent"],
            ).pack(side="left", padx=(0, 16))

        # ── Note row ──────────────────────────────────────────────────────
        tk.Label(outer, text="Note:", font=FONT_TIP,
                 fg=T["subtext"], **pad).grid(row=4, column=0, sticky="w", pady=6)

        self._note_var = tk.StringVar()
        self._note_entry = tk.Entry(
            outer, textvariable=self._note_var, width=36,
            font=FONT_ENTRY, fg=T["text"], bg=T["surface2"],
            insertbackground=T["text"], relief="flat",
            highlightthickness=1,
            highlightbackground=T["border"],
            highlightcolor=T["accent"],
        )
        self._note_entry.grid(row=4, column=1, columnspan=2,
                              sticky="ew", padx=(10, 0), pady=6)

        tk.Label(outer, text='Leave blank, or "custom stanza" auto-filled for Custom section',
                 font=("Segoe UI", 9), fg=T["subtext"], **pad).grid(
                 row=5, column=1, columnspan=2, sticky="w", padx=(10, 0))

        # ── Error label ───────────────────────────────────────────────────
        self._err_lbl = tk.Label(outer, textvariable=self._err_var,
                                 font=("Segoe UI", 10, "bold"),
                                 fg=T["red"], **pad, anchor="w")
        self._err_lbl.grid(row=6, column=0, columnspan=3, sticky="w", pady=(6, 0))

        # ── Buttons ───────────────────────────────────────────────────────
        btn_row = tk.Frame(outer, **pad)
        btn_row.grid(row=7, column=0, columnspan=3, sticky="e", pady=(16, 0))

        make_btn(btn_row, "Cancel", self._cancel,
                 padx=14, pady=6, font=FONT_TIP).pack(side="left", padx=(0, 8))
        make_btn(btn_row, "Add Entry", self._confirm,
                 padx=14, pady=6, font=FONT_TIP).pack(side="left")

        outer.columnconfigure(1, weight=1)

        def _on_section_change(*_):
            if not hasattr(self, "_note_var"):
                return
            if self._section_var.get() == "custom":
                current = self._note_var.get()
                if current == "" or current == "custom stanza":
                    self._note_var.set("custom stanza")
            else:
                if self._note_var.get() == "custom stanza":
                    self._note_var.set("")

        self._section_var.trace_add("write", _on_section_change)
        _on_section_change()  # 此时 _note_var 已存在，安全


    def _browse(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Select stanza file",
            filetypes=[("Text files", "*.txt")],
        )
        if path:
            name = Path(path).stem   # strip directory and .txt extension
            self._filename_var.set(name)

    def _confirm(self):
        raw_fn  = self._filename_var.get().strip()
        title   = self._title_var.get().strip()
        section = self._section_var.get()

        # Validate
        if not raw_fn:
            self._err_var.set("⚠  Filename is required")
            return
        if not re.match(r'^[\w\-]+$', raw_fn):
            self._err_var.set("⚠  Filename must contain only letters, digits, hyphens, underscores")
            return
        if not title:
            self._err_var.set("⚠  Title is required")
            return

        filename = raw_fn if raw_fn.endswith(".txt") else f"{raw_fn}.txt"
        note = self._note_var.get().strip()

        try:
            from src.db import insert_stanza
            insert_stanza(section, filename, title, note)
        except ValueError as exc:
            self._err_var.set(f"⚠  {exc}")
            return
        except Exception as exc:
            self._err_var.set(f"⚠  DB error: {exc}")
            return

        self._parent._log_ok(f"✔  Added [{section}] {filename} — {title!r}")
        self._close()

    def _cancel(self):
        self._close()

    def _close(self):
        self.grab_release()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()