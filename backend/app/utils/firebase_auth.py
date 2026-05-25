import time
from email.utils import parsedate_to_datetime

import jwt
import requests

FIREBASE_CERTS_URL = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"

_certs = None
_certs_expires_at = 0


def _cache_max_age(cache_control):
    for part in cache_control.split(","):
        part = part.strip()
        if part.startswith("max-age="):
            try:
                return int(part.split("=", 1)[1])
            except ValueError:
                return 300
    return 300


def _load_certs():
    global _certs, _certs_expires_at

    now = time.time()
    if _certs and now < _certs_expires_at:
        return _certs

    response = requests.get(FIREBASE_CERTS_URL, timeout=10)
    response.raise_for_status()

    max_age = _cache_max_age(response.headers.get("Cache-Control", ""))
    expires = response.headers.get("Expires")
    if expires:
        try:
            _certs_expires_at = parsedate_to_datetime(expires).timestamp()
        except (TypeError, ValueError, IndexError):
            _certs_expires_at = now + max_age
    else:
        _certs_expires_at = now + max_age

    _certs = response.json()
    return _certs


def verify_firebase_id_token(id_token, project_id):
    if not project_id:
        raise ValueError("FIREBASE_PROJECT_ID is not configured")

    header = jwt.get_unverified_header(id_token)
    key_id = header.get("kid")
    certs = _load_certs()
    cert = certs.get(key_id)
    if not cert:
        raise ValueError("Firebase token uses an unknown signing key")

    issuer = f"https://securetoken.google.com/{project_id}"
    return jwt.decode(
        id_token,
        cert,
        algorithms=["RS256"],
        audience=project_id,
        issuer=issuer,
    )
