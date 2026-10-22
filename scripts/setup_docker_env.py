"""Generate private Docker credentials without overwriting an existing file."""
from pathlib import Path
import secrets


if __name__ == "__main__":
    target = Path(__file__).resolve().parents[1] / ".env.docker"
    values = {key: secrets.token_hex(24) for key in (
        "MYSQL_PASSWORD", "MYSQL_ROOT_PASSWORD", "JWT_SECRET", "DEMO_PASSWORD"
    )}
    try:
        with target.open("x", encoding="utf-8") as file:
            file.write("".join(f"{key}={value}\n" for key, value in values.items()))
    except FileExistsError:
        raise SystemExit(".env.docker sudah ada; konfigurasi tidak ditimpa.")
    print(".env.docker dibuat. Lihat DEMO_PASSWORD di file lokal untuk login.")
