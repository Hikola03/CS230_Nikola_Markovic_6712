import os
import json
import time
import base64
import hashlib
from database import save_log

# ==============================================================
#  KONFIGURACIJA
# ==============================================================
STORAGE_DIR = "storage"          # folder gde se čuvaju enkriptovani fajlovi
ENCRYPTION_KEY = "CS230SecretKey"  # AES ključ (u produkciji bio bi u env varijabli)


# ==============================================================
#  ENKRICIJA / DEKRIPCIJA  (XOR + Base64)
#  Napomena: u produkciji koristiti cryptography.fernet ili AES
# ==============================================================
def _derive_key(secret: str) -> bytes:
    """Izvodi 32-bajtni ključ iz stringa pomoću SHA-256."""
    return hashlib.sha256(secret.encode()).digest()


def encrypt_data(plaintext: bytes) -> str:
    """
    Enkriptuje bajte XOR algoritmom sa izvedenim ključem i
    enkoduje rezultat u Base64 string za čuvanje na disku.
    """
    key = _derive_key(ENCRYPTION_KEY)
    encrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(plaintext)])
    return base64.b64encode(encrypted).decode("utf-8")


def decrypt_data(encoded: str) -> bytes:
    """Dekriptuje Base64+XOR podatke natrag u originalne bajte."""
    key = _derive_key(ENCRYPTION_KEY)
    encrypted = base64.b64decode(encoded.encode("utf-8"))
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(encrypted)])


# ==============================================================
#  KONTROLA PRISTUPA
# ==============================================================
USERS_FILE = "users.json"

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)["users"]


def authenticate(username: str, password: str):
    """
    Proverava kredencijale korisnika.
    Vraća korisnika (dict) ako su ispravni, None ako nisu.
    """
    for user in load_users():
        if user["username"] == username and user["password"] == password:
            return user
    return None


def authorize(user: dict, action: str) -> bool:
    """
    Proverava da li korisnik ima pravo da izvrši akciju.
    admin → sve operacije
    user  → upload, download, list (ne može delete tuđih fajlova)
    """
    if user["role"] == "admin":
        return True
    allowed = {"upload", "download", "list"}
    return action in allowed


# ==============================================================
#  OPERACIJE NAD FAJLOVIMA
# ==============================================================
def ensure_storage():
    os.makedirs(STORAGE_DIR, exist_ok=True)


def handle_upload(data: dict, server_id: int, client_ip: str) -> dict:
    """Prima fajl od klijenta, enkriptuje ga i čuva na disk."""
    ensure_storage()

    username  = data.get("username")
    filename  = data.get("filename")
    file_b64  = data.get("file_data")   # klijent šalje fajl kao Base64

    if not filename or not file_b64:
        return {"status": "ERROR", "message": "Missing filename or file_data"}

    # sanitizacija imena fajla
    filename = os.path.basename(filename)

    raw_bytes  = base64.b64decode(file_b64)
    encrypted  = encrypt_data(raw_bytes)

    save_path = os.path.join(STORAGE_DIR, filename + ".enc")

    with open(save_path, "w") as f:
        f.write(encrypted)

    size_kb = round(len(raw_bytes) / 1024, 2)

    save_log(client_ip, username, server_id, "upload", filename, "SUCCESS", size_kb)

    return {
        "status": "SUCCESS",
        "action": "upload",
        "filename": filename,
        "size_kb": size_kb,
        "server_id": server_id
    }


def handle_download(data: dict, server_id: int, client_ip: str) -> dict:
    """Čita enkriptovani fajl sa diska, dekriptuje ga i šalje klijentu."""
    ensure_storage()

    username = data.get("username")
    filename = os.path.basename(data.get("filename", ""))

    save_path = os.path.join(STORAGE_DIR, filename + ".enc")

    if not os.path.exists(save_path):
        save_log(client_ip, username, server_id, "download", filename, "NOT_FOUND", 0)
        return {"status": "ERROR", "message": "File not found"}

    with open(save_path, "r") as f:
        encrypted = f.read()

    raw_bytes = decrypt_data(encrypted)
    file_b64  = base64.b64encode(raw_bytes).decode("utf-8")

    size_kb = round(len(raw_bytes) / 1024, 2)

    save_log(client_ip, username, server_id, "download", filename, "SUCCESS", size_kb)

    return {
        "status": "SUCCESS",
        "action": "download",
        "filename": filename,
        "file_data": file_b64,
        "size_kb": size_kb,
        "server_id": server_id
    }


def handle_list(data: dict, server_id: int, client_ip: str) -> dict:
    """Vraća listu svih fajlova u storage folderu."""
    ensure_storage()

    username = data.get("username")

    files = []
    for f in os.listdir(STORAGE_DIR):
        if f.endswith(".enc"):
            full_path = os.path.join(STORAGE_DIR, f)
            size_kb   = round(os.path.getsize(full_path) / 1024, 2)
            files.append({"name": f.replace(".enc", ""), "size_kb": size_kb})

    save_log(client_ip, username, server_id, "list", "-", "SUCCESS", 0)

    return {
        "status": "SUCCESS",
        "action": "list",
        "files": files,
        "server_id": server_id
    }


def handle_delete(data: dict, server_id: int, client_ip: str) -> dict:
    """Briše fajl sa diska (samo admin)."""
    ensure_storage()

    username = data.get("username")
    filename = os.path.basename(data.get("filename", ""))
    save_path = os.path.join(STORAGE_DIR, filename + ".enc")

    if not os.path.exists(save_path):
        save_log(client_ip, username, server_id, "delete", filename, "NOT_FOUND", 0)
        return {"status": "ERROR", "message": "File not found"}

    os.remove(save_path)

    save_log(client_ip, username, server_id, "delete", filename, "SUCCESS", 0)

    return {
        "status": "SUCCESS",
        "action": "delete",
        "filename": filename,
        "server_id": server_id
    }


# ==============================================================
#  GLAVNA ULAZNA TAČKA  (poziva je server.py)
# ==============================================================
def execute_request(data: dict, server_id: int, client_ip: str) -> dict:
    """
    Autentifikacija → autorizacija → izvršavanje akcije.
    data mora sadržati: username, password, action + ostala polja po akciji.
    """
    username = data.get("username")
    password = data.get("password")
    action   = data.get("action")

    # 1. autentifikacija
    user = authenticate(username, password)
    if not user:
        save_log(client_ip, username or "unknown", server_id,
                 action or "unknown", "-", "AUTH_FAILED", 0)
        return {"status": "ERROR", "message": "Invalid credentials"}

    # 2. autorizacija
    if not authorize(user, action):
        save_log(client_ip, username, server_id,
                 action, "-", "FORBIDDEN", 0)
        return {"status": "ERROR", "message": "Access denied – insufficient privileges"}

    # 3. izvršavanje
    if action == "upload":
        return handle_upload(data, server_id, client_ip)
    elif action == "download":
        return handle_download(data, server_id, client_ip)
    elif action == "list":
        return handle_list(data, server_id, client_ip)
    elif action == "delete":
        return handle_delete(data, server_id, client_ip)
    else:
        return {"status": "ERROR", "message": f"Unknown action: {action}"}