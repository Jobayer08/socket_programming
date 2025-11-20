import socket
import struct
import threading

MULTICAST_GROUP = '224.1.1.1'   # Multicast address
PORT = 5007                   # Port number

def receive_messages(sock):
    """Receive messages and print to screen"""
    while True:
        data, address = sock.recvfrom(1024)
        print(f"\n[Message from {address}] {data.decode()}")
        print("You: ",end="", flush=True)

def main():
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    # Allow multiple programs to use same port
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind socket to port
    sock.bind(('', PORT))

    # Join multicast group
    mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    # Thread to receive messages
    threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()

    print("=== Multicast Chat Started ===")
    print("Type your messages below...\n")

    # Send messages
    while True:
        message = input()
        sock.sendto(message.encode(), (MULTICAST_GROUP, PORT))

if __name__ == "__main__":
    main()
