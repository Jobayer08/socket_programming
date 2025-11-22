import socket
import struct
import threading
import queue
import tkinter as tk
from tkinter import ttk, font

MCAST_GROUP = '224.1.1.1'
MCAST_PORT = 10000
BUFFER_SIZE = 1024

# TELEGRAM-INSPIRED COLOR THEME
THEME = {
    "login_bg_top": "#1e2c3a",
    "login_bg_bottom": "#17212b",
    "title": "#6ab2f2",
    "subtitle": "#7f8b97",
    "entry_bg": "#2b5278",
    "entry_text": "#ffffff",
    "btn_bg": "#3d7ab3",
    "btn_text": "#ffffff",
    "btn_hover": "#4a8ac9",

    "app_bg": "#17212b",
    "sidebar_bg": "#1e2c3a",
    "sidebar_text": "#ffffff",
    "sidebar_header": "#6ab2f2",

    "chat_bg": "#17212b",
    "bubble_me": "#2b5278",
    "bubble_other": "#1e3a5f",
    "bubble_text": "#ffffff",
    "sender_name": "#6ab2f2",

    "input_bg": "#1e2c3a",
    "input_text": "#ffffff",
    "send_bg": "#3d7ab3",
    "send_hover": "#4a8ac9",

    "system_msg": "#7f8b97",
    "online_indicator": "#4caf50",
    "user_icon": "#6ab2f2",
}

class MessengerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Telegram-Style Messenger")
        self.root.geometry("900x600")
        self.root.configure(bg=THEME["login_bg_top"])
        
        # Set window icon (placeholder)
        try:
            self.root.iconbitmap(default='')
        except:
            pass

        self.username = ""
        self.running = True
        self.sock = None

        self.msg_queue = queue.Queue()
        self.active_users = set()

        self.show_login_page()

    # ---------------- LOGIN UI -------------------
    def show_login_page(self):
        self.login_frame = tk.Frame(self.root, bg=THEME["login_bg_top"])
        self.login_frame.pack(fill="both", expand=True)

        # Create gradient effect using multiple frames
        top_frame = tk.Frame(self.login_frame, height=200, bg=THEME["login_bg_top"])
        top_frame.pack(fill="x")
        top_frame.pack_propagate(False)
        
        bottom_frame = tk.Frame(self.login_frame, bg=THEME["login_bg_bottom"])
        bottom_frame.pack(fill="both", expand=True)

        # App logo/icon
        logo_frame = tk.Frame(top_frame, bg=THEME["login_bg_top"])
        logo_frame.pack(expand=True, fill="both")
        
        # Telegram-like icon
        icon_canvas = tk.Canvas(logo_frame, width=80, height=80, bg=THEME["login_bg_top"], 
                               highlightthickness=0)
        icon_canvas.pack(pady=(40, 10))
        # Draw a simple telegram-like icon
        icon_canvas.create_oval(10, 10, 70, 70, fill=THEME["title"], outline="")
        icon_canvas.create_text(40, 40, text="✈", font=("Arial", 24), fill="white")

        tk.Label(
            logo_frame,
            text="Telegram-Style Messenger",
            font=("Segoe UI", 20, "bold"),
            fg=THEME["title"],
            bg=THEME["login_bg_top"]
        ).pack(pady=(0, 5))

        tk.Label(
            logo_frame,
            text="Secure and fast messaging",
            font=("Segoe UI", 11),
            fg=THEME["subtitle"],
            bg=THEME["login_bg_top"]
        ).pack(pady=(0, 40))

        # Login form in bottom frame
        form_frame = tk.Frame(bottom_frame, bg=THEME["login_bg_bottom"])
        form_frame.pack(expand=True)

        tk.Label(
            form_frame,
            text="Enter Your Name",
            font=("Segoe UI", 12),
            fg=THEME["subtitle"],
            bg=THEME["login_bg_bottom"]
        ).pack(pady=(0, 10))

        self.name_entry = tk.Entry(
            form_frame,
            font=("Segoe UI", 13),
            bg=THEME["entry_bg"],
            fg=THEME["entry_text"],
            insertbackground="white",
            bd=0,
            justify="center",
            width=25,
            relief="flat"
        )
        self.name_entry.insert(0, "Your display name")
        self.name_entry.pack(ipady=12, ipadx=10, pady=(0, 20))
        self.name_entry.bind("<FocusIn>", lambda e: self.name_entry.delete(0, "end") if self.name_entry.get() == "Your display name" else None)
        self.name_entry.bind("<Return>", self.start_chat)

        # Style the button with hover effect
        self.join_btn = tk.Button(
            form_frame,
            text="START MESSAGING",
            command=self.start_chat,
            fg=THEME["btn_text"],
            bg=THEME["btn_bg"],
            bd=0,
            font=("Segoe UI", 12, "bold"),
            padx=30,
            pady=12,
            cursor="hand2",
            relief="flat"
        )
        self.join_btn.pack(pady=10)
        
        # Add hover effect
        self.join_btn.bind("<Enter>", lambda e: self.join_btn.config(bg=THEME["btn_hover"]))
        self.join_btn.bind("<Leave>", lambda e: self.join_btn.config(bg=THEME["btn_bg"]))

    # ---------------- CHAT UI -------------------
    def build_chat_ui(self):
        self.login_frame.destroy()

        # MAIN LAYOUT SPLIT: LEFT SIDEBAR + RIGHT CHAT
        container = tk.Frame(self.root, bg=THEME["app_bg"])
        container.pack(fill="both", expand=True)

        # LEFT SIDEBAR - Telegram-like sidebar
        sidebar = tk.Frame(container, bg=THEME["sidebar_bg"], width=280)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Sidebar header
        sidebar_header = tk.Frame(sidebar, bg=THEME["sidebar_bg"], height=60)
        sidebar_header.pack(fill="x", pady=0)
        sidebar_header.pack_propagate(False)
        
        tk.Label(
            sidebar_header,
            text="Telegram",
            bg=THEME["sidebar_bg"],
            fg=THEME["sidebar_header"],
            font=("Segoe UI", 18, "bold")
        ).pack(side="left", padx=20, pady=18)
        
        # User info
        user_frame = tk.Frame(sidebar_header, bg=THEME["sidebar_bg"])
        user_frame.pack(side="right", padx=15, pady=15)
        
        tk.Label(
            user_frame,
            text=f"👤 {self.username}",
            bg=THEME["sidebar_bg"],
            fg=THEME["sidebar_text"],
            font=("Segoe UI", 10)
        ).pack(side="right")

        # Online users section
        users_label_frame = tk.Frame(sidebar, bg=THEME["sidebar_bg"])
        users_label_frame.pack(fill="x", padx=20, pady=(15, 10))
        
        tk.Label(
            users_label_frame,
            text="ONLINE USERS",
            bg=THEME["sidebar_bg"],
            fg=THEME["sidebar_header"],
            font=("Segoe UI", 10, "bold")
        ).pack(side="left")
        
        online_count = tk.Label(
            users_label_frame,
            text="0",
            bg=THEME["sidebar_bg"],
            fg=THEME["system_msg"],
            font=("Segoe UI", 9)
        )
        online_count.pack(side="right")
        self.online_count_label = online_count

        # User list with custom styling
        user_list_frame = tk.Frame(sidebar, bg=THEME["sidebar_bg"])
        user_list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Create a canvas for user list with scrollbar
        user_canvas = tk.Canvas(user_list_frame, bg=THEME["sidebar_bg"], highlightthickness=0)
        user_scrollbar = ttk.Scrollbar(user_list_frame, orient="vertical", command=user_canvas.yview)
        self.user_scrollable_frame = tk.Frame(user_canvas, bg=THEME["sidebar_bg"])

        self.user_scrollable_frame.bind(
            "<Configure>",
            lambda e: user_canvas.configure(scrollregion=user_canvas.bbox("all"))
        )

        user_canvas.create_window((0, 0), window=self.user_scrollable_frame, anchor="nw")
        user_canvas.configure(yscrollcommand=user_scrollbar.set)

        user_canvas.pack(side="left", fill="both", expand=True)
        user_scrollbar.pack(side="right", fill="y")

        # CHAT AREA - Telegram-like chat interface
        chat_area = tk.Frame(container, bg=THEME["chat_bg"])
        chat_area.pack(side="right", fill="both", expand=True)

        # Chat header
        chat_header = tk.Frame(chat_area, bg=THEME["sidebar_bg"], height=60)
        chat_header.pack(fill="x")
        chat_header.pack_propagate(False)
        
        tk.Label(
            chat_header,
            text="Group Chat",
            bg=THEME["sidebar_bg"],
            fg=THEME["sidebar_text"],
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=20, pady=18)
        
        # Message area with modern styling
        msg_container = tk.Frame(chat_area, bg=THEME["chat_bg"])
        msg_container.pack(fill="both", expand=True, padx=0, pady=0)

        self.canvas = tk.Canvas(msg_container, bg=THEME["chat_bg"], highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True, padx=0, pady=0)

        self.msg_frame = tk.Frame(self.canvas, bg=THEME["chat_bg"])
        self.canvas.create_window((0, 0), window=self.msg_frame, anchor="nw", width=600)

        self.msg_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        scrollbar = ttk.Scrollbar(msg_container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # INPUT BAR - Modern input area
        input_frame = tk.Frame(chat_area, bg=THEME["input_bg"], height=70)
        input_frame.pack(fill="x", pady=0)
        input_frame.pack_propagate(False)
        
        input_inner = tk.Frame(input_frame, bg=THEME["input_bg"])
        input_inner.pack(fill="both", expand=True, padx=15, pady=10)

        self.msg_entry = tk.Entry(
            input_inner,
            font=("Segoe UI", 12),
            bg=THEME["input_bg"],
            fg=THEME["input_text"],
            bd=0,
            insertbackground="white",
            relief="flat"
        )
        self.msg_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(10, 5))
        self.msg_entry.bind("<Return>", self.send_msg)
        self.msg_entry.insert(0, "Type a message...")
        self.msg_entry.bind("<FocusIn>", lambda e: self.msg_entry.delete(0, "end") if self.msg_entry.get() == "Type a message..." else None)

        # Send button with hover effect
        self.send_btn = tk.Button(
            input_inner,
            text="Send",
            command=self.send_msg,
            bg=THEME["send_bg"],
            fg="white",
            bd=0,
            font=("Segoe UI", 11, "bold"),
            padx=20,
            pady=8,
            cursor="hand2",
            relief="flat"
        )
        self.send_btn.pack(side="right", padx=5)
        
        # Add hover effect to send button
        self.send_btn.bind("<Enter>", lambda e: self.send_btn.config(bg=THEME["send_hover"]))
        self.send_btn.bind("<Leave>", lambda e: self.send_btn.config(bg=THEME["send_bg"]))

    # ---------------- LOGIC -------------------
    def start_chat(self, event=None):
        name = self.name_entry.get().strip()
        if not name or name == "Your display name":
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
                        self.msg_queue.put(("system", f"{user} joined the chat"))
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
        # Clear the user list
        for widget in self.user_scrollable_frame.winfo_children():
            widget.destroy()
            
        # Update online count
        self.online_count_label.config(text=str(len(self.active_users)))
        
        # Add users to the list
        for user in sorted(self.active_users):
            user_frame = tk.Frame(self.user_scrollable_frame, bg=THEME["sidebar_bg"])
            user_frame.pack(fill="x", pady=2, padx=5)
            
            # User icon and online indicator
            icon_frame = tk.Frame(user_frame, bg=THEME["sidebar_bg"], width=30)
            icon_frame.pack(side="left")
            icon_frame.pack_propagate(False)
            
            # Online indicator (green dot)
            indicator_color = THEME["online_indicator"] if user != self.username else THEME["user_icon"]
            indicator = tk.Frame(icon_frame, bg=indicator_color, width=8, height=8)
            indicator.place(relx=0.5, rely=0.5, anchor="center")
            
            # User name
            name_label = tk.Label(
                user_frame,
                text=user,
                bg=THEME["sidebar_bg"],
                fg=THEME["sidebar_text"],
                font=("Segoe UI", 11),
                anchor="w"
            )
            name_label.pack(side="left", fill="x", expand=True, padx=10)
            
            # Add "You" indicator for current user
            if user == self.username:
                you_label = tk.Label(
                    user_frame,
                    text="(You)",
                    bg=THEME["sidebar_bg"],
                    fg=THEME["system_msg"],
                    font=("Segoe UI", 9),
                    anchor="e"
                )
                you_label.pack(side="right", padx=5)

    def send_msg(self, event=None):
        txt = self.msg_entry.get().strip()
        if not txt or txt == "Type a message...":
            return
        self.send_packet(f"{self.username}: {txt}")
        self.msg_entry.delete(0, "end")

    def send_packet(self, text):
        self.sock.sendto(text.encode(), (MCAST_GROUP, MCAST_PORT))

    # ---------------- MESSAGE RENDERING -------------------
    def show_message(self, sender, text, tag):
        message_frame = tk.Frame(self.msg_frame, bg=THEME["chat_bg"])
        message_frame.pack(fill="x", pady=2)
        
        # Align message to right if it's from me, left if from others
        if tag == "me":
            container = tk.Frame(message_frame, bg=THEME["chat_bg"])
            container.pack(anchor="e", padx=10)
            
            # Message bubble for my messages
            bubble_frame = tk.Frame(container, bg=THEME["bubble_me"], relief="flat")
            bubble_frame.pack(anchor="e", padx=10)
            
            # Message text
            msg_text = tk.Label(
                bubble_frame,
                text=text,
                bg=THEME["bubble_me"],
                fg=THEME["bubble_text"],
                padx=14,
                pady=8,
                wraplength=400,
                justify="left",
                font=("Segoe UI", 11)
            )
            msg_text.pack(anchor="e")
            
        else:
            container = tk.Frame(message_frame, bg=THEME["chat_bg"])
            container.pack(anchor="w", padx=10)
            
            # Sender name for others' messages
            if sender != self.username:
                name_label = tk.Label(
                    container,
                    text=sender,
                    bg=THEME["chat_bg"],
                    fg=THEME["sender_name"],
                    font=("Segoe UI", 10, "bold"),
                    anchor="w"
                )
                name_label.pack(anchor="w", padx=14)
            
            # Message bubble for others' messages
            bubble_frame = tk.Frame(container, bg=THEME["bubble_other"], relief="flat")
            bubble_frame.pack(anchor="w")
            
            # Message text
            msg_text = tk.Label(
                bubble_frame,
                text=text,
                bg=THEME["bubble_other"],
                fg=THEME["bubble_text"],
                padx=14,
                pady=8,
                wraplength=400,
                justify="left",
                font=("Segoe UI", 11)
            )
            msg_text.pack(anchor="w")

        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def show_system_msg(self, text):
        system_frame = tk.Frame(self.msg_frame, bg=THEME["chat_bg"])
        system_frame.pack(fill="x", pady=5)
        
        system_label = tk.Label(
            system_frame,
            text=text,
            fg=THEME["system_msg"],
            bg=THEME["chat_bg"],
            font=("Segoe UI", 9, "italic")
        )
        system_label.pack()
        
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