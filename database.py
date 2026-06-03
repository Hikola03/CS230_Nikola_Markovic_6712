import json
import time
import os

DB_FILE = "logs.json"


# ======================
# CORE DATABASE LAYER
# ======================

def create_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump([], f)


def read_logs():
    create_db()
    with open(DB_FILE, "r") as f:
        return json.load(f)


def write_logs(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)


def save_data(client_ip, router_ip, router_name, server_id, result, time_ms):
    data = read_logs()

    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "client_ip": client_ip,
        "router_ip": router_ip,
        "router_name": router_name,
        "status": result,
        "time_ms": time_ms,
        "server_id": server_id
    }

    data.append(entry)
    write_logs(data)


# ======================
# ADMIN FUNCTIONS
# ======================

def print_all_logs():
    data = read_logs()

    if not data:
        print("No logs found")
        return

    print("\n===== ALL LOGS =====")
    for d in data:
        print(d)
    print("====================\n")


def filter_by_ip(ip):
    data = read_logs()

    found = False

    print(f"\n===== LOGS FOR IP: {ip} =====")

    for d in data:
        if d["router_ip"] == ip:
            print(d)
            found = True

    if not found:
        print("No logs for this IP")

    print("============================\n")


def last_n_logs(n):
    data = read_logs()

    print(f"\n===== LAST {n} LOGS =====")

    for d in data[-n:]:
        print(d)

    print("========================\n")


def reset_logs():
    write_logs([])
    print("Logs cleared")


# ======================
# STATISTICS ENGINE
# ======================

def stats():
    data = read_logs()

    if not data:
        print("No logs found")
        return

    total = len(data)
    online = len([d for d in data if d["status"] == "ONLINE"])
    offline = len([d for d in data if d["status"] == "OFFLINE"])

    avg_time = sum(d["time_ms"] for d in data) / total

    print("\n===== STATISTICS =====")
    print(f"Total requests: {total}")
    print(f"ONLINE: {online}")
    print(f"OFFLINE: {offline}")
    print(f"Average response time: {round(avg_time, 2)} ms")
    print("======================\n")


def stats_by_server():
    data = read_logs()

    result = {}

    for d in data:
        sid = d["server_id"]
        result.setdefault(sid, 0)
        result[sid] += 1

    print("\n===== REQUESTS BY SERVER =====")
    for k, v in result.items():
        print(f"Server {k}: {v} requests")
    print("==============================\n")


def stats_by_router():
    data = read_logs()

    result = {}

    for d in data:
        name = d["router_name"]
        result.setdefault(name, 0)
        result[name] += 1

    print("\n===== REQUESTS BY ROUTER =====")
    for k, v in result.items():
        print(f"{k}: {v} requests")
    print("==============================\n")


# ======================
# ADMIN MENU
# ======================

def admin_menu():
    while True:
        print("\n===== ADMIN PANEL =====")
        print("1. Prikaži sve logove")
        print("2. Statistika (globalna)")
        print("3. Statistika po serveru")
        print("4. Statistika po routeru")
        print("5. Filtriraj po IP")
        print("6. Poslednjih N zahteva")
        print("7. Obriši logove")
        print("0. Exit")

        choice = input("> ")

        if choice == "1":
            print_all_logs()
        elif choice == "2":
            stats()
        elif choice == "3":
            stats_by_server()
        elif choice == "4":
            stats_by_router()
        elif choice == "5":
            ip = input("Enter IP: ")
            filter_by_ip(ip)
        elif choice == "6":
            n = int(input("N: "))
            last_n_logs(n)
        elif choice == "7":
            reset_logs()
        elif choice == "0":
            break
        else:
            print("Invalid option")