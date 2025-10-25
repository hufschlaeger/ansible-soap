"""
Domain Service für Validierungen.
"""
from typing import List, Optional, Dict, Any
from ..entities.soap_request import SoapRequest
from ..entities.endpoint import Endpoint
from ..value_objects.xml_body import XmlBody
from ..value_objects.url import Url
import re


class ValidationResult:
    """Ergebnis einer Validierung"""

    def __init__(self):
        self.is_valid: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def add_error(self, message: str) -> None:
        """Fügt einen Fehler hinzu"""
        self.is_valid = False
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        """Fügt eine Warnung hinzu"""
        self.warnings.append(message)

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary"""
        return {
            "valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings
        }


class ValidationService:
    """
    Domain Service für verschiedene Validierungen.
    """

    def validate_request(self, request: SoapRequest) -> ValidationResult:
        """
        Validiert einen kompletten SOAP-Request.

        Args:
            request: Der zu validierende Request

        Returns:
            ValidationResult mit Ergebnis
        """
        result = ValidationResult()

        # URL validieren
        try:
            Url.from_string(request.endpoint_url)
        except ValueError as e:
            result.add_error(f"Ungültige URL: {e}")

        # XML Body validieren
        try:
            xml_body = XmlBody.from_string(request.body)

            # Prüfen ob SOAP Envelope
            if not xml_body.is_soap_envelope():
                result.add_warning("Body ist kein SOAP Envelope")

            # Prüfen ob Body-Größe okay
            if len(xml_body) > 1024 * 1024:  # 1 MB
                result.add_warning("Body ist größer als 1 MB")

        except ValueError as e:
            result.add_error(f"Ungültiges XML: {e}")

        # Timeout validieren
        if request.timeout <= 0:
            result.add_error("Timeout muss größer als 0 sein")
        elif request.timeout > 300:
            result.add_warning("Timeout ist sehr hoch (> 300 Sekunden)")

        # SOAP Action validieren
        if not request.soap_action:
            result.add_warning("Keine SOAP Action definiert")

        # SOAP Version validieren
        if request.soap_version not in ["1.1", "1.2"]:
            result.add_error(f"Ungültige SOAP Version: {request.soap_version}")

        return result

    def validate_endpoint(self, endpoint: Endpoint) -> ValidationResult:
        """
        Validiert einen Endpoint.

        Args:
            endpoint: Der zu validierende Endpoint

        Returns:
            ValidationResult mit Ergebnis
        """
        result = ValidationResult()

        # URL validieren
        try:
            url = Url.from_string(endpoint.url)
            if not url.is_secure():
                result.add_warning("Endpoint verwendet kein HTTPS")
        except ValueError as e:
            result.add_error(f"Ungültige URL: {e}")

        # Auth validieren
        if endpoint.requires_auth():
            auth_config = endpoint.get_auth_config()

            if endpoint.auth_type in ["basic", "digest", "ntlm"]:
                if not endpoint.username or not endpoint.password:
                    result.add_error(
                        f"Auth-Type '{endpoint.auth_type}' erfordert Username und Password"
                    )

            elif endpoint.auth_type == "certificate":
                if not endpoint.cert_path:
                    result.add_error("Certificate Auth erfordert cert_path")

        # Timeout validieren
        if endpoint.default_timeout <= 0:
            result.add_error("Default Timeout muss größer als 0 sein")

        return result

    def validate_xml_against_schema(
            self,
            xml_content: str,
            xsd_schema: str
    ) -> ValidationResult:
        """
        Validiert XML gegen ein XSD-Schema.

        Args:
            xml_content: Der XML-Inhalt
            xsd_schema: Das XSD-Schema

        Returns:
            ValidationResult mit Ergebnis
        """
        result = ValidationResult()

        try:
            from lxml import etree

            # Schema parsen
            schema_root = etree.XML(xsd_schema.encode())
            schema = etree.XMLSchema(schema_root)

            # XML parsen
            xml_doc = etree.XML(xml_content.encode())

            # Validieren
            if not schema.validate(xml_doc):
                for error in schema.error_log:
                    result.add_error(f"Zeile {error.line}: {error.message}")

        except ImportError:
            result.add_warning("lxml nicht verfügbar, Schema-Validierung übersprungen")
        except Exception as e:
            result.add_error(f"Schema-Validierung fehlgeschlagen: {e}")

        return result

    def validate_soap_structure(self, xml_content: str) -> ValidationResult:
        """
        Validiert die grundlegende SOAP-Struktur.

        Args:
            xml_content: Der zu validierende XML-Content

        Returns:
            ValidationResult mit Ergebnis
        """
        result = ValidationResult()

        try:
            xml_body = XmlBody.from_string(xml_content)

            # Muss SOAP Envelope sein
            if not xml_body.is_soap_envelope():
                result.add_error("Kein SOAP Envelope gefunden")
                return result

            # Namespaces prüfen
            namespaces = xml_body.get_namespaces()
            soap_ns_found = False

            for prefix, uri in namespaces.items():
                if uri in [
                    'http://schemas.xmlsoap.org/soap/envelope/',
                    'http://www.w3.org/2003/05/soap-envelope'
                ]:
                    soap_ns_found = True
                    break

            if not soap_ns_found:
                result.add_error("Kein gültiger SOAP Namespace gefunden")

            # Body muss vorhanden sein
            body_content = xml_body.extract_body_content()
            if not body_content:
                result.add_error("Kein SOAP Body gefunden")

        except ValueError as e:
            result.add_error(f"Ungültiges XML: {e}")

        return result
