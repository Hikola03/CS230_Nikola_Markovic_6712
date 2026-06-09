import socket
import json
import os
import base64

SERVER_HOST = "localhost"
LB_PORT = 5000

# korisnik koji je ulogovan u ovoj sesiji
current_user = {"username": None, "password": None, "role": None}


# ==============================================================
#  KOMUNIKACIJA SA SERVEROM
# ==============================================================
def send_request(payload: dict) -> dict | None:
    """Šalje JSON payload load balanceru i vraća odgovor."""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((SERVER_HOST, LB_PORT))
        client.send(json.dumps(payload).encode("utf-8"))

        response_raw = client.recv(1024 * 1024).decode("utf-8")  # 1MB buffer
        client.close()
        return json.loads(response_raw)
    except Exception as e:
        print(f"Connection error: {e}")
        return None


# ==============================================================
#  LOGIN
# ==============================================================
def login() -> bool:
    """Traži od korisnika kredencijale i verifikuje ih putem servera."""
    ART = [
        "                     .--.  .--.",
        "                    /    \\/    \\",
        "                   | .-.  .-.   \\",
        "                   |/_  |/_  |   \\",
        "                   || `\\|| `\\|    `----.",
        "                   |\\0_/ \\0_/    --,    \\_",
        " .--\"\"\"\"\"-.       /              (` \\     `-.",
        "/          \\-----'-.              \\          \\",
        "\\  () ()                         /`\\          \\",
        "|                         .___.-'   |          \\",
        "\\                        /` \\|      /           ;",
        " `-.___             ___.' .-.`.---.|             \\",
        "    \\| ``-..___,.-'`\\| / /   /     |              `\\",
        "     `      \\|      ,`/ /   /   ,  /",
        "             `      |\\ /   /    |\\/",
        "              ,   .'`-;   '     \\/",
        "         ,    |\\-'  .'   ,   .-'`",
        "       .-|\\--;`` .-'     |\\.'",
        "      ( `\"'-.|\\ (___,.--'`'   ",
        "       `-.    `\"`          _.--'",
        "          `.          _.-'`-.",
        "            `''---''``       `.",
    ]
    for line in ART:
        print(line)
    print("\n===== LOGIN =====")
    username = input("Username: ").strip()
    password = input("Password: ").strip()

    # šaljemo list zahtev samo da proverimo kredencijale
    res = send_request({
        "username": username,
        "password": password,
        "action": "list"
    })

    if res and res.get("status") == "SUCCESS":
        current_user["username"] = username
        current_user["password"] = password
        print(f"\nDobrodošli, {username}!")
        return True
    else:
        msg = res.get("message", "Login failed") if res else "Server unreachable"
        print(f"Login failed: {msg}")
        return False


# ==============================================================
#  OPERACIJE
# ==============================================================
def do_list():
    res = send_request({
        "username": current_user["username"],
        "password": current_user["password"],
        "action": "list"
    })

    if not res or res.get("status") != "SUCCESS":
        print("Error:", res.get("message") if res else "No response")
        return

    files = res.get("files", [])
    print(f"\n===== FILES ON SERVER (via server {res.get('server_id')}) =====")
    if not files:
        print("  (no files)")
    else:
        for f in files:
            print(f"  {f['name']}  [{f['size_kb']} KB]")
    print("=" * 50)


def do_upload():
    path = input("Local file path: ").strip()

    if not os.path.exists(path):
        print("File not found.")
        return

    filename = os.path.basename(path)

    with open(path, "rb") as f:
        file_b64 = base64.b64encode(f.read()).decode("utf-8")

    print(f"Uploading {filename}...")

    res = send_request({
        "username": current_user["username"],
        "password": current_user["password"],
        "action": "upload",
        "filename": filename,
        "file_data": file_b64
    })

    if not res:
        print("No response from server.")
        return

    if res.get("status") == "SUCCESS":
        print(f"Upload successful! Size: {res.get('size_kb')} KB | Server: {res.get('server_id')}")
    else:
        print(f"Error: {res.get('message')}")


def do_download():
    do_list()
    filename = input("Filename to download: ").strip()

    save_path = input(f"Save as (default: {filename}): ").strip() or filename

    res = send_request({
        "username": current_user["username"],
        "password": current_user["password"],
        "action": "download",
        "filename": filename
    })

    if not res:
        print("No response from server.")
        return

    if res.get("status") == "SUCCESS":
        raw = base64.b64decode(res["file_data"])
        with open(save_path, "wb") as f:
            f.write(raw)
        print(f"Downloaded {filename} → {save_path} ({res.get('size_kb')} KB) | Server: {res.get('server_id')}")
    else:
        print(f"Error: {res.get('message')}")


def do_delete():
    do_list()
    filename = input("Filename to delete: ").strip()

    confirm = input(f"Are you sure you want to delete '{filename}'? (yes/no): ").strip()
    if confirm.lower() != "yes":
        print("Cancelled.")
        return

    res = send_request({
        "username": current_user["username"],
        "password": current_user["password"],
        "action": "delete",
        "filename": filename
    })

    if not res:
        print("No response from server.")
        return

    if res.get("status") == "SUCCESS":
        print(f"File '{filename}' deleted. | Server: {res.get('server_id')}")
    else:
        print(f"Error: {res.get('message')}")


# ==============================================================
#  GLAVNI MENI
# ==============================================================
def main():
    if not login():
        return

    while True:
        print("\n===== FILE STORAGE =====")
        print(f"Logged in as: {current_user['username']}")
        print("1. List files")
        print("2. Upload file")
        print("3. Download file")
        print("4. Delete file  (admin only)")
        print("0. Logout")
        print("========================")

        choice = input("> ").strip()

        if choice == "0":
            print("Goodbye!")
            break
        elif choice == "1":
            do_list()
        elif choice == "2":
            do_upload()
        elif choice == "3":
            do_download()
        elif choice == "4":
            do_delete()
        else:
            print("Invalid option")


if __name__ == "__main__":
    main()