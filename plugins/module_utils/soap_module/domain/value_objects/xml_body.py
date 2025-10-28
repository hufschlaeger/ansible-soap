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
      root_tag: Optional[str] = None,
      namespace: Optional[str] = None,
      namespace_prefix: Optional[str] = None
  ) -> 'XmlBody':
    """
    Erstellt XML aus Dictionary.

    Args:
        data: Dictionary mit XML-Daten
        root_tag: Optional - Wenn None, wird kein Wrapper-Element erzeugt
        namespace: Optional - Namespace URL
        namespace_prefix: Optional - Namespace Prefix

    Returns:
        XmlBody Instanz

    Wenn `root_tag` None ist:
    - Bei einem Key in `data`: Dieses Element wird Root (empfohlen)
    - Bei mehreren Keys: Alle werden als Fragment serialisiert (Warnung!)
    """

    if not data:
      raise ValueError("data darf nicht leer sein")

    return_inner_fragment = False

    if root_tag is None:
      if len(data) > 1:
        import warnings
        warnings.warn(
          f"Ohne root_tag werden mehrere Elemente als Fragment erzeugt: "
          f"{list(data.keys())}. Das könnte zu ungültigem XML führen!",
          UserWarning
        )

      # Kein Wrapper-Root gewünscht → temporären Container verwenden
      if namespace and not namespace_prefix:
        ET.register_namespace('', namespace)
      elif namespace and namespace_prefix:
        ET.register_namespace(namespace_prefix, namespace)

      # Temporären Container anlegen (ohne Namespace!)
      root = ET.Element('tmp_root')
      return_inner_fragment = True

    else:
      # MIT root_tag (Standard-Verhalten)
      if namespace and not namespace_prefix:
        # Default-Namespace
        ET.register_namespace('', namespace)
        root = ET.Element(f"{{{namespace}}}{root_tag}")
      elif namespace and namespace_prefix:
        # Prefix-Namespace
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
              list_child.text = str(item) if item is not None else ''
        elif value is None:
          # Leeres Element (z.B. <getStatus/>)
          pass
        else:
          child.text = str(value)

    add_elements(root, data)

    if return_inner_fragment:
      # Als Fragment zurückgeben: direkte Kinder serialisieren
      children = list(root)
      if not children:
        raise ValueError("Keine XML-Elemente in data gefunden")

      xml_string = ''.join(
        ET.tostring(child, encoding='unicode', method='xml')
        for child in children
      )
    else:
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
