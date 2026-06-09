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


def save_log(client_ip, username, server_id, action, filename, result, size_kb):
    data = read_logs()

    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "client_ip": client_ip,
        "username": username,
        "server_id": server_id,
        "action": action,
        "filename": filename,
        "result": result,
        "size_kb": size_kb
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
        ts  = d.get("timestamp", "-")
        usr = d.get("username", "-")
        act = d.get("action", "-")
        fn  = d.get("filename", "-")
        res = d.get("result", "-")
        sid = d.get("server_id", "-")
        print(f"[{ts}] {usr} | {act} | {fn} | {res} | server:{sid}")
    print("====================\n")


def filter_by_user(username):
    data = read_logs()
    found = False
    print(f"\n===== LOGS FOR USER: {username} =====")
    for d in data:
        if d.get("username") == username:
            print(d)
            found = True
    if not found:
        print("No logs for this user")
    print("=====================================\n")


def filter_by_action(action):
    data = read_logs()
    found = False
    print(f"\n===== LOGS FOR ACTION: {action} =====")
    for d in data:
        if d.get("action") == action:
            print(d)
            found = True
    if not found:
        print("No logs for this action")
    print("=====================================\n")


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

    total   = len(data)
    success = len([d for d in data if d.get("result") == "SUCCESS"])
    failed  = total - success

    uploads   = len([d for d in data if d.get("action") == "upload"])
    downloads = len([d for d in data if d.get("action") == "download"])
    deletes   = len([d for d in data if d.get("action") == "delete"])
    lists     = len([d for d in data if d.get("action") == "list"])

    total_kb = sum(d.get("size_kb", 0) for d in data)

    print("\n===== STATISTICS =====")
    print(f"Total operations : {total}")
    print(f"Successful       : {success}")
    print(f"Failed           : {failed}")
    print(f"Uploads          : {uploads}")
    print(f"Downloads        : {downloads}")
    print(f"Deletes          : {deletes}")
    print(f"List requests    : {lists}")
    print(f"Total data (KB)  : {round(total_kb, 2)}")
    print("======================\n")


def stats_by_server():
    data = read_logs()
    result = {}
    for d in data:
        sid = d.get("server_id")
        result.setdefault(sid, 0)
        result[sid] += 1

    print("\n===== REQUESTS BY SERVER =====")
    for k, v in result.items():
        print(f"Server {k}: {v} requests")
    print("==============================\n")


def stats_by_user():
    data = read_logs()
    result = {}
    for d in data:
        usr = d.get("username", "unknown")
        result.setdefault(usr, 0)
        result[usr] += 1

    print("\n===== REQUESTS BY USER =====")
    for k, v in result.items():
        print(f"{k}: {v} requests")
    print("============================\n")


# ======================
# ADMIN MENU
# ======================

def admin_menu():
    while True:
        print("\n===== ADMIN PANEL =====")
        print("1. Prikaži sve logove")
        print("2. Statistika (globalna)")
        print("3. Statistika po serveru")
        print("4. Statistika po korisniku")
        print("5. Filtriraj po korisniku")
        print("6. Filtriraj po akciji (upload/download/delete/list)")
        print("7. Poslednjih N zahteva")
        print("8. Obriši logove")
        print("0. Exit")

        choice = input("> ")

        if choice == "1":
            print_all_logs()
        elif choice == "2":
            stats()
        elif choice == "3":
            stats_by_server()
        elif choice == "4":
            stats_by_user()
        elif choice == "5":
            usr = input("Username: ")
            filter_by_user(usr)
        elif choice == "6":
            act = input("Action (upload/download/delete/list): ")
            filter_by_action(act)
        elif choice == "7":
            n = int(input("N: "))
            last_n_logs(n)
        elif choice == "8":
            reset_logs()
        elif choice == "0":
            break
        else:
            print("Invalid option")