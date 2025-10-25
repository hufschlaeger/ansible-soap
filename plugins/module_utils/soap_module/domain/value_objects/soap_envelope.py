"""
Value Object: SoapEnvelope
Spezialisiertes Value Object für komplette SOAP Envelopes.
"""
from dataclasses import dataclass
from typing import Optional, Dict
from enum import Enum
import xml.etree.ElementTree as ET

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
    namespace_prefix: Optional[str] = None  # ← NEU! Custom Prefix für Body-Content

    def __post_init__(self):
        """Validierung bei Erstellung"""
        if not self.body_content:
            raise ValueError("Body-Content darf nicht leer sein")

        # Body-Content sollte valides XML sein
        try:
            ET.fromstring(self.body_content)
        except ET.ParseError as e:
            raise ValueError(f"Body-Content ist kein valides XML: {e}")

        # Header validieren falls vorhanden
        if self.header_content:
            try:
                ET.fromstring(self.header_content)
            except ET.ParseError as e:
                raise ValueError(f"Header-Content ist kein valides XML: {e}")

    @classmethod
    def from_body(
            cls,
            body_content: str,
            version: SoapVersion = SoapVersion.V1_1,
            namespace_declarations: Optional[Dict[str, str]] = None,
            namespace_prefix: Optional[str] = None  # ← NEU!
    ) -> 'SoapEnvelope':
        """
        Factory-Methode zum Erstellen aus Body-Content

        Args:
            body_content: Der XML-Inhalt für den SOAP Body
            version: SOAP Version (1.1 oder 1.2)
            namespace_declarations: Zusätzliche Namespace-Deklarationen
            namespace_prefix: Optional Prefix für den Body-Content (z.B. 'web')
        """
        return cls(
            body_content=body_content,
            version=version,
            namespace_declarations=namespace_declarations,
            namespace_prefix=namespace_prefix
        )

    def build(self) -> str:
        """
        Baut den kompletten SOAP Envelope mit ElementTree.
        Berücksichtigt dabei den namespace_prefix falls vorhanden.
        """

        # SOAP Envelope Namespace
        soap_ns = self.version.namespace
        ET.register_namespace('soap', soap_ns)

        # Zusätzliche Namespaces registrieren
        if self.namespace_declarations:
            for prefix, uri in self.namespace_declarations.items():
                ET.register_namespace(prefix if prefix else '', uri)

        # Falls namespace_prefix angegeben, auch diesen registrieren
        if self.namespace_prefix and self.namespace_declarations:
            # Suche nach dem Namespace für den Prefix
            for prefix, uri in self.namespace_declarations.items():
                if prefix == self.namespace_prefix:
                    ET.register_namespace(prefix, uri)
                    break

        # Root Element
        envelope = ET.Element(f'{{{soap_ns}}}Envelope')

        # Header falls vorhanden
        if self.header_content:
            header = ET.SubElement(envelope, f'{{{soap_ns}}}Header')
            header_element = ET.fromstring(self.header_content)
            header.append(header_element)

        # Body
        body = ET.SubElement(envelope, f'{{{soap_ns}}}Body')

        # Body Content parsen und direkt anhängen
        try:
            body_element = ET.fromstring(self.body_content)
            body.append(body_element)
        except ET.ParseError as e:
            raise ValueError(f"Ungültiger XML Body Content: {e}")

        xml_str = ET.tostring(envelope, encoding='unicode', method='xml')
        return f'<?xml version="1.0" encoding="utf-8"?>\n{xml_str}'

    def with_header(self, header_content: str) -> 'SoapEnvelope':
        """Gibt einen neuen Envelope mit Header zurück"""
        return SoapEnvelope(
            body_content=self.body_content,
            version=self.version,
            header_content=header_content,
            namespace_declarations=self.namespace_declarations,
            namespace_prefix=self.namespace_prefix  # ← NEU!
        )

    def with_namespace(self, prefix: str, uri: str) -> 'SoapEnvelope':
        """Fügt eine Namespace-Deklaration hinzu"""
        ns_decl = dict(self.namespace_declarations) if self.namespace_declarations else {}
        ns_decl[prefix] = uri

        return SoapEnvelope(
            body_content=self.body_content,
            version=self.version,
            header_content=self.header_content,
            namespace_declarations=ns_decl,
            namespace_prefix=self.namespace_prefix  # ← NEU!
        )

    def with_namespace_prefix(self, prefix: str) -> 'SoapEnvelope':
        """
        Setzt einen Namespace-Prefix für den Body-Content.

        Args:
            prefix: Der zu verwendende Prefix (z.B. 'web', 'tns', etc.)

        Returns:
            Neuer SoapEnvelope mit gesetztem Prefix
        """
        return SoapEnvelope(
            body_content=self.body_content,
            version=self.version,
            header_content=self.header_content,
            namespace_declarations=self.namespace_declarations,
            namespace_prefix=prefix
        )

    def __str__(self) -> str:
        return self.build()

    def __eq__(self, other) -> bool:
        if not isinstance(other, SoapEnvelope):
            return False
        return (self.body_content == other.body_content and
                self.version == other.version and
                self.header_content == other.header_content and
                self.namespace_declarations == other.namespace_declarations and
                self.namespace_prefix == other.namespace_prefix)  # ← NEU!

    def __hash__(self) -> int:
        ns_tuple = tuple(sorted(self.namespace_declarations.items())) if self.namespace_declarations else ()
        return hash((
            self.body_content,
            self.version,
            self.header_content,
            ns_tuple,
            self.namespace_prefix  # ← NEU!
        ))
