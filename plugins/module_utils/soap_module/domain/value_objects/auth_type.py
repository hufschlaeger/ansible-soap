from enum import Enum

class AuthType(Enum):
    """Unterstützte Authentifizierungstypen"""
    NONE = "none"
    BASIC = "basic"
    DIGEST = "digest"
    NTLM = "ntlm"
    CERTIFICATE = "certificate"
