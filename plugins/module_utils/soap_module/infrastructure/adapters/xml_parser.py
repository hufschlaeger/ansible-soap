"""
XML Parser Adapter.
Abstrahiert XML-Parsing-Bibliothek.
"""
from typing import Dict, Any, Optional, List
from xml.etree import ElementTree as ET
from xml.dom import minidom
import re


class XmlParserError(Exception):
    """Exception für XML-Parsing-Fehler"""
    pass


class XmlParser:
    """
    XML Parser für SOAP-Responses.
    Wrapper um ElementTree.
    """

    @staticmethod
    def parse(xml_string: str) -> ET.Element:
        """
        Parsed XML-String zu Element.

        Args:
            xml_string: XML als String

        Returns:
            ElementTree Element

        Raises:
            XmlParserError: Bei Parsing-Fehlern
        """
        try:
            return ET.fromstring(xml_string)
        except ET.ParseError as e:
            raise XmlParserError(f"XML-Parsing fehlgeschlagen: {e}")

    @staticmethod
    def to_string(element: ET.Element, pretty: bool = False) -> str:
        """
        Konvertiert Element zu String.

        Args:
            element: ElementTree Element
            pretty: Ob formatiert werden soll

        Returns:
            XML als String
        """
        xml_string = ET.tostring(element, encoding='unicode')

        if pretty:
            try:
                dom = minidom.parseString(xml_string)
                return dom.toprettyxml(indent="  ")
            except Exception:
                return xml_string

        return xml_string

    @staticmethod
    def element_to_dict(element: ET.Element) -> Dict[str, Any]:
        """
        Konvertiert XML-Element rekursiv zu Dictionary.

        Args:
            element: ElementTree Element

        Returns:
            Dictionary-Repräsentation
        """
        result: Dict[str, Any] = {}

        # Attributes hinzufügen
        if element.attrib:
            result['@attributes'] = element.attrib

        # Text-Content
        if element.text and element.text.strip():
            result['#text'] = element.text.strip()

        # Kinder verarbeiten
        for child in element:
            child_data = XmlParser.element_to_dict(child)

            # Namespace vom Tag entfernen
            tag = XmlParser._remove_namespace(child.tag)

            # Wenn Tag schon existiert, Liste erstellen
            if tag in result:
                if not isinstance(result[tag], list):
                    result[tag] = [result[tag]]
                result[tag].append(child_data)
            else:
                result[tag] = child_data

        # Wenn nur Text, direkt Text zurückgeben
        if len(result) == 1 and '#text' in result:
            return result['#text']

        return result

    @staticmethod
    def dict_to_element(
            data: Dict[str, Any],
            root_tag: str = 'root'
    ) -> ET.Element:
        """
        Konvertiert Dictionary zu XML-Element.

        Args:
            data: Dictionary mit Daten
            root_tag: Tag für Root-Element

        Returns:
            ElementTree Element
        """
        root = ET.Element(root_tag)
        XmlParser._dict_to_element_recursive(root, data)
        return root

    @staticmethod
    def _dict_to_element_recursive(parent: ET.Element, data: Any) -> None:
        """Rekursive Hilfsmethode für dict_to_element"""
        if isinstance(data, dict):
            for key, value in data.items():
                if key == '@attributes':
                    parent.attrib.update(value)
                elif key == '#text':
                    parent.text = str(value)
                else:
                    if isinstance(value, list):
                        for item in value:
                            child = ET.SubElement(parent, key)
                            XmlParser._dict_to_element_recursive(child, item)
                    else:
                        child = ET.SubElement(parent, key)
                        XmlParser._dict_to_element_recursive(child, value)
        else:
            parent.text = str(data)

    @staticmethod
    def find_elements(
            element: ET.Element,
            xpath: str,
            namespaces: Optional[Dict[str, str]] = None
    ) -> List[ET.Element]:
        """
        Findet Elemente via XPath.

        Args:
            element: Root-Element
            xpath: XPath-Ausdruck
            namespaces: Namespace-Map

        Returns:
            Liste gefundener Elemente
        """
        try:
            return element.findall(xpath, namespaces or {})
        except Exception as e:
            raise XmlParserError(f"XPath-Suche fehlgeschlagen: {e}")

    @staticmethod
    def find_element_text(
            element: ET.Element,
            xpath: str,
            namespaces: Optional[Dict[str, str]] = None,
            default: Optional[str] = None
    ) -> Optional[str]:
        """
        Findet Element und gibt Text zurück.

        Args:
            element: Root-Element
            xpath: XPath-Ausdruck
            namespaces: Namespace-Map
            default: Default-Wert wenn nicht gefunden

        Returns:
            Text des Elements oder default
        """
        found = element.find(xpath, namespaces or {})
        if found is not None and found.text:
            return found.text.strip()
        return default

    @staticmethod
    def extract_namespaces(element: ET.Element) -> Dict[str, str]:
        """
        Extrahiert alle Namespaces aus einem Element.

        Args:
            element: ElementTree Element

        Returns:
            Dictionary mit Namespace-Präfixen und URIs
        """
        namespaces = {}

        # Namespaces aus Root-Element
        for prefix, uri in element.attrib.items():
            if prefix.startswith('{http://www.w3.org/2000/xmlns/}'):
                ns_prefix = prefix.split('}')[1]
                namespaces[ns_prefix] = uri

        # Standard-Namespace
        if element.tag.startswith('{'):
            uri = element.tag[1:].split('}')[0]
            namespaces[''] = uri

        return namespaces

    @staticmethod
    def strip_namespaces(element: ET.Element) -> ET.Element:
        """
        Entfernt alle Namespaces aus Element-Tree.

        Args:
            element: ElementTree Element

        Returns:
            Element ohne Namespaces
        """
        # Tag-Name ohne Namespace
        if '}' in element.tag:
            element.tag = element.tag.split('}')[1]

        # Rekursiv für Kinder
        for child in element:
            XmlParser.strip_namespaces(child)

        return element

    @staticmethod
    def _remove_namespace(tag: str) -> str:
        """Entfernt Namespace aus Tag-Name"""
        if '}' in tag:
            return tag.split('}')[1]
        return tag

    @staticmethod
    def validate_xml(xml_string: str) -> bool:
        """
        Validiert ob String gültiges XML ist.

        Args:
            xml_string: Zu validierender String

        Returns:
            True wenn gültig, False sonst
        """
        try:
            ET.fromstring(xml_string)
            return True
        except ET.ParseError:
            return False

    @staticmethod
    def extract_soap_body(element: ET.Element) -> Optional[ET.Element]:
        """
        Extrahiert SOAP Body aus Envelope.

        Args:
            element: SOAP Envelope Element

        Returns:
            Body-Element oder None
        """
        # SOAP 1.1 und 1.2 Namespaces
        soap_namespaces = {
            'soap11': 'http://schemas.xmlsoap.org/soap/envelope/',
            'soap12': 'http://www.w3.org/2003/05/soap-envelope'
        }

        # Versuche beide SOAP-Versionen
        for ns_prefix, ns_uri in soap_namespaces.items():
            body = element.find(f'.//{{{ns_uri}}}Body')
            if body is not None:
                # Erstes Kind-Element des Body zurückgeben
                for child in body:
                    return child

        return None
