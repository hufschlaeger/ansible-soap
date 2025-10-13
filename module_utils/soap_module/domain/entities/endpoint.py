"""
Domain Entity: Endpoint
Repräsentiert einen SOAP-Endpunkt mit seinen Eigenschaften.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from urllib.parse import urlparse


@dataclass
class Endpoint:
    """
    Entity für einen SOAP-Endpunkt.
    Kapselt URL, Authentifizierung und Endpunkt-spezifische Konfiguration.
    """

    url: str
    name: Optional[str] = None
    description: Optional[str] = None

    # Authentifizierung
    auth_type: Optional[str] = None  # "basic", "digest", "ntlm", "certificate"
    username: Optional[str] = None
    password: Optional[str] = None
    cert_path: Optional[str] = None
    key_path: Optional[str] = None

    # SSL/TLS
    verify_ssl: bool = True
    ca_bundle_path: Optional[str] = None

    # Proxy
    proxy_url: Optional[str] = None

    # Standard-Einstellungen für Requests an diesen Endpoint
    default_timeout: int = 30
    default_soap_version: str = "1.1"
    default_headers: Dict[str, str] = field(default_factory=dict)

    # Capabilities / Metadata
    supported_operations: List[str] = field(default_factory=list)
    wsdl_url: Optional[str] = None

    def __post_init__(self):
        """Validierung nach Initialisierung"""
        if not self.url:
            raise ValueError("url ist erforderlich")

        # URL validieren
        parsed = urlparse(self.url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Ungültige URL: {self.url}")

        if parsed.scheme not in ["http", "https"]:
            raise ValueError(f"URL muss http oder https verwenden: {self.url}")

        # Auth-Validierung
        if self.auth_type:
            if self.auth_type not in ["basic", "digest", "ntlm", "certificate"]:
                raise ValueError(f"Ungültiger auth_type: {self.auth_type}")

            if self.auth_type in ["basic", "digest", "ntlm"]:
                if not self.username or not self.password:
                    raise ValueError(f"{self.auth_type} Auth benötigt username und password")

            if self.auth_type == "certificate":
                if not self.cert_path:
                    raise ValueError("certificate Auth benötigt cert_path")

        # Timeout validieren
        if self.default_timeout <= 0:
            raise ValueError("default_timeout muss größer als 0 sein")

        # SOAP Version validieren
        if self.default_soap_version not in ["1.1", "1.2"]:
            raise ValueError("default_soap_version muss '1.1' oder '1.2' sein")

        # Name generieren falls nicht vorhanden
        if not self.name:
            self.name = self._generate_name_from_url()

    def _generate_name_from_url(self) -> str:
        """Generiert einen Namen aus der URL"""
        parsed = urlparse(self.url)
        return f"{parsed.netloc}{parsed.path}".replace("/", "_").strip("_")

    def get_base_url(self) -> str:
        """Gibt die Basis-URL zurück (ohne Query-Parameter)"""
        parsed = urlparse(self.url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    def requires_auth(self) -> bool:
        """Prüft ob Authentifizierung erforderlich ist"""
        return self.auth_type is not None

    def get_auth_config(self) -> Optional[Dict[str, str]]:
        """Gibt die Auth-Konfiguration zurück"""
        if not self.requires_auth():
            return None

        config = {"type": self.auth_type}

        if self.auth_type in ["basic", "digest", "ntlm"]:
            config["username"] = self.username
            config["password"] = self.password
        elif self.auth_type == "certificate":
            config["cert_path"] = self.cert_path
            if self.key_path:
                config["key_path"] = self.key_path

        return config

    def supports_operation(self, operation: str) -> bool:
        """Prüft ob eine Operation unterstützt wird"""
        if not self.supported_operations:
            return True  # Wenn keine Operationen definiert, alle erlauben
        return operation in self.supported_operations

    def __repr__(self) -> str:
        return f"Endpoint(name='{self.name}', url='{self.url}', auth={self.auth_type})"
