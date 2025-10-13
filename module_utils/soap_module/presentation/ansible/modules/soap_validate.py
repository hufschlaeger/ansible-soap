#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: soap_validate
short_description: Validiert SOAP-Endpoints
version_added: "1.0.0"
description:
    - Validiert ob ein SOAP-Endpoint erreichbar ist
    - Prüft WSDL-Verfügbarkeit
    - Listet verfügbare Operationen auf
options:
    endpoint_url:
        description:
            - URL des SOAP-Endpoints
        required: true
        type: str
    check_connectivity:
        description:
            - Ob Erreichbarkeit geprüft werden soll
        required: false
        type: bool
        default: true
    check_wsdl:
        description:
            - Ob WSDL geprüft werden soll
        required: false
        type: bool
        default: false
    wsdl_url:
        description:
            - URL der WSDL (falls abweichend von endpoint_url?wsdl)
        required: false
        type: str
    timeout:
        description:
            - Timeout in Sekunden
        required: false
        type: int
        default: 5
    validate_certs:
        description:
            - Ob SSL-Zertifikate validiert werden sollen
        required: false
        type: bool
        default: true

author:
    - Your Name (@yourhandle)
'''

EXAMPLES = r'''
# Einfache Validierung
- name: Check if endpoint is reachable
  soap_validate:
    endpoint_url: https://api.example.com/soap

# Mit WSDL-Check
- name: Validate endpoint and check WSDL
  soap_validate:
    endpoint_url: https://api.example.com/soap
    check_wsdl: true
  register: validation

- name: Show available operations
  debug:
    var: validation.wsdl_operations
'''

RETURN = r'''
valid:
    description: Ob der Endpoint gültig ist
    type: bool
    returned: always
    sample: true
reachable:
    description: Ob der Endpoint erreichbar ist
    type: bool
    returned: always
    sample: true
has_wsdl:
    description: Ob WSDL verfügbar ist
    type: bool
    returned: when check_wsdl is true
    sample: true
wsdl_operations:
    description: Liste der verfügbaren SOAP-Operationen
    type: list
    returned: when check_wsdl is true
    sample: ["GetUser", "UpdateUser", "DeleteUser"]
validation_errors:
    description: Liste der Validierungsfehler
    type: list
    returned: when validation fails
    sample: ["URL format invalid", "Port not reachable"]
error_message:
    description: Fehlermeldung bei Fehler
    type: str
    returned: on failure
    sample: "Connection refused"
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from ansible.module_utils.soap_module.application.dtos.soap_request_dto import EndpointValidationDTO
    from ansible.module_utils.soap_module.application.use_cases.validate_endpoint_use_case import (
        ValidateEndpointUseCase,
        ValidateEndpointCommand
    )
    from ansible.module_utils.soap_module.domain.entities.endpoint import Endpoint
    from ansible.module_utils.soap_module.infrastructure.repositories.http_soap_repository import (
        HttpSoapRepository
    )
    HAS_SOAP_MODULE = True
except ImportError as e:
    HAS_SOAP_MODULE = False
    SOAP_MODULE_IMPORT_ERROR = str(e)


def run_module():
    """Hauptfunktion des Ansible-Moduls"""

    module_args = dict(
        endpoint_url=dict(type='str', required=True),
        check_connectivity=dict(type='bool', required=False, default=True),
        check_wsdl=dict(type='bool', required=False, default=False),
        wsdl_url=dict(type='str', required=False),
        timeout=dict(type='int', required=False, default=5),
        validate_certs=dict(type='bool', required=False, default=True),
    )

    result = dict(
        changed=False,
        valid=False,
        reachable=False,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if not HAS_SOAP_MODULE:
        module.fail_json(
            msg='SOAP Module konnte nicht importiert werden',
            error=SOAP_MODULE_IMPORT_ERROR
        )

    if module.check_mode:
        module.exit_json(**result)

    try:
        # Endpoint erstellen
        endpoint = Endpoint(
            url=module.params['endpoint_url'],
            name='validation',
            default_timeout=module.params['timeout']
        )

        # Command erstellen
        command = ValidateEndpointCommand(
            endpoint=endpoint,
            check_connectivity=module.params['check_connectivity'],
            check_wsdl=module.params['check_wsdl'],
            wsdl_url=module.params.get('wsdl_url')
        )

        # Repository und Use Case
        repository = HttpSoapRepository(
            verify_ssl=module.params['validate_certs'],
            timeout=module.params['timeout']
        )
        use_case = ValidateEndpointUseCase(repository)

        # Validierung ausführen
        validation_result = use_case.execute(command)

        # Result aktualisieren
        result.update(validation_result.to_dict())

        # Cleanup
        repository.close()

        if not validation_result.is_valid:
            module.fail_json(
                msg='Endpoint-Validierung fehlgeschlagen',
                **result
            )

    except Exception as e:
        module.fail_json(
            msg=f'Unerwarteter Fehler: {str(e)}',
            exception=str(e),
            **result
        )

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
