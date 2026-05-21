import re
import socket
import ipaddress
from urllib.parse import urlparse
from typing import Optional


BLOCKED_HOSTS = {
    "localhost", "127.0.0.1", "0.0.0.0", "::1",
}

PRIVATE_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("::1/128"),
]


def _is_private_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        return any(ip in network for network in PRIVATE_RANGES)
    except ValueError:
        return False


def normalize_url(raw_url: str) -> tuple[str, Optional[str]]:
    """
    Returns (normalized_url, error_message).
    error_message is None if URL is valid.

    Security: resolves hostname to IP to prevent SSRF via DNS rebinding.
    """
    url = raw_url.strip()
    if not url:
        return "", "URL не может быть пустым"

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)
    except Exception:
        return "", "Некорректный формат URL"

    host = parsed.hostname
    if not host:
        return "", "Не удалось определить домен"

    if host in BLOCKED_HOSTS:
        return "", "Проверка локальных адресов недоступна"

    # Check if host is a literal IP address
    try:
        ipaddress.ip_address(host)
        # It's a literal IP — check if private
        if _is_private_ip(host):
            return "", "Проверка внутренних IP-адресов недоступна"
    except ValueError:
        # It's a domain name — resolve to IP and check
        domain_pattern = re.compile(
            r"^(?:[a-zA-Z0-9]"
            r"(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+"
            r"[a-zA-Z]{2,}$"
        )
        if not domain_pattern.match(host):
            return "", f"Некорректное доменное имя: {host}"

        # Resolve hostname → IP to prevent SSRF via DNS rebinding
        try:
            resolved_ip = socket.gethostbyname(host)
        except socket.gaierror:
            return "", f"Не удалось разрезолвить домен: {host}"

        if _is_private_ip(resolved_ip):
            return "", "Домен указывает на внутренний адрес — проверка недоступна"

    # Reconstruct clean URL
    clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path or '/'}"
    if parsed.query:
        clean += f"?{parsed.query}"

    return clean, None
