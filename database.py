import json
import time
import os

DB_FILE = "logs.json"


def create_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump([], f)


def save_data(client_ip, router_ip, router_name, server_id, result, time_ms):
    create_db()

    with open(DB_FILE, "r") as f:
        data = json.load(f)

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

    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)


def get_data():
    create_db()

    with open(DB_FILE, "r") as f:
        data = json.load(f)

    print("\n===== STATISTICS =====")

    if not data:
        print("No logs found")
        return

    total = len(data)
    online = len([d for d in data if d["status"] == "ONLINE"])
    offline = len([d for d in data if d["status"] == "OFFLINE"])

    avg_time = sum(d["time_ms"] for d in data) / total

    print(f"Total requests: {total}")
    print(f"ONLINE: {online}")
    print(f"OFFLINE: {offline}")
    print(f"Average response time: {round(avg_time, 2)} ms")

    print("======================\n")