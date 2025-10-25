from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleActionFail
import json


class ActionModule(ActionBase):
  """Action Plugin für soap_batch mit body_dict Support"""

  def run(self, tmp=None, task_vars=None):
    """Führt Action aus"""
    if task_vars is None:
      task_vars = {}

    result = super(ActionModule, self).run(tmp, task_vars)
    del tmp

    # Task Args holen
    requests = self._task.args.get('requests', [])
    parallel = self._task.args.get('parallel', False)
    max_workers = self._task.args.get('max_workers', 5)
    stop_on_error = self._task.args.get('stop_on_error', False)
    validate_certs = self._task.args.get('validate_certs', True)

    if not requests:
      return {
        'failed': True,
        'msg': 'Parameter "requests" ist erforderlich'
      }

    # Jedes Request verarbeiten (body_dict -> body)
    processed_requests = []

    for idx, req in enumerate(requests):
      processed_req = dict(req)  # Copy

      # Wenn body_dict vorhanden: in XML umwandeln
      if 'body_dict' in processed_req:
        try:
          body_xml = self._build_xml_body(
            body_dict=processed_req.pop('body_dict'),
            root_tag=processed_req.pop('body_root_tag', None),
            namespace=processed_req.pop('namespace', None),
            namespace_prefix=processed_req.pop('namespace_prefix', 'ns')
          )
          processed_req['body'] = body_xml
        except Exception as e:
          return {
            'failed': True,
            'msg': f'Fehler beim Erstellen von Request #{idx + 1} XML Body: {str(e)}'
          }

      # Validierung
      if 'body' not in processed_req:
        return {
          'failed': True,
          'msg': f'Request #{idx + 1}: Weder "body" noch "body_dict" angegeben'
        }

      if 'endpoint_url' not in processed_req:
        return {
          'failed': True,
          'msg': f'Request #{idx + 1}: Parameter "endpoint_url" fehlt'
        }

      if 'soap_action' not in processed_req:
        return {
          'failed': True,
          'msg': f'Request #{idx + 1}: Parameter "soap_action" fehlt'
        }

      processed_requests.append(processed_req)

    # Module Args vorbereiten
    module_args = {
      'requests': processed_requests,
      'parallel': parallel,
      'max_workers': max_workers,
      'stop_on_error': stop_on_error,
      'validate_certs': validate_certs
    }

    # Modul ausführen
    result.update(
      self._execute_module(
        module_name='hufschlaeger.soap_client.soap_batch',
        module_args=module_args,
        task_vars=task_vars
      )
    )

    return result

  def _build_xml_body(self, body_dict, root_tag=None, namespace=None, namespace_prefix='ns'):
    """Baut XML Body aus Dictionary (wie in soap_request)"""
    try:
      from xml.etree import ElementTree as ET

      # Root Element
      if root_tag:
        if namespace:
          root = ET.Element(f'{{{namespace}}}{root_tag}')
        else:
          root = ET.Element(root_tag)
      else:
        # Nimm ersten Key als Root
        if not body_dict:
          raise ValueError("body_dict ist leer")
        root_key = list(body_dict.keys())[0]
        root_value = body_dict[root_key]

        if namespace:
          root = ET.Element(f'{{{namespace}}}{root_key}')
        else:
          root = ET.Element(root_key)

        if isinstance(root_value, dict):
          self._dict_to_xml(root_value, root, namespace, namespace_prefix)
        else:
          root.text = str(root_value)

        # Early return wenn kein root_tag
        if not root_tag:
          return ET.tostring(root, encoding='unicode', method='xml')

      # Body Content hinzufügen
      if root_tag:
        self._dict_to_xml(body_dict, root, namespace, namespace_prefix)

      # Namespace Registration für pretty output
      if namespace and namespace_prefix:
        ET.register_namespace(namespace_prefix, namespace)

      return ET.tostring(root, encoding='unicode', method='xml')

    except Exception as e:
      raise ValueError(f'Fehler beim XML-Aufbau: {str(e)}')

  def _dict_to_xml(self, data, parent, namespace=None, namespace_prefix='ns'):
    """Konvertiert Dictionary zu XML Elementen"""
    from xml.etree import ElementTree as ET
    for key, value in data.items():
      if namespace:
        child = ET.SubElement(parent, f'{{{namespace}}}{key}')
      else:
        child = ET.SubElement(parent, key)

      if isinstance(value, dict):
        self._dict_to_xml(value, child, namespace, namespace_prefix)
      elif isinstance(value, (list, tuple)):
        # Listen als wiederholte Elemente
        parent.remove(child)
        for item in value:
          if namespace:
            list_child = ET.SubElement(parent, f'{{{namespace}}}{key}')
          else:
            list_child = ET.SubElement(parent, key)

          if isinstance(item, dict):
            self._dict_to_xml(item, list_child, namespace, namespace_prefix)
          else:
            list_child.text = str(item)
      else:
        child.text = str(value)