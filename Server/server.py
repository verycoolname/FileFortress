import socket
import threading
from auth import start_login
from config import DB_URL, DB_NAME

def start():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 5959))
    server_socket.listen(5)
    print("Server is up and running")

    while True:
        client_socket, addr = server_socket.accept()
        print("client connected")
        threading.Thread(target=start_login, args=(client_socket,)).start()

if __name__ == "__main__":
    start()