"""
Value Object: SoapEnvelope
Spezialisiertes Value Object für komplette SOAP Envelopes.
"""
from dataclasses import dataclass
from typing import Optional, Dict
from enum import Enum


class SoapVersion(Enum):
    """SOAP Version Enumeration"""
    V1_1 = "1.1"
    V1_2 = "1.2"

    @property
    def namespace(self) -> str:
        """Gibt den Namespace für die SOAP-Version zurück"""
        if self == SoapVersion.V1_1:
            return "http://schemas.xmlsoap.org/soap/envelope/"
        return "http://www.w3.org/2003/05/soap-envelope"

    @property
    def prefix(self) -> str:
        """Standard-Prefix für die SOAP-Version"""
        return "soap"


@dataclass(frozen=True)
class SoapEnvelope:
    """
    Immutable Value Object für einen kompletten SOAP Envelope.
    Wrapper um XmlBody mit SOAP-spezifischer Logik.
    """

    body_content: str  # Der Inhalt innerhalb von <soap:Body>
    version: SoapVersion = SoapVersion.V1_1
    header_content: Optional[str] = None
    namespace_declarations: Optional[Dict[str, str]] = None

    def __post_init__(self):
        """Validierung bei Erstellung"""
        if not self.body_content:
            raise ValueError("Body-Content darf nicht leer sein")

        # Body-Content sollte valides XML sein
        from xml.etree.ElementTree import fromstring, ParseError
        try:
            fromstring(self.body_content)
        except ParseError as e:
            raise ValueError(f"Body-Content ist kein valides XML: {e}")

        # Header validieren falls vorhanden
        if self.header_content:
            try:
                fromstring(self.header_content)
            except ParseError as e:
                raise ValueError(f"Header-Content ist kein valides XML: {e}")

    @classmethod
    def from_body(cls, body_content: str, version: SoapVersion = SoapVersion.V1_1,
                  namespace_declarations: Optional[Dict[str, str]] = None) -> 'SoapEnvelope':
        """Factory-Methode zum Erstellen aus Body-Content"""
        return cls(
            body_content=body_content,
            version=version,
            namespace_declarations=namespace_declarations
        )

    def build(self) -> str:
        """Baut den kompletten SOAP Envelope"""
        # Namespace-Deklarationen sammeln
        ns_declarations = [f'xmlns:{self.version.prefix}="{self.version.namespace}"']

        if self.namespace_declarations:
            for prefix, uri in self.namespace_declarations.items():
                ns_declarations.append(f'xmlns:{prefix}="{uri}"')

        ns_string = ' '.join(ns_declarations)

        # Envelope aufbauen
        parts = [f'<?xml version="1.0" encoding="utf-8"?>']
        parts.append(f'<{self.version.prefix}:Envelope {ns_string}>')

        # Optional: Header
        if self.header_content:
            parts.append(f'<{self.version.prefix}:Header>')
            parts.append(self.header_content)
            parts.append(f'</{self.version.prefix}:Header>')

        # Body
        parts.append(f'<{self.version.prefix}:Body>')
        parts.append(self.body_content)
        parts.append(f'</{self.version.prefix}:Body>')

        parts.append(f'</{self.version.prefix}:Envelope>')

        return '\n'.join(parts)

    def with_header(self, header_content: str) -> 'SoapEnvelope':
        """Gibt einen neuen Envelope mit Header zurück"""
        return SoapEnvelope(
            body_content=self.body_content,
            version=self.version,
            header_content=header_content,
            namespace_declarations=self.namespace_declarations
        )

    def with_namespace(self, prefix: str, uri: str) -> 'SoapEnvelope':
        """Fügt eine Namespace-Deklaration hinzu"""
        ns_decl = dict(self.namespace_declarations) if self.namespace_declarations else {}
        ns_decl[prefix] = uri

        return SoapEnvelope(
            body_content=self.body_content,
            version=self.version,
            header_content=self.header_content,
            namespace_declarations=ns_decl
        )

    def __str__(self) -> str:
        return self.build()

    def __eq__(self, other) -> bool:
        if not isinstance(other, SoapEnvelope):
            return False
        return (self.body_content == other.body_content and
                self.version == other.version and
                self.header_content == other.header_content and
                self.namespace_declarations == other.namespace_declarations)

    def __hash__(self) -> int:
        ns_tuple = tuple(sorted(self.namespace_declarations.items())) if self.namespace_declarations else ()
        return hash((self.body_content, self.version, self.header_content, ns_tuple))
