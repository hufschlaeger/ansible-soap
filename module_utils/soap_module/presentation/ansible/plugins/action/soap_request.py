"""
Action Plugin für erweiterte Funktionalität.
Ermöglicht Template-Rendering und Vault-Integration.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleError
from ansible.utils.vars import merge_hash


class ActionModule(ActionBase):
    """
    Action Plugin für soap_request Modul.
    Erweitert das Modul um Template- und Vault-Unterstützung.
    """

    def run(self, tmp=None, task_vars=None):
        """
        Führt die Action aus.

        Args:
            tmp: Temporäres Verzeichnis
            task_vars: Task-Variablen

        Returns:
            Result-Dictionary
        """
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp wird nicht mehr benötigt

        # Module-Args holen
        module_args = self._task.args.copy()

        # Template-Rendering für body
        if 'body' in module_args and module_args['body']:
            try:
                module_args['body'] = self._templar.template(
                    module_args['body'],
                    preserve_trailing_newlines=True
                )
            except Exception as e:
                raise AnsibleError(f"Template-Rendering für body fehlgeschlagen: {e}")

        # Template-Rendering für endpoint_url
        if 'endpoint_url' in module_args:
            try:
                module_args['endpoint_url'] = self._templar.template(
                    module_args['endpoint_url']
                )
            except Exception as e:
                raise AnsibleError(f"Template-Rendering für endpoint_url fehlgeschlagen: {e}")

        # Vault-Variablen für Passwörter
        if 'password' in module_args and module_args['password']:
            # Wird automatisch von Ansible gehandhabt
            pass

        # Modul ausführen
        result.update(
            self._execute_module(
                module_name='soap_request',
                module_args=module_args,
                task_vars=task_vars
            )
        )

        return result
