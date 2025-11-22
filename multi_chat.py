import socket
import struct
import threading
import queue
import tkinter as tk
from tkinter import ttk, font

MCAST_GROUP = '224.1.1.1'
MCAST_PORT = 10000
BUFFER_SIZE = 1024

# NEW COLOR THEME (FULLY DIFFERENT)
THEME = {
    "login_bg_top": "#1b2a49",
    "login_bg_bottom": "#162447",
    "title": "#e43f5a",
    "subtitle": "#c5c6c7",
    "entry_bg": "#1f4068",
    "entry_text": "#eeeeee",
    "btn_bg": "#e43f5a",
    "btn_text": "#ffffff",

    "app_bg": "#0d1b2a",
    "sidebar_bg": "#1b263b",
    "sidebar_text": "#ffffff",

    "chat_bg": "#0d1b2a",
    "bubble_me": "#e43f5a",
    "bubble_other": "#415a77",

    "input_bg": "#1b263b",
    "input_text": "#ffffff",
    "send_bg": "#e43f5a",
}

class MessengerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LAN Messenger X")
        self.root.geometry("750x520")
        self.root.configure(bg=THEME["login_bg_top"])

        self.username = ""
        self.running = True
        self.sock = None

        self.msg_queue = queue.Queue()
        self.active_users = set()

        self.show_login_page()

    # ---------------- LOGIN UI -------------------
    def show_login_page(self):
        self.login_frame = tk.Frame(self.root)
        self.login_frame.pack(fill="both", expand=True)

        self.login_frame.configure(bg=THEME["login_bg_top"])

        tk.Label(
            self.login_frame,
            text="LAN Messenger X",
            font=("Calibri", 26, "bold"),
            fg=THEME["title"],
            bg=THEME["login_bg_top"]
        ).pack(pady=(80, 10))

        tk.Label(
            self.login_frame,
            text="Connect with your friends instantly",
            font=("Calibri", 12),
            fg=THEME["subtitle"],
            bg=THEME["login_bg_top"]
        ).pack(pady=(0, 30))

        self.name_entry = tk.Entry(
            self.login_frame,
            font=("Calibri", 13),
            bg=THEME["entry_bg"],
            fg=THEME["entry_text"],
            insertbackground="white",
            bd=0,
            justify="center",
            width=28
        )
        self.name_entry.insert(0, "Enter your display name")
        self.name_entry.pack(ipady=10)
        self.name_entry.bind("<FocusIn>", lambda e: self.name_entry.delete(0, "end"))
        self.name_entry.bind("<Return>", self.start_chat)

        tk.Button(
            self.login_frame,
            text="JOIN CHAT",
            command=self.start_chat,
            fg=THEME["btn_text"],
            bg=THEME["btn_bg"],
            bd=0,
            font=("Calibri", 12, "bold"),
            padx=20,
            pady=8
        ).pack(pady=30)

    # ---------------- CHAT UI -------------------
    def build_chat_ui(self):
        self.login_frame.destroy()

        # MAIN LAYOUT SPLIT: LEFT SIDEBAR + RIGHT CHAT
        container = tk.Frame(self.root, bg=THEME["app_bg"])
        container.pack(fill="both", expand=True)

        # LEFT SIDEBAR
        sidebar = tk.Frame(container, bg=THEME["sidebar_bg"], width=180)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="Online Users",
            bg=THEME["sidebar_bg"],
            fg=THEME["sidebar_text"],
            font=("Calibri", 10, "bold")
        ).pack(pady=10)

        self.user_list = tk.Listbox(
            sidebar,
            bg=THEME["sidebar_bg"],
            fg=THEME["sidebar_text"],
            font=("Calibri", 11),
            highlightthickness=0,
            bd=0
        )
        self.user_list.pack(fill="both", expand=True, padx=10, pady=5)

        # CHAT AREA
        chat_area = tk.Frame(container, bg=THEME["chat_bg"])
        chat_area.pack(side="right", fill="both", expand=True)

        self.canvas = tk.Canvas(chat_area, bg=THEME["chat_bg"], highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self.msg_frame = tk.Frame(self.canvas, bg=THEME["chat_bg"])
        self.canvas.create_window((0, 0), window=self.msg_frame, anchor="nw")

        self.msg_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        scrollbar = ttk.Scrollbar(chat_area, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # INPUT BAR
        bottom = tk.Frame(chat_area, bg=THEME["app_bg"])
        bottom.pack(fill="x", pady=10)

        self.msg_entry = tk.Entry(
            bottom,
            font=("Calibri", 12),
            bg=THEME["input_bg"],
            fg=THEME["input_text"],
            bd=0,
            insertbackground="white"
        )
        self.msg_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(10, 5))
        self.msg_entry.bind("<Return>", self.send_msg)

        tk.Button(
            bottom,
            text="SEND",
            command=self.send_msg,
            bg=THEME["send_bg"],
            fg="white",
            bd=0,
            font=("Calibri", 12, "bold"),
            padx=15,
            pady=5
        ).pack(side="right", padx=10)

    # ---------------- LOGIC -------------------
    def start_chat(self, event=None):
        name = self.name_entry.get().strip()
        if not name:
            return
        self.username = name

        self.build_chat_ui()
        self.network_setup()

        self.active_users.add(self.username)
        self.refresh_user_list()
        self.send_packet(f"__JOIN__:{self.username}")

        self.process_queue()

    def network_setup(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', MCAST_PORT))

        mreq = struct.pack("4sl", socket.inet_aton(MCAST_GROUP), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        threading.Thread(target=self.receiver, daemon=True).start()

    def receiver(self):
        while self.running:
            try:
                data, _ = self.sock.recvfrom(BUFFER_SIZE)
                msg = data.decode()

                if msg.startswith("__JOIN__:"):
                    user = msg.split(":")[1]
                    if user != self.username:
                        self.msg_queue.put(("system", f"{user} joined"))
                        self.msg_queue.put(("add", user))
                        self.send_packet(f"__PRESENCE__:{self.username}")

                elif msg.startswith("__PRESENCE__:"):
                    user = msg.split(":")[1]
                    self.msg_queue.put(("add", user))

                elif msg.startswith("__LEAVE__:"):
                    left = msg.split(":")[1]
                    self.msg_queue.put(("remove", left))

                elif ": " in msg:
                    sender, txt = msg.split(": ", 1)
                    tag = "me" if sender == self.username else "other"
                    self.msg_queue.put(("chat", sender, txt, tag))

            except:
                break

    def process_queue(self):
        while not self.msg_queue.empty():
            item = self.msg_queue.get()
            t = item[0]

            if t == "chat":
                self.show_message(item[1], item[2], item[3])
            elif t == "system":
                self.show_system_msg(item[1])
            elif t == "add":
                self.active_users.add(item[1])
                self.refresh_user_list()
            elif t == "remove":
                self.active_users.discard(item[1])
                self.refresh_user_list()

        self.root.after(100, self.process_queue)

    def refresh_user_list(self):
        self.user_list.delete(0, "end")
        for user in sorted(self.active_users):
            icon = "🟢 " if user != self.username else "👤 "
            self.user_list.insert("end", icon + user)

    def send_msg(self, event=None):
        txt = self.msg_entry.get().strip()
        if not txt:
            return
        self.send_packet(f"{self.username}: {txt}")
        self.msg_entry.delete(0, "end")

    def send_packet(self, text):
        self.sock.sendto(text.encode(), (MCAST_GROUP, MCAST_PORT))

    # ---------------- MESSAGE RENDERING -------------------
    def show_message(self, sender, text, tag):
        row = tk.Frame(self.msg_frame, bg=THEME["chat_bg"])
        row.pack(anchor="w" if tag == "other" else "e", pady=5, fill="x")

        bubble_color = THEME["bubble_me"] if tag == "me" else THEME["bubble_other"]

        msg_label = tk.Label(
            row,
            text=text,
            bg=bubble_color,
            fg="white",
            padx=10,
            pady=6,
            wraplength=350,
            justify="left",
            font=("Calibri", 11)
        )
        msg_label.pack(anchor="w" if tag == "other" else "e", padx=10)

        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def show_system_msg(self, text):
        tk.Label(
            self.msg_frame,
            text=text,
            fg="#e8e8e8",
            bg=THEME["chat_bg"],
            font=("Calibri", 9, "italic")
        ).pack(pady=5)

        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def on_close(self):
        self.running = False
        try:
            self.send_packet(f"__LEAVE__:{self.username}")
            self.sock.close()
        except:
            pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = MessengerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
