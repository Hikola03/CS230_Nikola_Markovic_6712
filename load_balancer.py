import socket
import json
import threading
import time

LB_HOST = "localhost"
LB_PORT = 5000

SERVERS = [
    {"host": "localhost", "port": 5001, "id": 1},
    {"host": "localhost", "port": 5002, "id": 2},
    {"host": "localhost", "port": 5003, "id": 3},
]

HEALTH_CHECK_INTERVAL = 5
HEALTH_CHECK_TIMEOUT  = 2

server_status = {s["port"]: True for s in SERVERS}
active_connections = {s["port"]: 0 for s in SERVERS}
rr_index = 0
lb_lock = threading.Lock()


def health_check_loop():
    while True:
        for s in SERVERS:
            port = s["port"]
            try:
                test = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test.settimeout(HEALTH_CHECK_TIMEOUT)
                test.connect((s["host"], port))
                test.close()
                online = True
            except Exception:
                online = False
            with lb_lock:
                old = server_status[port]
                server_status[port] = online
            if old != online:
                state = "ONLINE ✓" if online else "OFFLINE ✗"
                print(f"[HEALTH] Server {s['id']} (:{port}) → {state}")
        time.sleep(HEALTH_CHECK_INTERVAL)


def pick_server():
    global rr_index
    with lb_lock:
        online = [s for s in SERVERS if server_status[s["port"]]]
    if not online:
        return None
    with lb_lock:
        server = online[rr_index % len(online)]
        rr_index = (rr_index + 1) % len(online)
    return server


def recv_full(sock):
    """Prima kompletan JSON payload (podržava velike fajlove)."""
    chunks = []
    sock.settimeout(30)
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        chunks.append(chunk)
        try:
            json.loads(b"".join(chunks).decode("utf-8"))
            break
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
    return b"".join(chunks)


def forward_to_worker(client_socket, client_addr):
    try:
        raw = recv_full(client_socket)
        if not raw:
            return

        server = pick_server()
        if server is None:
            error = {"status": "ERROR", "message": "All servers are offline"}
            client_socket.send(json.dumps(error).encode("utf-8"))
            return

        port = server["port"]
        print(f"[LB] {client_addr[0]} → Server {server['id']} (:{port})")

        with lb_lock:
            active_connections[port] += 1

        try:
            worker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            worker.settimeout(60)
            worker.connect((server["host"], port))
            worker.sendall(raw)
            response = recv_full(worker)
            worker.close()
            client_socket.sendall(response)
        finally:
            with lb_lock:
                active_connections[port] -= 1

    except Exception as e:
        print(f"[LB] Greška: {e}")
        try:
            err = {"status": "ERROR", "message": "Load balancer error"}
            client_socket.send(json.dumps(err).encode("utf-8"))
        except Exception:
            pass
    finally:
        client_socket.close()


def status_loop():
    while True:
        time.sleep(10)
        with lb_lock:
            print("\n[LB STATUS]")
            for s in SERVERS:
                p = s["port"]
                state = "ONLINE " if server_status[p] else "OFFLINE"
                print(f"  Server {s['id']} (:{p}) | {state} | konekicje: {active_connections[p]}")
            print()


def start():
    threading.Thread(target=health_check_loop, daemon=True).start()
    threading.Thread(target=status_loop, daemon=True).start()

    lb_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lb_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    lb_socket.bind((LB_HOST, LB_PORT))
    lb_socket.listen()

    print(f"[LB] Load Balancer pokrenut na portu {LB_PORT}")
    print(f"[LB] Workeri: {[s['port'] for s in SERVERS]}\n")

    while True:
        client_socket, client_addr = lb_socket.accept()
        threading.Thread(target=forward_to_worker, args=(client_socket, client_addr), daemon=True).start()


if __name__ == "__main__":
    start()