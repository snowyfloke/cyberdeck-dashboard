import threading
import time
import tkinter as tk
from datetime import datetime
import calendar
import urllib.request
import io
 
from auth import get_spotify_client
from player import sp_play, sp_pause, next_song, previous_song, set_volume, get_current_state
from weather import get_weather
from notes import load_notes, save_notes
from sysmonitor import get_system_stats
from theme import THEME
from PIL import Image, ImageTk

# ── Backend ──────────────────────────────────────────────────────────────────

sp = get_spotify_client()

def refresh_client():
    global sp
    while True:
        time.sleep(300)
        sp = get_spotify_client()

threading.Thread(target=refresh_client, daemon=True).start()

# ── RoundedButton ─────────────────────────────────────────────────────────────

class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, radius=None, **kwargs):
        self.bg       = kwargs.pop("bg",               THEME["bg_alt"])
        self.fg       = kwargs.pop("fg",               THEME["text"])
        self.font     = kwargs.pop("font",             (THEME["font_family"], THEME["font_size_lg"]))
        self.active_bg = kwargs.pop("activebackground", THEME["accent"])
        self.active_fg = kwargs.pop("activeforeground", THEME["bg"])
        self.command  = command
        self.text     = text
        kwargs.pop("bd",     None)
        kwargs.pop("padx",   None)
        kwargs.pop("pady",   None)
        kwargs.pop("cursor", None)

        height = kwargs.get("height", 40)
        self.radius = radius if radius is not None else height // 2

        super().__init__(parent, bg=parent["bg"], highlightthickness=0, **kwargs)
        self.bind("<ButtonPress-1>",   self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Configure>",       self._draw)

    def _draw(self, event=None, color=None, text_color=None):
        self.delete("all")
        w, h, r = self.winfo_width(), self.winfo_height(), self.radius
        c = color or self.bg
        self.create_arc(0,     0,     r*2, r*2, start=90,  extent=90,  fill=c, outline=c)
        self.create_arc(w-r*2, 0,     w,   r*2, start=0,   extent=90,  fill=c, outline=c)
        self.create_arc(0,     h-r*2, r*2, h,   start=180, extent=90,  fill=c, outline=c)
        self.create_arc(w-r*2, h-r*2, w,   h,   start=270, extent=90,  fill=c, outline=c)
        self.create_rectangle(r, 0,   w-r, h,   fill=c, outline=c)
        self.create_rectangle(0, r,   w,   h-r, fill=c, outline=c)
        self.create_text(w//2, h//2, text=self.text,
                         fill=text_color or self.fg, font=self.font)

    def _on_press(self, e):
        self._draw(color=self.active_bg, text_color=self.active_fg)

    def _on_release(self, e):
        self._draw()
        if self.command:
            self.command()

    def configure_text(self, text):
        self.text = text
        self._draw()

# ── Widget builder functions ──────────────────────────────────────────────────

def make_widget_frame(parent, title=None, bg=None, fg=None):
    """
    Creates a consistently styled container frame with an optional title label.
    All widgets use this so changing bg_alt in THEME reskins everything at once.
    """
    bg = bg or THEME["bg"]
    fg = fg or THEME["text_alt"]
    outer = tk.Frame(parent, bg=bg, padx=12, pady=12)

    if title:
        tk.Label(
            outer,
            text=title,
            bg=bg,
            fg=fg,
            font=(THEME["font_family"], THEME["font_size_sm"])
        ).pack(anchor="w", pady=(0, 6))

    return outer

# ── Clock widget ──────────────────────────────────────────────────────────────

def build_clock(parent):
    frame = make_widget_frame(parent)

    time_label = tk.Label(
        frame,
        text="",
        bg=THEME["bg"],
        fg=THEME["text"],
        font=(THEME["font_family"], THEME["font_size_xl"], "bold")
    )
    time_label.pack()

    date_label = tk.Label(
        frame,
        text="",
        bg=THEME["bg"],
        fg=THEME["text"],
        font=(THEME["font_family"], THEME["font_size_md"])
    )
    date_label.pack()

    def tick():
        now = datetime.now()
        time_label.config(text=now.strftime("%H:%M:%S"))
        date_label.config(text=now.strftime("%A, %d %B %Y"))
        frame.after(1000, tick)  # update every second

    tick()
    return frame

# ── Calendar widget ───────────────────────────────────────────────────────────

def build_calendar(parent):
    frame = make_widget_frame(parent, title="CALENDAR")

    now   = datetime.now()
    today = now.day
    cal   = calendar.monthcalendar(now.year, now.month)
    
    tk.Label(
        frame,
        text=now.strftime("%B %Y"),
        bg=THEME["bg"],
        fg=THEME["text"],
        font=(THEME["font_family"], THEME["font_size_md"], "bold")
    ).pack(pady=(0, 4))

    grid_frame = tk.Frame(frame, bg=THEME["text_alt"])
    grid_frame.pack()

    # day headers
    for col, day in enumerate(["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]):
        tk.Label(
            grid_frame,
            text=day,
            bg=THEME["bg_alt"],
            fg=THEME["bg"],
            font=(THEME["font_family"], THEME["font_size_sm"]),
            width=3
        ).grid(row=0, column=col, pady=(0, 2))

    # day numbers
    for row, week in enumerate(cal):
        for col, day in enumerate(week):
            if day == 0:
                text = ""
                fg   = THEME["text_alt"]
            elif day == today:
                text = str(day)
                fg   = THEME["bg"]
            else:
                text = str(day)
                fg   = THEME["bg"]

            cell_bg = THEME["bg_alt"] if day == today else THEME["text_alt"]

            tk.Label(
                grid_frame,
                text=text,
                bg=cell_bg,
                fg=fg,
                font=(THEME["font_family"], THEME["font_size_sm"],
                      "bold" if day == today else "normal"),
                width=3
            ).grid(row=row+1, column=col, pady=1)

    return frame

# ── Weather widget ────────────────────────────────────────────────────────────

def build_weather(parent):
    frame = make_widget_frame(parent, title="WEATHER")

    city_label = tk.Label(
        frame,
        text=THEME["weather_city"].upper(),
        bg=THEME["bg"],
        fg=THEME["text"],
        font=(THEME["font_family"], THEME["font_size_sm"])
    )
    city_label.pack()

    temp_label = tk.Label(
        frame,
        text="󰅟 --°C",
        bg=THEME["bg"],
        fg=THEME["accent"],
        font=(THEME["font_family"], THEME["font_size_lg"], "bold")
    )
    temp_label.pack(pady=(4, 0))

    condition_label = tk.Label(
        frame,
        text="Loading...",
        bg=THEME["bg"],
        fg=THEME["text_alt"],
        font=(THEME["font_family"], THEME["font_size_sm"])
    )
    condition_label.pack()

    def refresh_weather():
        # runs in a background thread so it doesn't freeze the GUI during the request
        def fetch():
            data = get_weather(THEME["weather_city"])
            if data["error"]:
                temp_label.config(text="--°C")
                condition_label.config(text="Unavailable")
            else:
                temp_label.config(text=f"󰅟 {data['temp_c']}°C")
                condition_label.config(text=data["condition"])
            frame.after(600000, refresh_weather)  # refresh every 10 minutes

        threading.Thread(target=fetch, daemon=True).start()

    refresh_weather()
    return frame

# ── Notes widget ──────────────────────────────────────────────────────────────

def build_notes(parent):
    frame = make_widget_frame(parent, title="NOTES", bg=THEME["bg_alt"], fg=THEME["bg"])
    notes = load_notes(THEME["notes_folder"])

    listbox = tk.Listbox(
        frame,
        bg=THEME["text_alt"],
        fg=THEME["bg"],
        selectbackground=THEME["bg_alt"],
        selectforeground=THEME["bg"],
        font=(THEME["font_family"], THEME["font_size_sm"]),
        bd=0,
        highlightthickness=0,
        activestyle="none",
        height=8,
        width=90,
    )
    listbox.pack()

    for note in notes:
        listbox.insert(tk.END, f"• {note}")

    # input row
    input_frame = tk.Frame(frame, bg=THEME["bg_alt"])
    input_frame.pack(fill=tk.X, pady=(6, 0))

    entry = tk.Entry(
        input_frame,
        bg=THEME["text_alt"],
        fg=THEME["bg"],
        insertbackground=THEME["bg"],  # cursor color
        font=(THEME["font_family"], THEME["font_size_sm"]),
        bd=0,
        highlightthickness=1,
        highlightcolor=THEME["bg"],
        highlightbackground=THEME["bg_alt"],
    )
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 4))

    def add_note():
        text = entry.get().strip()
        if not text:
            return
        notes.append(text)
        listbox.insert(tk.END, f"• {text}")
        save_notes(THEME["notes_folder"], notes)  # write to disk immediately
        entry.delete(0, tk.END)

    def delete_selected(e=None):
        selected = listbox.curselection()
        if not selected:
            return
        idx = selected[0]
        listbox.delete(idx)
        notes.pop(idx)
        save_notes(THEME["notes_folder"], notes)  # write to disk immediately

    entry.bind("<Return>", lambda e: add_note())           # add on Enter
    listbox.bind("<Delete>", delete_selected)              # delete selected on Delete key
    listbox.bind("<BackSpace>", delete_selected)

    RoundedButton(
        input_frame,
        text="+",
        command=add_note,
        bg=THEME["bg_alt"],
        fg=THEME["bg"],
        activebackground=THEME["accent"],
        activeforeground=THEME["bg"],
        width=26,
        height=26,
    ).pack(side=tk.LEFT, padx=(4, 4))

    return frame

# ── System Monitor widget ─────────────────────────────────────────────────────
 
def build_sysmonitor(parent):
    frame = make_widget_frame(parent, title="SYSTEM")
 
    def make_stat_row(label_text):
        row = tk.Frame(frame, bg=THEME["bg"])
        row.pack(fill=tk.X, pady=2)
 
        tk.Label(
            row,
            text=label_text,
            bg=THEME["bg"],
            fg=THEME["text"],
            font=(THEME["font_family"], THEME["font_size_sm"]),
            width=5,
            anchor="w"
        ).pack(side=tk.LEFT)
 
        bar = tk.Canvas(
            row,
            bg=THEME["bg"],
            highlightthickness=0,
            height=10,
            width=120,
        )
        bar.pack(side=tk.LEFT, padx=(4, 6))
 
        val_label = tk.Label(
            row,
            text="--",
            bg=THEME["bg"],
            fg=THEME["text"],
            font=(THEME["font_family"], THEME["font_size_sm"]),
            width=10,
            anchor="w"
        )
        val_label.pack(side=tk.LEFT)
 
        return val_label, bar
 
    def draw_bar(bar, percent):
        bar.delete("all")
        w = bar.winfo_width() or 120
        fill_w = int(w * (percent / 100))
        color = THEME["accent"] if percent < 80 else "#FF4444"
        bar.create_rectangle(0, 0, fill_w, 10, fill=color, outline="")
 
    cpu_val,  cpu_bar  = make_stat_row("CPU")
    ram_val,  ram_bar  = make_stat_row("RAM")
    disk_val, disk_bar = make_stat_row("DISK")
 
    status_label = tk.Label(
        frame,
        text="Connecting...",
        bg=THEME["bg"],
        fg=THEME["text"],
        font=(THEME["font_family"], THEME["font_size_sm"])
    )
    status_label.pack(pady=(4, 0))
 
    def refresh():
        def fetch():
            stats = get_system_stats(THEME["pc_ip"])
            if stats is None:
                frame.after(0, lambda: status_label.config(text="PC unreachable"))
                frame.after(0, lambda: cpu_val.config(text="--"))
                frame.after(0, lambda: ram_val.config(text="--"))
                frame.after(0, lambda: disk_val.config(text="--"))
            else:
                def update_ui():
                    status_label.config(text="")
                    cpu_val.config(text=f"{stats['cpu_percent']}%")
                    ram_val.config(text=f"{stats['ram_used_gb']}/{stats['ram_total_gb']} GB")
                    disk_val.config(text=f"{stats['disk_used_gb']}/{stats['disk_total_gb']} GB")
                    draw_bar(cpu_bar,  stats["cpu_percent"])
                    draw_bar(ram_bar,  stats["ram_percent"])
                    draw_bar(disk_bar, stats["disk_percent"])
                frame.after(0, update_ui)  # tkinter widgets must always be updated on the main thread
 
            frame.after(2000, refresh)  # refresh every 2 seconds
 
        threading.Thread(target=fetch, daemon=True).start()
 
    refresh()
    return frame

# ── Spotify widget ────────────────────────────────────────────────────────────

def build_spotify(parent):
    frame = make_widget_frame(parent, title="Spotify")

    inner = tk.Frame(frame, bg=THEME["bg"])
    inner.pack(expand=True, fill=tk.BOTH)

    track_label = tk.Label(
        inner,
        text="Nothing Currently Playing...",
        bg=THEME["bg"],
        fg=THEME["text"],
        font=(THEME["font_family"], THEME["font_size_lg"], "bold")
    )
    track_label.pack(pady=(0, 2))

    artist_label = tk.Label(
        inner,
        text="",
        bg=THEME["bg"],
        fg=THEME["text"],
        font=(THEME["font_family"], THEME["font_size_sm"])
    )
    artist_label.pack()

    album_label = tk.Label(inner, bg=THEME["bg"])
    album_label.pack(pady=(8, 0))

    # controls
    controls_frame = tk.Frame(inner, bg=THEME["bg"])
    controls_frame.pack(pady=12)

    btn_style = {
        "bg":               THEME["bg_alt"],
        "fg":               THEME["bg"],
        "font":             (THEME["font_family"], THEME["font_size_lg"]),
        "activebackground": THEME["accent"],
        "activeforeground": THEME["bg"],
        "width":            THEME["button_width"],
        "height":           THEME["button_height"],
    }

    RoundedButton(controls_frame, text="  ", command=lambda: previous_song(sp), **btn_style).pack(side=tk.LEFT, padx=4)
    RoundedButton(controls_frame, text=" ⏸ ", command=lambda: sp_pause(sp),      **btn_style).pack(side=tk.LEFT, padx=4)
    RoundedButton(controls_frame, text=" ▶ ",  command=lambda: sp_play(sp),       **btn_style).pack(side=tk.LEFT, padx=4)
    RoundedButton(controls_frame, text="  ", command=lambda: next_song(sp),      **btn_style).pack(side=tk.LEFT, padx=4)

    # volume
    vol_frame = tk.Frame(inner, bg=THEME["bg"])
    vol_frame.pack()

    tk.Label(
        vol_frame,
        text="VOL",
        bg=THEME["bg"],
        fg=THEME["text"],
        font=(THEME["font_family"], THEME["font_size_sm"])
    ).pack(side=tk.LEFT, padx=(0, 8))

    volume_slider = tk.Scale(
        vol_frame,
        from_=0, to=100,
        orient=tk.HORIZONTAL,
        length=THEME["slider_length"],
        bg=THEME["bg_alt"],
        fg=THEME["text"],
        troughcolor=THEME["text_alt"],
        activebackground=THEME["accent"],
        highlightthickness=0,
        bd=0,
        showvalue=False,
    )
    volume_slider.bind("<ButtonRelease-1>", lambda e: set_volume(sp, volume_slider.get()))
    volume_slider.pack(side=tk.LEFT)

    # album cover loader
    album_photo_ref = [None]  # list used to keep reference alive without a class

    def load_album_cover(url):
        with urllib.request.urlopen(url) as response:
            data = response.read()
        img = Image.open(io.BytesIO(data))
        img = img.resize((80, 80))
        album_photo_ref[0] = ImageTk.PhotoImage(img)
        album_label.config(image=album_photo_ref[0])

    def update():
        state = get_current_state(sp)
        if state and state["item"]:
            track_label.config(text=state["item"]["name"])
            artist_label.config(text=state["item"]["artists"][0]["name"])
            threading.Thread(
                target=load_album_cover,
                args=(state["item"]["album"]["images"][1]["url"],),
                daemon=True
            ).start()
        else:
            track_label.config(text="Nothing Playing")
            artist_label.config(text="")
            album_label.config(image="")

        frame.after(5000, update)

    update()
    return frame

# ── Dashboard layout ──────────────────────────────────────────────────────────

class Dashboard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dashboard")
        self.root.configure(bg=THEME["bg"])
        self.root.geometry(f"{THEME['window_width']}x{THEME['window_height']}")

        PAD = 10

        # ── Row 0: Clock (full width) ─────────────────────────────────────
        clock = build_clock(self.root)
        clock.pack(fill=tk.X, padx=PAD, pady=(PAD, 0))

        # ── Row 1: Weather | Calendar | Notes (3 columns) ────────────────
        middle = tk.Frame(self.root, bg=THEME["bg"])
        middle.pack(fill=tk.X, padx=PAD, pady=PAD)

        build_weather(middle).pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, PAD))
        build_calendar(middle).pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, PAD))
        build_notes(middle).pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ── Row 2: Sysmonitor | Spotify ───────────────────────────────────────
        bottom = tk.Frame(self.root, bg=THEME["bg"])
        bottom.pack(fill=tk.BOTH, expand=True, padx=PAD, pady=(0, PAD))
        
        sysmon = build_sysmonitor(bottom)
        sysmon.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, PAD))

        build_spotify(bottom).pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.root.mainloop()

Dashboard()
