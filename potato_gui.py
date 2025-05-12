import ctypes
import multiprocessing
import tkinter.ttk as ttk
import webbrowser
from tkinter import *
from tkinter import font

from playsound3 import playsound

from messages import *

APP_WINDOW_TITLE = "Potato.tf Server Checker"
APP_ICON = "images/potato.ico"
NEW_SERVER_SOUND = "sound/new_server.mp3"
SERVER_FULL_SOUND = "sound/server_full.mp3"

BACKGROUND_COLOR = 'gray30'
TEXT_COLOR = 'white'
CONNECT_BUTTON_COLOR = 'gray35'
CONNECT_BUTTON_PRESSED_COLOR = 'gray50'
UNRELATED_SEPARATOR_COLOR = 'white'
RELATED_SEPARATOR_COLOR = 'gray60'

FONT_FAMILY = "TkDefaultFont"
SETTINGS_FONT_SIZE = 12
CONTENT_FONT_SIZE = 16

WINDOW_WIDTH = 1535
WINDOW_HEIGHT = 600
SERVER_FRAME_WIDTH = 920


class PotatoGui:
    def __init__(self, message_queue: multiprocessing.Queue):
        self.root = Tk()

        self.active = BooleanVar(value=True)
        self.new_server_sound = BooleanVar(value=True)
        self.server_full_sound = BooleanVar(value=True)
        self.not_completed = BooleanVar(value=True)
        self.wave_1 = BooleanVar(value=True)
        self.not_in_wave = BooleanVar(value=True)
        self.not_empty = BooleanVar(value=True)
        self.not_full = BooleanVar(value=True)

        self.content_font = font.Font(family=FONT_FAMILY, size=CONTENT_FONT_SIZE)
        self.settings_font = font.Font(family=FONT_FAMILY, size=SETTINGS_FONT_SIZE)
        ttk.Style().configure("TCheckbutton", background=BACKGROUND_COLOR, foreground=TEXT_COLOR, font=self.settings_font)

        self.all_servers_list = None
        self.current_server = CurrentServerData()

        self._setup_gui()
        self._check_for_new_data(message_queue)

    def _check_for_new_data(self, server_q: multiprocessing.Queue) -> None:
        while not server_q.empty():
            server_obj = server_q.get(block=False)
            if isinstance(server_obj, ServerDataList):
                self._process_new_servers_list(server_obj)
            elif isinstance(server_obj, CurrentServerData):
                self._process_new_current_server(server_obj)
        # Rerun this method periodically
        self.root.after(200, self._check_for_new_data, server_q)

    def _process_new_servers_list(self, servers: ServerDataList) -> None:
        if (self.all_servers_list is not None and self.new_server_sound.get() and
                not (set([s.server_name for s in servers.data if self._server_filter(s)])
                        .issubset(set([s.server_name for s in self.all_servers_list if self._server_filter(s)])))):
            playsound(NEW_SERVER_SOUND, block=False)
        self.all_servers_list = servers.data
        self._display_servers()

    def _process_new_current_server(self, server: CurrentServerData) -> None:
        if (self.server_full_sound.get() and
                (not server.is_empty()) and
                self.current_server.player_count != server.player_count and
                server.player_count == server.player_max_count):
            playsound(SERVER_FULL_SOUND, block=False)
        self.current_server = server
        self._display_current_server()

    def _server_filter(self, server: ServerData) -> bool:
        return ((not self.not_in_wave.get() or server.status != 'In-Wave') and
                (not self.wave_1.get() or server.wave == 1) and
                (not self.not_completed.get() or not server.completed) and
                (not self.not_empty.get() or 0 < server.player_count) and
                (not self.not_full.get() or server.player_count < server.player_max_count))

    def _setup_gui(self) -> None:
        # Root window settings
        self.root.title(APP_WINDOW_TITLE)
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('potato.server.checker')
        self.root.iconbitmap(APP_ICON)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.wm_minsize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.root.resizable(False, True)
        self.root.configure(bg=BACKGROUND_COLOR)

        # Settings frame
        self._create_settings_frame()

        # Separator
        Frame(self.root, bg=UNRELATED_SEPARATOR_COLOR, height=2).pack(fill='x')

        # Content frame
        self.content_frame = Frame(self.root, bg=BACKGROUND_COLOR)

        # Servers frame
        self.server_canvas = Canvas(self.content_frame, bg=BACKGROUND_COLOR, highlightthickness=0)
        server_scrollbar = Scrollbar(self.content_frame, orient="vertical", command=self.server_canvas.yview)
        server_scrollbar.configure()
        self.server_canvas.configure(yscrollcommand=server_scrollbar.set)
        self.server_canvas.bind_all("<MouseWheel>", self._scroll_canvas)

        self.server_frame = Frame(self.server_canvas, bg=BACKGROUND_COLOR)
        for i in range(0, 13, 2):
            self.server_frame.columnconfigure(i, weight=1)

        self.server_canvas.create_window((0, 0), window=self.server_frame, anchor="nw", width=SERVER_FRAME_WIDTH, tags="server_frame")
        self.server_frame.bind("<Configure>", lambda e: self.server_canvas.configure(scrollregion=self.server_canvas.bbox("all")))

        self.server_canvas.grid(row=0, column=0, sticky='nsew')
        server_scrollbar.grid(row=0, column=1, sticky='ns')

        # Current server frame
        self.curr_server_frame = Frame(self.content_frame, bg=BACKGROUND_COLOR)
        self.curr_server_frame.grid(row=0, column=2, sticky='new')
        self.curr_server_frame.columnconfigure(3, weight=1)

        self.content_frame.pack(fill='both', expand=True)
        self.content_frame.rowconfigure(0, weight=1)
        self.content_frame.columnconfigure(0, minsize=SERVER_FRAME_WIDTH)
        self.content_frame.columnconfigure(2, weight=1)

    def _scroll_canvas(self, event):
        # Only scroll if a part of the canvas is not visible
        if not self.server_canvas.yview() == (0.0, 1.0):
            self.server_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _create_settings_frame(self) -> None:
        settings_frame = Frame(self.root, bg=BACKGROUND_COLOR)
        self._create_label(settings_frame, "App settings:", _font=self.settings_font).grid(row=0, column=0, padx=3, pady=3, sticky=W)
        new_sound_checkbox = ttk.Checkbutton(settings_frame, text="Play notification sound for new match", variable=self.new_server_sound)
        new_sound_checkbox.grid(row=0, column=1, columnspan=3, padx=3, pady=3, sticky='w')
        full_sound_checkbox = ttk.Checkbutton(settings_frame, text="Play notification sound when current server is full", variable=self.server_full_sound)
        full_sound_checkbox.grid(row=0, column=4, columnspan=2, padx=3, pady=3, sticky='w')

        self._create_label(settings_frame, "Filter settings:", _font=self.settings_font).grid(row=1, column=0, padx=3, pady=3, sticky=W)
        uncompleted_checkbox = ttk.Checkbutton(settings_frame, text="Uncompleted", variable=self.not_completed, command=self._display_servers)
        uncompleted_checkbox.grid(row=1, column=1, padx=3, pady=3, sticky='w')
        wave_1_checkbox = ttk.Checkbutton(settings_frame, text="On wave 1", variable=self.wave_1, command=self._display_servers)
        wave_1_checkbox.grid(row=1, column=2, padx=3, pady=3, sticky='w')
        not_in_wave_checkbox = ttk.Checkbutton(settings_frame, text="Not in wave", variable=self.not_in_wave, command=self._display_servers)
        not_in_wave_checkbox.grid(row=1, column=3, padx=3, pady=3, sticky='w')
        not_empty_checkbox = ttk.Checkbutton(settings_frame, text="Not empty", variable=self.not_empty, command=self._display_servers)
        not_empty_checkbox.grid(row=1, column=4, padx=3, pady=3, sticky='w')
        not_full_checkbox = ttk.Checkbutton(settings_frame, text="Not full", variable=self.not_full, command=self._display_servers)
        not_full_checkbox.grid(row=1, column=5, padx=3, pady=3, sticky='w')

        settings_frame.columnconfigure(5, weight=1)
        settings_frame.pack(fill='x')

    def _create_label(self, parent, text, fg=None, _font=None) -> Label:
        return Label(parent, bg=BACKGROUND_COLOR, font=_font if _font is not None else self.content_font, text=text,
                     fg=fg if fg is not None else TEXT_COLOR)

    def _create_connect_button(self, address):
        return Button(self.server_frame, text="Connect", command=lambda: webbrowser.open(f"steam://connect/{address}"),
                      bg=CONNECT_BUTTON_COLOR, fg=TEXT_COLOR, activebackground=CONNECT_BUTTON_PRESSED_COLOR, activeforeground=TEXT_COLOR)

    def _create_difficulty_label(self, parent: Frame, mission_name: str) -> Label:
        if mission_name.startswith("int"):
            return self._create_label(parent, "Intermediate", 'gold')
        elif mission_name.startswith("adv"):
            return self._create_label(parent, "Advanced", 'green3')
        elif mission_name.startswith("exp"):
            return self._create_label(parent, "Expert", 'crimson')
        elif mission_name.startswith("rev") or mission_name.startswith("reverse"):
            return self._create_label(parent, "Reverse", 'white')
        elif mission_name.startswith("mas"):
            return self._create_label(parent, "Master", 'crimson')
        else:
            return self._create_label(parent, "Unknown", 'white')

    def _create_col_separator(self) -> Frame:
        return Frame(self.server_frame, bg=RELATED_SEPARATOR_COLOR, width=1, height=20)

    def _display_servers(self):
        for child in self.server_frame.winfo_children():
            child.destroy()
        if self.all_servers_list is None:
            return
        filtered_servers = list(filter(self._server_filter, self.all_servers_list))
        if not len(filtered_servers) == 0:
            i = 0
            for server in sorted(filtered_servers, key=lambda s: s.player_count, reverse=True):
                self._create_label(self.server_frame, server.region).grid(row=i, column=0, padx=3, pady=2, sticky=W)
                self._create_col_separator().grid(row=i, column=1)
                self._create_label(self.server_frame, server.map).grid(row=i, column=2, padx=3, pady=2, sticky=W)
                self._create_col_separator().grid(row=i, column=3)
                self._create_label(self.server_frame, server.mission).grid(row=i, column=4, padx=3, pady=2, sticky=W)
                self._create_col_separator().grid(row=i, column=5)
                self._create_difficulty_label(self.server_frame, server.mission_name).grid(row=i, column=6, padx=3, pady=2, sticky=W)
                self._create_col_separator().grid(row=i, column=7)
                self._create_label(self.server_frame, f"W {server.wave}/{server.max_wave}").grid(row=i, column=8, padx=3, pady=2)
                self._create_col_separator().grid(row=i, column=9)
                self._create_label(self.server_frame, f"P {server.player_count}/{server.player_max_count}").grid(row=i, column=10, padx=3, pady=2)
                self._create_col_separator().grid(row=i, column=11)
                self._create_connect_button(server.address).grid(row=i, column=12, padx=3, pady=2, sticky='ew')
                Frame(self.server_frame, bg=RELATED_SEPARATOR_COLOR, height=1).grid(row=i + 1, columnspan=13, sticky='ew')
                i += 2
        else:
            # Update the server frame to force the frame to resize
            Frame(self.server_frame, bg=BACKGROUND_COLOR).grid(row=0)

    def _display_current_server(self):
        for child in self.curr_server_frame.winfo_children():
            child.destroy()
        self._create_label(self.curr_server_frame, "Currently playing").grid(row=0, column=0, padx=3, pady=2, columnspan=4, sticky=N)
        Frame(self.curr_server_frame, bg=RELATED_SEPARATOR_COLOR, height=1).grid(row=1, columnspan=4, sticky='ew')

        if not self.current_server.is_empty():
            self._create_label(self.curr_server_frame, f"Map:").grid(row=2, column=0, padx=3, pady=2, sticky=W)
            self._create_label(self.curr_server_frame, self.current_server.map).grid(row=2, column=1, columnspan=2, padx=3, pady=2, sticky=W)

            self._create_label(self.curr_server_frame, f"Mission:").grid(row=3, column=0, padx=3, pady=2, sticky=W)
            self._create_difficulty_label(self.curr_server_frame, self.current_server.mission_name).grid(row=3, column=1, padx=3, pady=2, sticky=W)
            self._create_label(self.curr_server_frame, self.current_server.mission).grid(row=3, column=2, padx=3, pady=2, sticky=W)
            Frame(self.curr_server_frame, bg=RELATED_SEPARATOR_COLOR, height=1).grid(row=4, columnspan=4, sticky='ew')
            Frame(self.curr_server_frame, bg=BACKGROUND_COLOR, height=25).grid(row=5, columnspan=4, sticky='ew')

            if not len(self.current_server.uncompleted_missions) == 0:
                self._create_label(self.curr_server_frame, "Uncompleted missions on this map (needed by # other players)").grid(row=6, column=0, padx=3, pady=2, columnspan=4, sticky='s')
                Frame(self.curr_server_frame, bg=RELATED_SEPARATOR_COLOR, height=1).grid(row=7, columnspan=4, sticky='ew')

                uncompleted_missions_frame = Frame(self.curr_server_frame, bg=BACKGROUND_COLOR)
                uncompleted_missions_frame.grid(row=8, columnspan=4, sticky='new')
                uncompleted_missions_frame.columnconfigure(3, weight=1)

                i = 0
                for mission in sorted(self.current_server.uncompleted_missions, key=lambda m: m[2], reverse=True):
                    self._create_difficulty_label(uncompleted_missions_frame, mission[1]).grid(row=i, column=0, padx=3, pady=2, sticky=W)
                    self._create_label(uncompleted_missions_frame, mission[0]).grid(row=i, column=1, padx=3, pady=2, sticky=W)
                    self._create_label(uncompleted_missions_frame, f"({mission[2]})").grid(row=i, column=2, padx=3, pady=2, sticky=W)
                    Frame(uncompleted_missions_frame, bg=RELATED_SEPARATOR_COLOR, height=1).grid(row=i + 1, columnspan=4, sticky='ew')
                    i += 2

    def mainloop(self):
        self.root.mainloop()
