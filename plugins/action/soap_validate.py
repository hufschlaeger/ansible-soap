# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleError


class ActionModule(ActionBase):
  """Action Plugin für soap_validate"""

  def run(self, tmp=None, task_vars=None):
    if task_vars is None:
      task_vars = dict()

    result = super(ActionModule, self).run(tmp, task_vars)

    if result.get('skipped', False) or result.get('failed', False):
      return result

    # Module-Parameter vorbereiten (DEINE Variablennamen)
    module_args = self._task.args.copy()

    # Endpoint URL templaten
    if 'endpoint_url' in module_args:
      module_args['endpoint_url'] = self._templar.template(module_args['endpoint_url'])

    # WSDL URL templaten
    if 'wsdl_url' in module_args:
      module_args['wsdl_url'] = self._templar.template(module_args['wsdl_url'])

    # Username/Password templaten (falls vorhanden)
    if 'username' in module_args:
      module_args['username'] = self._templar.template(module_args['username'])

    if 'password' in module_args:
      module_args['password'] = self._templar.template(module_args['password'])

    try:
      result.update(
        self._execute_module(
          module_name='hufschlaeger.soap_client.soap_validate',
          module_args=module_args,
          task_vars=task_vars,
          tmp=tmp
        )
      )
    except AnsibleError as e:
      result['failed'] = True
      result['msg'] = str(e)

    return result
