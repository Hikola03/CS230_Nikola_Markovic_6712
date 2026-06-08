import socket
import json
import os

SERVER_HOST = "localhost"
LB_PORT = 5000

def load_routers():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "routers.json")
    with open(path, "r") as f:
        data = json.load(f)
    return data["routers"]


def show_routers(routers):
    print("\n===== ROUTERS =====")
    for r in routers:
        print(f"{r['id']}. {r['name']} - {r['ip']}")
    print("===================\n")


def send_request(router):
    try:
        port = LB_PORT

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((SERVER_HOST, port))

        data = {
            "router_ip": router["ip"],
            "router_name": router["name"]
        }

        client.send(json.dumps(data).encode("utf-8"))

        response_raw = client.recv(4096).decode("utf-8")
        response = json.loads(response_raw)

        client.close()
        return response

    except Exception as e:
        print("Error:", e)
        return None


def show_response(res):
    if not res:
        print("No response")
        return

    print("\n===== RESULT =====")

    if res["status"] == "ERROR":
        print("Error:", res["message"])
    else:
        icon = "ONLINE" if res["status"] == "ONLINE" else "OFFLINE"
        print(f"{icon} - {res['router_name']} ({res['router_ip']})")
        print(f"Response time: {res['time_ms']} ms")
        print(f"Server ID: {res['server_id']}")

    print("==================\n")


def main():
    routers = load_routers()

    while True:
        show_routers(routers)

        print(f"Select router (1-{len(routers)}) or 0 to exit:")
        choice = input("> ")

        if choice == "0":
            break

        if not choice.isdigit():
            print("Invalid input")
            continue

        choice = int(choice)

        if choice < 1 or choice > len(routers):
            print("Out of range")
            continue

        router = routers[choice - 1]

        print(f"Sending request for {router['name']}...")

        res = send_request(router)
        show_response(res)

        input("Press Enter to continue...")


if __name__ == "__main__":
    main()