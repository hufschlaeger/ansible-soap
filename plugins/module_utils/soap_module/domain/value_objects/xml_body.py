from typing import Dict, Any, Optional
import xml.etree.ElementTree as ET

class XmlBody:
    def __init__(self, value: str):
        self.value = value

    def __len__(self):
        return len(self.value or "")

    def is_soap_envelope(self) -> bool:
        # lightweight check to see if content contains SOAP Envelope tag
        if not self.value:
            return False
        content = self.value.lower()
        return ("<soap:envelope" in content) or ("<envelope" in content)

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        root_tag: str,
        namespace: Optional[str] = None,
        namespace_prefix: Optional[str] = None
    ) -> 'XmlBody':
      """Erstellt XML aus Dictionary."""

      if namespace and not namespace_prefix:
        # ✅ DEFAULT-NAMESPACE - NUR register_namespace verwenden!
        ET.register_namespace('', namespace)
        # 🔥 Root-Element MIT {namespace} erstellen
        root = ET.Element(f"{{{namespace}}}{root_tag}")
        # ❌ KEIN root.set('xmlns', ...) mehr!

      elif namespace and namespace_prefix:
        # PREFIX-NAMESPACE
        ET.register_namespace(namespace_prefix, namespace)
        root = ET.Element(f"{{{namespace}}}{root_tag}")

      else:
        # Kein Namespace
        root = ET.Element(root_tag)
        namespace = None

      def add_elements(parent: ET.Element, data: Dict[str, Any]):
        """Rekursiv Elemente hinzufügen"""
        for key, value in data.items():

          # Bei gesetztem Namespace: IMMER mit {namespace}
          if namespace:
            child = ET.SubElement(parent, f"{{{namespace}}}{key}")
          else:
            child = ET.SubElement(parent, key)

          # Wert setzen
          if isinstance(value, dict):
            add_elements(child, value)
          elif isinstance(value, list):
            parent.remove(child)
            for item in value:
              if namespace:
                list_child = ET.SubElement(parent, f"{{{namespace}}}{key}")
              else:
                list_child = ET.SubElement(parent, key)

              if isinstance(item, dict):
                add_elements(list_child, item)
              else:
                list_child.text = str(item)
          else:
            child.text = str(value)

      add_elements(root, data)
      xml_string = ET.tostring(root, encoding='unicode', method='xml')
      return cls(xml_string)

    @classmethod
    def from_string(cls, xml_string: str) -> 'XmlBody':
        return cls(xml_string)

    def to_string(self) -> str:
        return self.value

    def to_pretty_string(self) -> str:
        """Gibt formatierten XML-String zurück"""
        try:
            import xml.dom.minidom
            dom = xml.dom.minidom.parseString(self.value)
            return dom.toprettyxml(indent="  ")
        except Exception:
            return self.value
