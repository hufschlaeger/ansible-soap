#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = r'''
module: soap_request
short_description: Sendet SOAP Requests
description:
  - Sendet SOAP Requests an Webservices
options:
  endpoint_url:
    description: URL des SOAP Endpoints
    required: true
    type: str
  soap_action:
    description: SOAP Action
    required: true
    type: str
  # ... alle Parameter
'''

EXAMPLES = r'''
- name: Simple SOAP Request
  soap_request:
    endpoint_url: https://api.example.com/soap
    soap_action: GetUser
    body_dict:
      UserId: "123"
'''

RETURN = r'''
success:
  description: Ob Request erfolgreich war
  returned: always
  type: bool
status_code:
  description: HTTP Status Code
  returned: always
  type: int
body:
  description: Response Body
  returned: when successful
  type: str
# ... alle Return-Werte
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.soap_module.presentation.ansible.ansible_soap_controller import AnsibleSoapController


def run_module():
    """Hauptfunktion des Moduls"""

    # 1. Modul-Spezifikation (welche Parameter werden akzeptiert?)
    module_args = dict(
        endpoint_url=dict(type='str', required=True),
        soap_action=dict(type='str', required=True),
        body=dict(type='str', required=False),
        body_dict=dict(type='dict', required=False),
        body_root_tag=dict(type='str', default='Request'),
        namespace=dict(type='str', required=False),
        soap_version=dict(type='str', default='1.1', choices=['1.1', '1.2']),
        timeout=dict(type='int', default=30),
        auth_type=dict(type='str', choices=['none', 'basic', 'ntlm', 'digest', 'oauth2']),
        username=dict(type='str', no_log=False),
        password=dict(type='str', no_log=True),
        # ... alle Parameter
    )

    # 2. Ansible Module initialisieren
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        mutually_exclusive=[
            ['body', 'body_dict']  # Nur eins von beiden erlaubt
        ],
        required_one_of=[
            ['body', 'body_dict']  # Mindestens eins muss angegeben sein
        ]
    )

    # 3. Check Mode behandeln
    if module.check_mode:
        module.exit_json(changed=False, msg="Would send SOAP request")

    try:
        # 4. Controller erstellen und Request verarbeiten
        controller = AnsibleSoapController(module)
        result = controller.handle_soap_request(module.params)

        # 5. Erfolg zurückmelden
        module.exit_json(**result)

    except Exception as e:
        # 6. Fehler zurückmelden
        module.fail_json(msg=str(e))


def main():
    run_module()


if __name__ == '__main__':
    main()
