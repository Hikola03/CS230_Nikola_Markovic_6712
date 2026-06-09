import socket
import json
import sys
from middleware import execute_request
import threading

HOST = "localhost"


def handle_client(client_socket, client_addr, server_id):
    try:
        # 4MB buffer - potreban za prenos fajlova
        chunks = []
        client_socket.settimeout(30)
        while True:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
            try:
                # pokušaj parsiranja - ako uspe, primili smo kompletan JSON
                data_raw = b"".join(chunks).decode("utf-8")
                json.loads(data_raw)
                break
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue

        data_raw = b"".join(chunks).decode("utf-8")

        if not data_raw:
            client_socket.close()
            return

        try:
            data = json.loads(data_raw)
        except json.JSONDecodeError:
            error_response = {"status": "ERROR", "message": "Invalid JSON"}
            client_socket.send(json.dumps(error_response).encode("utf-8"))
            return

        username = data.get("username", "unknown")
        action   = data.get("action", "unknown")
        print(f"[SERVER {server_id}] {client_addr[0]} | user:{username} | action:{action}")

        response = execute_request(data, server_id, client_addr[0])

        response_bytes = json.dumps(response).encode("utf-8")
        client_socket.sendall(response_bytes)

        print(f"[SERVER {server_id}] Response sent → {response.get('status')}")

    except Exception as e:
        print(f"[SERVER {server_id}] Error: {e}")

    finally:
        client_socket.close()


def start_server(port):
    server_id = port - 5000

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, port))
    server_socket.listen()

    print(f"SERVER {server_id} running on port {port}")

    while True:
        client_socket, client_addr = server_socket.accept()

        thread = threading.Thread(
            target=handle_client,
            args=(client_socket, client_addr, server_id)
        )
        thread.start()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python server.py <port>")
        sys.exit()

    port = int(sys.argv[1])
    start_server(port)