import socket
import json
import threading
import time

# ============================================================
#  KONFIGURACIJA
# ============================================================
LB_HOST = "localhost"
LB_PORT = 5000

SERVERS = [
    {"host": "localhost", "port": 5001, "id": 1},
    {"host": "localhost", "port": 5002, "id": 2},
    {"host": "localhost", "port": 5003, "id": 3},
]

HEALTH_CHECK_INTERVAL = 5
HEALTH_CHECK_TIMEOUT  = 2

# ============================================================
#  STANJE LOAD BALANCERA
# ============================================================
server_status = {s["port"]: True for s in SERVERS}
active_connections = {s["port"]: 0 for s in SERVERS}
rr_index = 0
lb_lock = threading.Lock()


# ============================================================
#  HEALTH CHECK
# ============================================================
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

            # loguj samo kad se stanje promeni
            if old != online:
                state = "ONLINE ✓" if online else "OFFLINE ✗"
                print(f"[HEALTH] Server {s['id']} (:{port}) → {state}")

        time.sleep(HEALTH_CHECK_INTERVAL)


# ============================================================
#  IZBOR SERVERA  (Round-Robin, samo ONLINE serveri)
# ============================================================
def pick_server():

    global rr_index

    with lb_lock:
        online = [s for s in SERVERS if server_status[s["port"]]]

    if not online:
        return None

    with lb_lock:
        # rr_index % len(online) → uvek u opsegu
        server = online[rr_index % len(online)]
        rr_index = (rr_index + 1) % len(online)

    return server


# ============================================================
#  PROSLJEĐIVANJE ZAHTJEVA  (po jedna nit po klijentu)
# ============================================================
def forward_to_worker(client_socket, client_addr):

    try:
        raw = client_socket.recv(4096).decode("utf-8")
        if not raw:
            return

        server = pick_server()

        if server is None:
            error = {"status": "ERROR", "message": "All servers are offline"}
            client_socket.send(json.dumps(error).encode("utf-8"))
            print(f"[LB] ✗ Svi serveri OFFLINE – zahtev od {client_addr[0]} odbijen")
            return

        port = server["port"]
        print(f"[LB] {client_addr[0]} → Server {server['id']} (:{port})")

        # povećaj brojač aktivnih konekcija
        with lb_lock:
            active_connections[port] += 1

        try:
            worker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            worker.settimeout(10)
            worker.connect((server["host"], port))
            worker.send(raw.encode("utf-8"))

            response_raw = worker.recv(4096).decode("utf-8")
            worker.close()

            client_socket.send(response_raw.encode("utf-8"))

        finally:
            # smanji brojač kad konekcija završi (čak i pri gresci)
            with lb_lock:
                active_connections[port] -= 1

    except Exception as e:
        print(f"[LB] Greška pri prosleđivanju: {e}")
        try:
            err = {"status": "ERROR", "message": "Load balancer error"}
            client_socket.send(json.dumps(err).encode("utf-8"))
        except Exception:
            pass

    finally:
        client_socket.close()


# ============================================================
#  STATUS ISPIS  (opcionalno, svakih 10 sek)
# ============================================================
def status_loop():
    while True:
        time.sleep(10)
        with lb_lock:
            print("\n[LB STATUS]")
            for s in SERVERS:
                p = s["port"]
                state = "ONLINE " if server_status[p] else "OFFLINE"
                conns = active_connections[p]
                print(f"  Server {s['id']} (:{p}) | {state} | aktivne konekcije: {conns}")
            print()


# ============================================================
#  GLAVNI SERVER LOOP
# ============================================================
def start():
    # pokreni health-check nit (daemon → gasi se kad se glavni program ugasi)
    hc_thread = threading.Thread(target=health_check_loop, daemon=True)
    hc_thread.start()

    # pokreni status nit
    st_thread = threading.Thread(target=status_loop, daemon=True)
    st_thread.start()

    lb_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lb_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    lb_socket.bind((LB_HOST, LB_PORT))
    lb_socket.listen()

    print(f"[LB] Load Balancer pokrenut na portu {LB_PORT}")
    print(f"[LB] Workeri: {[s['port'] for s in SERVERS]}\n")

    while True:
        client_socket, client_addr = lb_socket.accept()

        # svaki klijent dobija svoju nit (dispecer model iz lekcije)
        t = threading.Thread(
            target=forward_to_worker,
            args=(client_socket, client_addr),
            daemon=True
        )
        t.start()


if __name__ == "__main__":
    start()
