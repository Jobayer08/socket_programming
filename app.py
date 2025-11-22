import socket
import struct
import threading
import time
from flask import Flask, render_template
from flask_socketio import SocketIO

# Multicast configuration
MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='eventlet')

# ---- UDP socket for sending ----
send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)

# ---- UDP socket for receiving ----
recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
recv_sock.bind(('', MCAST_PORT))
mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
recv_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
recv_sock.settimeout(1.0)

# ---- Multicast listener thread ----
def multicast_listener():
    print(f"Multicast listener started on {MCAST_GRP}:{MCAST_PORT}")
    while True:
        try:
            data, addr = recv_sock.recvfrom(65536)
            text = data.decode('utf-8', errors='replace')
            print("Received from multicast:", text)
            # Emit to all connected browsers
            socketio.emit('message', {
                'from': f'{addr[0]}:{addr[1]}',
                'text': text,
                'time': time.strftime('%Y-%m-%d %H:%M:%S')
            }, broadcast=True)
        except socket.timeout:
            continue

# ---- Flask routes ----
@app.route('/')
def index():
    return render_template('index.html')

# ---- Socket.IO send event ----
@socketio.on('send')
def handle_send(data):
    username = data.get('username', 'Anon')
    text = data.get('text', '')
    payload = f"[{username}] {text}"
    print("Sending:", payload)
    send_sock.sendto(payload.encode('utf-8'), (MCAST_GRP, MCAST_PORT))

# ---- Main ----
if __name__ == '__main__':
    # Start listener in background task
    socketio.start_background_task(multicast_listener)
    print("Server running at http://127.0.0.1:5000")
    socketio.run(app, host='127.0.0.1', port=5000, debug=True, use_reloader=False)
