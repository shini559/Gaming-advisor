import hashlib
import time
from uuid import uuid4
from fastapi import Request


def generate_session_identifier(request: Request) -> str:
    """Générer un identifiant unique pour la session"""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")[:100]  # Limiter la taille
    timestamp = f"{time.time():.6f}"  # Microsecondes pour l'unicité
    random_part = str(uuid4())[:8]

    # Hash court mais unique
    raw_data = f"{client_ip}:{user_agent}:{timestamp}:{random_part}"
    return hashlib.md5(raw_data.encode()).hexdigest()[:12]