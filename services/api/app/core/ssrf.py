import socket
import ipaddress
from urllib.parse import urlparse
from typing import Tuple

BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),      # IPv4 Loopback
    ipaddress.ip_network("::1/128"),          # IPv6 Loopback
    ipaddress.ip_network("10.0.0.0/8"),       # RFC1918 Private
    ipaddress.ip_network("172.16.0.0/12"),    # RFC1918 Private
    ipaddress.ip_network("192.168.0.0/16"),   # RFC1918 Private
    ipaddress.ip_network("169.254.0.0/16"),   # Link-local / Cloud metadata (AWS/GCP/Azure)
    ipaddress.ip_network("fe80::/10"),        # IPv6 Link-local
    ipaddress.ip_network("224.0.0.0/4"),      # Multicast
    ipaddress.ip_network("0.0.0.0/8"),        # This-network
]

def is_ip_blocked(ip_addr_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_addr_str)
        for net in BLOCKED_IP_NETWORKS:
            if ip in net:
                return True
        return False
    except ValueError:
        return True

def validate_target_url(url: str, allow_private_dev: bool = False) -> Tuple[bool, str]:
    if not url:
        return False, "URL is required"

    parsed = urlparse(url)
    if parsed.scheme not in ["http", "https"]:
        return False, f"Unsupported scheme '{parsed.scheme}'. Only HTTP and HTTPS are permitted."

    hostname = parsed.hostname
    if not hostname:
        return False, "Invalid host in URL"

    if hostname.lower() in ["localhost", "127.0.0.1", "0.0.0.0", "::1"] and not allow_private_dev:
        return False, "Access to localhost or loopback addresses is prohibited for security."

    # Cloud metadata endpoints explicitly blocked
    if hostname in ["169.254.169.254", "metadata.google.internal"]:
        return False, "Access to cloud instance metadata service is prohibited."

    # Resolve IP address to detect DNS rebinding or private intranet addressing
    try:
        addr_info = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
        for res in addr_info:
            ip_str = res[4][0]
            if not allow_private_dev and is_ip_blocked(ip_str):
                return False, f"Target hostname resolved to private or restricted network address ({ip_str})."
    except socket.gaierror:
        return False, f"Failed to resolve hostname: {hostname}"

    return True, "Valid"
