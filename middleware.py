import time
import socket


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
    try:
        socket.setdefaulttimeout(1)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, 80))
        s.close()

        return "ONLINE"
    except:
        return "OFFLINE"


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

    return {
        "status": status,
        "router_ip": router_ip,
        "router_name": router_name,
        "time_ms": round((end - start) * 1000, 2),
        "server_id": server_id
    }