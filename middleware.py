import time
import socket
import subprocess
from database import save_data


def validate_ip(ip):
    parts = ip.split(".")
    if len(parts) != 4:
        return False

    for p in parts:
        if not p.isdigit():
            return False
        if int(p) < 0 or int(p) > 255:
            return False

    return True


def ping_router(ip):
    result = subprocess.run(
        ["ping", "-n", "1", "-w", "1000", ip],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return "ONLINE" if result.returncode == 0 else "OFFLINE"


def execute_request(data, server_id, client_ip):
    router_ip = data.get("router_ip")
    router_name = data.get("router_name")

    if not validate_ip(router_ip):
        return {
            "status": "ERROR",
            "message": "Invalid IP address",
            "server_id": server_id
        }

    start = time.time()
    status = ping_router(router_ip)
    end = time.time()

    time_ms = round((end - start) * 1000, 2)

    save_data(client_ip, router_ip, router_name, server_id, status, time_ms)

    return {
        "status": status,
        "router_ip": router_ip,
        "router_name": router_name,
        "time_ms": time_ms,
        "server_id": server_id
    }