#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = r'''
module: soap_validate
short_description: Validiert SOAP Endpoints
description:
  - Prüft ob SOAP Endpoint erreichbar ist
  - Optional: Validiert WSDL
options:
  endpoint_url:
    description: URL des Endpoints
    required: true
    type: str
  check_wsdl:
    description: WSDL validieren
    type: bool
    default: false
  timeout:
    description: Timeout in Sekunden
    type: int
    default: 10
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.soap_module.application.use_cases.validate_endpoint_use_case import ValidateEndpointUseCase


def run_module():
    module_args = dict(
        endpoint_url=dict(type='str', required=True),
        check_wsdl=dict(type='bool', default=False),
        check_ssl=dict(type='bool', default=True),
        timeout=dict(type='int', default=10)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(changed=False, msg="Would validate endpoint")

    try:
        use_case = ValidateEndpointUseCase()
        result = use_case.execute(
            endpoint_url=module.params['endpoint_url'],
            check_wsdl=module.params['check_wsdl'],
            check_ssl=module.params['check_ssl'],
            timeout=module.params['timeout']
        )

        module.exit_json(
            changed=False,
            is_valid=result.is_valid,
            is_reachable=result.is_reachable,
            response_time_ms=result.response_time_ms,
            wsdl_valid=result.wsdl_valid,
            ssl_valid=result.ssl_valid,
            errors=result.errors
        )

    except Exception as e:
        module.fail_json(msg=str(e))


def main():
    run_module()


if __name__ == '__main__':
    main()
