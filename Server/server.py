import socket
import threading
from auth import start_login


def handle_client(client_socket, addr):
    """
    Handle a single client connection with comprehensive error handling.
    """
    try:
        print(f"New connection from {addr}")
        start_login(client_socket)
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        try:
            client_socket.close()
        except:
            pass


def start_server(host='0.0.0.0', port=8989):
    """
    Start the server with improved error handling and client management.
    """
    # Create server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Allow socket reuse
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind and listen
        server_socket.bind((host, port))
        server_socket.listen(10)  # Increased backlog

        print(f"Server listening on {host}:{port}")

        while True:
            try:
                # Accept client connection
                client_socket, addr = server_socket.accept()

                # Create a thread for each client
                client_thread = threading.Thread(
                    target=handle_client,
                    args=(client_socket, addr),
                    daemon=True  # Allows thread to be terminated when main program exits
                )
                client_thread.start()

            except Exception as accept_error:
                print(f"Error accepting connection: {accept_error}")

    except Exception as start_error:
        print(f"Server startup error: {start_error}")

    finally:
        # Ensure server socket is closed
        server_socket.close()


if __name__ == "__main__":
    start_server()