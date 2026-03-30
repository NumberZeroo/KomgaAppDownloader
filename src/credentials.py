import os
import json
from cryptography.fernet import Fernet


def _get_cred_dir():
    try:
        from android.storage import app_storage_path  # type: ignore
        base = app_storage_path()
    except ImportError:
        base = os.path.expanduser("~")

    cred_dir = os.path.join(base, ".komgadownloader")
    os.makedirs(cred_dir, exist_ok=True)
    return cred_dir


def _get_paths():
    cred_dir = _get_cred_dir()
    return (
        cred_dir,
        os.path.join(cred_dir, "secret.key"),
        os.path.join(cred_dir, "credentials.enc"),
    )


def _load_key():
    cred_dir, key_path, _ = _get_paths()
    if not os.path.exists(key_path):
        key = Fernet.generate_key()
        with open(key_path, "wb") as key_file:
            key_file.write(key)
        return key
    with open(key_path, "rb") as key_file:
        return key_file.read()


def save_credentials(email, password, server_url):
    """Aggiunge o aggiorna un server nel database criptato."""
    _, _, cred_path = _get_paths()
    key = _load_key()
    f = Fernet(key)

    # Carichiamo i server esistenti
    data_dict = load_all_servers()

    # Aggiungiamo/Aggiorniamo il server (usiamo l'URL come chiave)
    data_dict[server_url] = {"email": email, "password": password}
    # Salviamo anche qual è l'ultimo server usato per il login automatico
    data_dict["_last_used"] = server_url

    encrypted_data = f.encrypt(json.dumps(data_dict).encode('utf-8'))
    with open(cred_path, "wb") as cred_file:
        cred_file.write(encrypted_data)


def load_all_servers():
    """Restituisce il dizionario completo dei server."""
    _, _, cred_path = _get_paths()
    if not os.path.exists(cred_path):
        return {}
    try:
        key = _load_key()
        f = Fernet(key)
        with open(cred_path, "rb") as cred_file:
            decrypted = f.decrypt(cred_file.read()).decode('utf-8')
        return json.loads(decrypted)
    except:
        return {}


def load_credentials():
    """Recupera l'ultimo server usato per il login automatico."""
    all_data = load_all_servers()
    last_url = all_data.get("_last_used")
    if last_url and last_url in all_data:
        creds = all_data[last_url]
        return creds["email"], creds["password"], last_url
    return None, None, None


def delete_credentials():
    _, _, cred_path = _get_paths()
    if os.path.exists(cred_path):
        os.remove(cred_path)