import os
import time
import httpx
import qrcode

WAHA_URL = os.getenv("WAHA_URL", "http://waha:3000")
WAHA_API_KEY = os.getenv("WAHA_API_KEY", "")
SESSION = "default"
HEADERS = {"X-Api-Key": WAHA_API_KEY}


def wait_for_waha(timeout=60):
    """Fica tentando até o WAHA responder (ele demora alguns segundos para subir)."""
    print("Aguardando WAHA iniciar...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get(f"{WAHA_URL}/ping", timeout=3)
            if r.status_code == 200:
                print("WAHA está no ar.")
                return
        except httpx.RequestError:
            pass
        time.sleep(2)
    raise TimeoutError("WAHA não respondeu em tempo hábil. Verifique se o container subiu.")


def get_session_status():
    try:
        r = httpx.get(f"{WAHA_URL}/api/sessions/{SESSION}", headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return r.json().get("status")
        return None  # sessão não existe
    except httpx.RequestError:
        return None


def create_session():
    httpx.post(
        f"{WAHA_URL}/api/sessions",
        headers=HEADERS,
        json={"name": SESSION},
        timeout=5,
    )


def start_session():
    httpx.post(f"{WAHA_URL}/api/sessions/{SESSION}/start", headers=HEADERS, timeout=5)


def show_qr():
    """Busca o QR code em formato raw e renderiza no terminal."""
    deadline = time.time() + 60  # QR expira em ~60s
    while time.time() < deadline:
        try:
            r = httpx.get(
                f"{WAHA_URL}/api/{SESSION}/auth/qr",
                headers=HEADERS,
                params={"format": "raw"},
                timeout=5,
            )
            if r.status_code == 200:
                raw = r.json().get("value") or r.text.strip()
                qr = qrcode.QRCode()
                qr.add_data(raw)
                qr.make(fit=True)
                print("\nEscaneie o QR code abaixo com o WhatsApp:\n")
                qr.print_ascii(invert=True)
                return
        except httpx.RequestError:
            pass
        time.sleep(2)
    print("Não foi possível obter o QR code.")


def wait_for_working(timeout=120):
    """Fica em loop até a sessão estar WORKING."""
    print("Aguardando autenticação do WhatsApp...")
    deadline = time.time() + timeout
    last_status = None
    while time.time() < deadline:
        status = get_session_status()
        if status != last_status:
            print(f"  Status: {status}")
            last_status = status
        if status == "WORKING":
            print("WhatsApp conectado com sucesso!")
            return
        if status == "SCAN_QR_CODE":
            show_qr()
        time.sleep(3)
    raise TimeoutError("Autenticação não concluída a tempo.")


def ensure_connected():
    wait_for_waha()

    status = get_session_status()

    if status is None:
        print("Sessão não encontrada. Criando...")
        create_session()
        time.sleep(1)
        status = get_session_status()

    if status in ("STOPPED", "FAILED", None):
        print(f"Sessão com status '{status}'. Iniciando...")
        start_session()

    if status == "WORKING":
        print("Sessão já está conectada.")
        return

    wait_for_working()
