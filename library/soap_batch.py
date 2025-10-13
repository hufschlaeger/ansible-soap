#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = r'''
module: soap_batch
short_description: Sendet mehrere SOAP Requests parallel
description:
  - Sendet mehrere SOAP Requests gleichzeitig
  - Optional mit Parallelverarbeitung
options:
  requests:
    description: Liste von SOAP Requests
    required: true
    type: list
    elements: dict
  parallel:
    description: Requests parallel ausführen
    type: bool
    default: false
  max_workers:
    description: Maximale Anzahl paralleler Requests
    type: int
    default: 5
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.soap_module.application.use_cases.batch_soap_request_use_case import BatchSoapRequestUseCase


def run_module():
    module_args = dict(
        requests=dict(type='list', elements='dict', required=True),
        parallel=dict(type='bool', default=False),
        max_workers=dict(type='int', default=5),
        stop_on_error=dict(type='bool', default=False)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(
            changed=False,
            msg=f"Would send {len(module.params['requests'])} SOAP requests"
        )

    try:
        use_case = BatchSoapRequestUseCase()
        result = use_case.execute(
            requests=module.params['requests'],
            parallel=module.params['parallel'],
            max_workers=module.params['max_workers'],
            stop_on_error=module.params['stop_on_error']
        )

        module.exit_json(
            changed=True if result.success_count > 0 else False,
            total=result.total,
            success_count=result.success_count,
            failed_count=result.failed_count,
            results=result.results,
            execution_time_ms=result.execution_time_ms
        )

    except Exception as e:
        module.fail_json(msg=str(e))


def main():
    run_module()


if __name__ == '__main__':
    main()
