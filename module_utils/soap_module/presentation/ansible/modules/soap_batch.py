#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: soap_batch
short_description: Sendet multiple SOAP-Requests
version_added: "1.0.0"
description:
    - Sendet mehrere SOAP-Requests gleichzeitig
    - Unterstützt parallele Ausführung
    - Stop-on-Error Option
options:
    requests:
        description:
            - Liste von SOAP-Request-Definitionen
            - Jeder Request hat die gleichen Parameter wie soap_request
        required: true
        type: list
        elements: dict
    parallel:
        description:
            - Ob Requests parallel ausgeführt werden sollen
        required: false
        type: bool
        default: false
    max_workers:
        description:
            - Maximale Anzahl paralleler Worker
        required: false
        type: int
        default: 5
    stop_on_error:
        description:
            - Ob bei ersten Fehler abgebrochen werden soll
        required: false
        type: bool
        default: false
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
# Sequential batch request
- name: Send multiple requests
  soap_batch:
    requests:
      - endpoint_url: https://api.example.com/soap
        soap_action: GetUser
        body_dict:
          UserId: "123"
      - endpoint_url: https://api.example.com/soap
        soap_action: GetUser
        body_dict:
          UserId: "456"
      - endpoint_url: https://api.example.com/soap
        soap_action: GetUser
        body_dict:
          UserId: "789"
  register: batch_result

# Parallel batch request
- name: Send requests in parallel
  soap_batch:
    parallel: true
    max_workers: 3
    requests:
      - endpoint_url: https://api1.example.com/soap
        soap_action: GetData
        body_dict:
          Id: "1"
      - endpoint_url: https://api2.example.com/soap
        soap_action: GetData
        body_dict:
          Id: "2"
      - endpoint_url: https://api3.example.com/soap
        soap_action: GetData
        body_dict:
          Id: "3"

- name: Show results
  debug:
    msg: "{{ batch_result.successful }} of {{ batch_result.total }} successful"
'''

RETURN = r'''
total:
    description: Gesamtanzahl der Requests
    type: int
    returned: always
    sample: 10
successful:
    description: Anzahl erfolgreicher Requests
    type: int
    returned: always
    sample: 9
failed:
    description: Anzahl fehlgeschlagener Requests
    type: int
    returned: always
    sample: 1
results:
    description: Liste aller Ergebnisse
    type: list
    returned: always
    sample: [{"success": true, "status_code": 200}, {"success": false}]
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from soap_module.application.dtos.soap_request_dto import SOAPRequestDTO
    from soap_module.application.mappers.dto_mapper import DtoMapper
    from soap_module.application.use_cases.batch_send_use_case import (
        BatchSendUseCase,
        BatchSendCommand
    )
    from soap_module.infrastructure.repositories.http_soap_repository import (
        HttpSoapRepository
    )
    HAS_SOAP_MODULE = True
except ImportError as e:
    HAS_SOAP_MODULE = False
    SOAP_MODULE_IMPORT_ERROR = str(e)


def run_module():
    """Hauptfunktion des Ansible-Moduls"""

    module_args = dict(
        requests=dict(type='list', required=True, elements='dict'),
        parallel=dict(type='bool', required=False, default=False),
        max_workers=dict(type='int', required=False, default=5),
        stop_on_error=dict(type='bool', required=False, default=False),
        validate_certs=dict(type='bool', required=False, default=True),
    )

    result = dict(
        changed=False,
        total=0,
        successful=0,
        failed=0,
        results=[]
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
        # Requests zu DTOs konvertieren
        request_dtos = []
        for req_params in module.params['requests']:
            # Defaults setzen
            req_params.setdefault('body_root_tag', 'Request')
            req_params.setdefault('namespace_prefix', 'ns')
            req_params.setdefault('soap_version', '1.1')
            req_params.setdefault('timeout', 30)
            req_params.setdefault('auth_type', 'none')
            req_params.setdefault('validate', True)
            req_params.setdefault('use_cache', False)
            req_params.setdefault('max_retries', 0)
            req_params.setdefault('strip_namespaces', False)

            dto = SoapRequestDTO(**req_params)

            # Validieren
            is_valid, error = dto.validate_input()
            if not is_valid:
                module.fail_json(
                    msg=f'Request-Validierung fehlgeschlagen: {error}',
                    **result
                )

            request_dtos.append(dto)

        # Repository und Use Case
        repository = HttpSoapRepository(
            verify_ssl=module.params['validate_certs']
        )
        use_case = BatchSendUseCase(repository)

        # Commands erstellen
        commands = [DtoMapper.dto_to_command(dto) for dto in request_dtos]

        # Batch Command
        batch_command = BatchSendCommand(
            requests=commands,
            parallel=module.params['parallel'],
            max_workers=module.params['max_workers'],
            stop_on_error=module.params['stop_on_error']
        )

        # Batch ausführen
        batch_result = use_case.execute(batch_command)

        # Result aktualisieren
        result.update(batch_result.to_dict())
        result['changed'] = batch_result.successful > 0

        # Cleanup
        repository.close()

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
