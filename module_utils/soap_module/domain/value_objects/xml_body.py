"""
Value Object: XmlBody
Repräsentiert einen XML-Body mit Validierung und Manipulation.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re


@dataclass(frozen=True)
class XmlBody:
    """
    Immutable Value Object für XML-Bodies.
    Stellt sicher, dass der Body valides XML enthält.
    """

    value: str
    _is_validated: bool = False

    def __post_init__(self):
        """Validierung bei Erstellung"""
        if not self.value:
            raise ValueError("XML Body darf nicht leer sein")

        # XML-Validierung
        try:
            ET.fromstring(self.value)
            object.__setattr__(self, '_is_validated', True)
        except ET.ParseError as e:
            raise ValueError(f"Ungültiges XML: {e}")

    @classmethod
    def from_string(cls, xml_string: str) -> 'XmlBody':
        """Factory-Methode zum Erstellen aus String"""
        return cls(value=xml_string.strip())

    @classmethod
    def from_dict(cls, data: Dict[str, Any], root_tag: str = "root") -> 'XmlBody':
        """
        Factory-Methode zum Erstellen aus Dictionary.
        Einfache Konvertierung Dict -> XML.
        """
        root = ET.Element(root_tag)
        cls._dict_to_xml(data, root)
        xml_string = ET.tostring(root, encoding='unicode')
        return cls(value=xml_string)

    @staticmethod
    def _dict_to_xml(data: Dict[str, Any], parent: ET.Element) -> None:
        """Hilfsmethode zur Konvertierung von Dict zu XML"""
        for key, value in data.items():
            if isinstance(value, dict):
                child = ET.SubElement(parent, key)
                XmlBody._dict_to_xml(value, child)
            elif isinstance(value, list):
                for item in value:
                    child = ET.SubElement(parent, key)
                    if isinstance(item, dict):
                        XmlBody._dict_to_xml(item, child)
                    else:
                        child.text = str(item)
            else:
                child = ET.SubElement(parent, key)
                child.text = str(value)

    def get_root_element(self) -> ET.Element:
        """Gibt das Root-Element zurück"""
        return ET.fromstring(self.value)

    def get_root_tag(self) -> str:
        """Gibt den Tag-Namen des Root-Elements zurück"""
        return self.get_root_element().tag

    def to_pretty_string(self, indent: str = "  ") -> str:
        """Gibt eine formatierte Version des XML zurück"""
        try:
            dom = minidom.parseString(self.value)
            return dom.toprettyxml(indent=indent)
        except Exception:
            # Fallback: Original zurückgeben
            return self.value

    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert XML zu Dictionary.
        Vereinfachte Konvertierung für einfache Strukturen.
        """
        root = self.get_root_element()
        return {root.tag: self._element_to_dict(root)}

    def _element_to_dict(self, element: ET.Element) -> Any:
        """Hilfsmethode zur Konvertierung von XML Element zu Dict"""
        result: Dict[str, Any] = {}

        # Attribute hinzufügen
        if element.attrib:
            result['@attributes'] = element.attrib

        # Kinder verarbeiten
        children = list(element)
        if children:
            child_dict: Dict[str, Any] = {}
            for child in children:
                child_data = self._element_to_dict(child)
                if child.tag in child_dict:
                    # Mehrere Elemente mit gleichem Tag -> Liste
                    if not isinstance(child_dict[child.tag], list):
                        child_dict[child.tag] = [child_dict[child.tag]]
                    child_dict[child.tag].append(child_data)
                else:
                    child_dict[child.tag] = child_data
            result.update(child_dict)

        # Text hinzufügen
        if element.text and element.text.strip():
            if result:
                result['#text'] = element.text.strip()
            else:
                return element.text.strip()

        return result if result else None

    def strip_namespaces(self) -> 'XmlBody':
        """Gibt eine neue XmlBody-Instanz ohne Namespaces zurück"""
        xml_without_ns = re.sub(r'\sxmlns[^=]*="[^"]*"', '', self.value)
        xml_without_ns = re.sub(r'<(\w+:)?', '<', xml_without_ns)
        xml_without_ns = re.sub(r'</(\w+:)?', '</', xml_without_ns)
        return XmlBody(value=xml_without_ns)

    def has_namespace(self, namespace: str) -> bool:
        """Prüft ob ein bestimmter Namespace verwendet wird"""
        return f'xmlns="{namespace}"' in self.value or f"xmlns='{namespace}'" in self.value

    def get_namespaces(self) -> Dict[str, str]:
        """Extrahiert alle Namespace-Deklarationen"""
        root = self.get_root_element()
        namespaces = {}

        # Standard-Namespace
        for key, value in root.attrib.items():
            if key == 'xmlns':
                namespaces['default'] = value
            elif key.startswith('xmlns:'):
                prefix = key.split(':', 1)[1]
                namespaces[prefix] = value

        return namespaces

    def find_element(self, xpath: str) -> Optional[str]:
        """
        Findet ein Element per XPath und gibt seinen Text zurück.
        """
        try:
            root = self.get_root_element()
            element = root.find(xpath)
            return element.text if element is not None else None
        except Exception:
            return None

    def is_soap_envelope(self) -> bool:
        """Prüft ob es sich um einen SOAP Envelope handelt"""
        return (
                '<soap:Envelope' in self.value or
                '<SOAP-ENV:Envelope' in self.value or
                '<soapenv:Envelope' in self.value or
                'http://schemas.xmlsoap.org/soap/envelope/' in self.value or
                'http://www.w3.org/2003/05/soap-envelope' in self.value
        )

    def extract_body_content(self) -> Optional['XmlBody']:
        """
        Extrahiert den Inhalt aus einem SOAP Body.
        Gibt None zurück wenn kein SOAP Envelope.
        """
        if not self.is_soap_envelope():
            return None

        try:
            root = self.get_root_element()
            # Namespace-aware suchen
            namespaces = {
                'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                'soap12': 'http://www.w3.org/2003/05/soap-envelope'
            }

            body = (root.find('soap:Body', namespaces) or
                    root.find('soap12:Body', namespaces) or
                    root.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Body') or
                    root.find('.//{http://www.w3.org/2003/05/soap-envelope}Body'))

            if body is not None and len(body) > 0:
                body_content = ET.tostring(body[0], encoding='unicode')
                return XmlBody(value=body_content)

            return None
        except Exception:
            return None

    def minify(self) -> 'XmlBody':
        """Entfernt unnötige Whitespaces"""
        minified = re.sub(r'>\s+<', '><', self.value)
        return XmlBody(value=minified.strip())

    def __str__(self) -> str:
        return self.value

    def __len__(self) -> int:
        return len(self.value)

    def __eq__(self, other) -> bool:
        if not isinstance(other, XmlBody):
            return False
        # Vergleich ohne Whitespace-Unterschiede
        return self.minify().value == other.minify().value

    def __hash__(self) -> int:
        return hash(self.minify().value)
