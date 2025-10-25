"""
Domain Entity: SoapRequest
Repräsentiert einen SOAP-Request mit allen notwendigen Informationen.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict


@dataclass
class SoapRequest:
    """
    Entity für einen SOAP-Request.
    Hat eine eindeutige Identität und verwaltet den Lebenszyklus eines Requests.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    endpoint_url: str = field(default=None)
    soap_action: str = field(default=None)
    body: str = field(default=None)
    headers: Dict[str, str] = field(default_factory=dict)
    namespace: Optional[str] = None
    soap_version: str = field(default="1.1")  # "1.1" oder "1.2"
    timeout: int = field(default=30)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validierung nach Initialisierung"""
        if not self.endpoint_url:
            raise ValueError("endpoint_url ist erforderlich")

        if not self.body:
            raise ValueError("body ist erforderlich")

        if self.soap_version not in ["1.1", "1.2"]:
            raise ValueError("soap_version muss '1.1' oder '1.2' sein")

        if self.timeout <= 0:
            raise ValueError("timeout muss größer als 0 sein")

        self._ensure_soap_headers()

    def _ensure_soap_headers(self) -> None:
        """Stellt sicher, dass die notwendigen SOAP-Headers gesetzt sind"""
        if self.soap_version == "1.1":
            self.headers.setdefault("Content-Type", "text/xml; charset=utf-8")
            if self.soap_action:
                self.headers.setdefault("SOAPAction", f'"{self.soap_action}"')
        elif self.soap_version == "1.2":
            content_type = "application/soap+xml; charset=utf-8"
            if self.soap_action:
                content_type += f'; action="{self.soap_action}"'
            self.headers.setdefault("Content-Type", content_type)

    def add_header(self, key: str, value: str) -> None:
        """Fügt einen benutzerdefinierten Header hinzu"""
        if not key or not value:
            raise ValueError("Header key und value dürfen nicht leer sein")
        self.headers[key] = value

    def get_soap_envelope(self) -> str:
        """
        Gibt den kompletten SOAP-Envelope zurück.
        Falls body bereits ein vollständiger Envelope ist, wird er zurückgegeben.
        """
        # Prüfen ob Body bereits ein vollständiger SOAP Envelope ist
        if "<soap:Envelope" in self.body or "<SOAP-ENV:Envelope" in self.body:
            return self.body

        # Sonst Envelope aufbauen
        namespace_attr = f' xmlns:ns="{self.namespace}"' if self.namespace else ''

        if self.soap_version == "1.1":
            envelope = f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"{namespace_attr}>
    <soap:Body>
        {self.body}
    </soap:Body>
</soap:Envelope>'''
        else:  # SOAP 1.2
            envelope = f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"{namespace_attr}>
    <soap:Body>
        {self.body}
    </soap:Body>
</soap:Envelope>'''

        return envelope

    def __eq__(self, other) -> bool:
        """Gleichheit basierend auf ID"""
        if not isinstance(other, SoapRequest):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash basierend auf ID"""
        return hash(self.id)

    def __repr__(self) -> str:
        return (f"SoapRequest(id='{self.id}', endpoint='{self.endpoint_url}', "
                f"action='{self.soap_action}', version='{self.soap_version}')")
