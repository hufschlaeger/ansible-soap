"""
Value Object: SoapAction
Repräsentiert eine SOAP Action mit Validierung.
"""
from dataclasses import dataclass
from typing import Optional
import re


@dataclass(frozen=True)
class SoapAction:
    """
    Immutable Value Object für SOAP Actions.
    Eine SOAP Action ist typischerweise eine URI oder ein Name einer Operation.
    """

    value: str
    namespace: Optional[str] = None

    def __post_init__(self):
        """Validierung bei Erstellung"""
        if not self.value:
            raise ValueError("SOAP Action darf nicht leer sein")

        # Action sollte keine Whitespaces enthalten
        if any(c.isspace() for c in self.value):
            raise ValueError(f"SOAP Action darf keine Leerzeichen enthalten: {self.value}")

    @classmethod
    def from_string(cls, action_string: str, namespace: Optional[str] = None) -> 'SoapAction':
        """Factory-Methode zum Erstellen aus String"""
        return cls(value=action_string.strip(), namespace=namespace)

    @classmethod
    def from_qualified_name(cls, qualified_name: str) -> 'SoapAction':
        """
        Factory-Methode zum Erstellen aus qualified name.
        Format: namespace#action oder namespace/action
        """
        if '#' in qualified_name:
            namespace, action = qualified_name.rsplit('#', 1)
        elif '/' in qualified_name and '://' not in qualified_name:
            namespace, action = qualified_name.rsplit('/', 1)
        else:
            return cls(value=qualified_name)

        return cls(value=action, namespace=namespace)

    def get_qualified_name(self, separator: str = '#') -> str:
        """
        Gibt den vollqualifizierten Namen zurück.
        Format: namespace#action
        """
        if self.namespace:
            return f"{self.namespace}{separator}{self.value}"
        return self.value

    def is_uri(self) -> bool:
        """Prüft ob die Action eine URI ist"""
        uri_pattern = re.compile(
            r'^https?://'  # http:// oder https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return bool(uri_pattern.match(self.value))

    def to_header_value(self, soap_version: str = "1.1") -> str:
        """
        Gibt den Wert zurück, wie er im SOAPAction-Header verwendet wird.
        SOAP 1.1: SOAPAction Header mit Anführungszeichen
        SOAP 1.2: Als Teil des Content-Type Headers
        """
        if soap_version == "1.1":
            return f'"{self.value}"'
        else:
            return self.value

    def __str__(self) -> str:
        return self.get_qualified_name()

    def __eq__(self, other) -> bool:
        if not isinstance(other, SoapAction):
            return False
        return self.value == other.value and self.namespace == other.namespace

    def __hash__(self) -> int:
        return hash((self.value, self.namespace))
