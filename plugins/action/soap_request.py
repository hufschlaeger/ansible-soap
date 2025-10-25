# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleError


class ActionModule(ActionBase):
  """Action plugin for soap_request module"""

  def run(self, tmp=None, task_vars=None):
    if task_vars is None:
      task_vars = dict()

    result = super(ActionModule, self).run(tmp, task_vars)
    del tmp

    # Get module args
    module_args = self._task.args.copy()

    # Liste aller Parameter die Templating brauchen
    template_fields = [
      'endpoint_url',
      'soap_action',
      'body',
      'body_dict',
      'body_root_tag',
      'namespace',
      'namespace_prefix',
      'soap_version',
      'soap_header',
      'headers',
      'timeout',
      'auth_type',
      'username',
      'password',
      'cert_path',
      'key_path',
      'validate_certs',
      'use_cache',
      'max_retries',
      'extract_xpath',
      'strip_namespaces',
      'validate'
    ]

    # Template alle vorhandenen Parameter
    for key in template_fields:
      if key in module_args:
        try:
          module_args[key] = self._templar.template(module_args[key])
        except Exception as e:
          raise AnsibleError(f"Failed to template parameter '{key}': {str(e)}")

    # Modul ausführen
    result.update(
      self._execute_module(
        module_name='hufschlaeger.soap_client.soap_request',
        module_args=module_args,
        task_vars=task_vars
      )
    )

    return result