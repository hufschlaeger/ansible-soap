#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: soap_request
short_description: Send SOAP requests to web services
version_added: "1.0.0"
'''

EXAMPLES = r'''
- name: Simple SOAP request
  hufschlaeger.soap_client.soap_request:
    endpoint_url: "https://example.com/soap"
    soap_action: "test"
    body_xml: "<test>data</test>"
'''

RETURN = r'''
status_code:
    description: HTTP status code
    returned: always
    type: int
'''

from ansible.module_utils.basic import AnsibleModule

HAS_SOAP_MODULE = False
SOAP_MODULE_IMPORT_ERROR = None

try:
  from ansible_collections.hufschlaeger.soap_client.plugins.module_utils.soap_module.application.dtos.soap_request_dto import \
    SoapRequestDTO
  from ansible_collections.hufschlaeger.soap_client.plugins.module_utils.soap_module.application.use_cases.send_soap_request_use_case import \
    SendSoapRequestUseCase
  from ansible_collections.hufschlaeger.soap_client.plugins.module_utils.soap_module.infrastructure.repositories.http_soap_repository import \
    HttpSoapRepository
  from ansible_collections.hufschlaeger.soap_client.plugins.module_utils.soap_module.application.mappers.dto_mapper import \
    DtoMapper

  HAS_SOAP_MODULE = True
except ImportError as e:
  SOAP_MODULE_IMPORT_ERROR = str(e)


def run_module():
  module = AnsibleModule(
    argument_spec=dict(
      endpoint_url=dict(type='str', required=True),
      soap_action=dict(type='str', required=False, default=''),
      body_dict=dict(type='dict', required=False),
      body_xml=dict(type='str', required=False),
      namespace=dict(type='str', required=False, default=''),
      timeout=dict(type='int', required=False, default=30),
      validate_certs=dict(type='bool', required=False, default=True),
    ),
    supports_check_mode=True
  )

  result = {'changed': False}

  if not HAS_SOAP_MODULE:
    module.fail_json(msg='SOAP Module not available', error=SOAP_MODULE_IMPORT_ERROR)

  try:
    dto = SoapRequestDTO(
      endpoint_url=module.params['endpoint_url'],
      soap_action=module.params.get('soap_action', ''),
      body_dict=module.params.get('body_dict'),
      body_xml=module.params.get('body_xml'),
      namespace=module.params.get('namespace', ''),
      timeout=module.params.get('timeout', 30),
      validate_certs=module.params.get('validate_certs', True)
    )

    is_valid, error = dto.validate_input()
    if not is_valid:
      module.fail_json(msg=f'Validation failed: {error}')

    command = DtoMapper.dto_to_command(dto)
    repository = HttpSoapRepository(
      verify_ssl=module.params['validate_certs'],
      timeout=module.params['timeout']
    )

    try:
      use_case = SendSoapRequestUseCase(repository)
      response = use_case.execute(command)
      result.update(response.to_dict())
      result['changed'] = True
    finally:
      repository.close()

  except Exception as e:
    module.fail_json(msg=f'Error: {str(e)}')

  module.exit_json(**result)


def main():
  run_module()


if __name__ == '__main__':
  main()