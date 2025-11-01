from __future__ import absolute_import, division, print_function

# !/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Daniel Hufschläger <daniel@hufschlaeger.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: soap_batch
short_description: Send multiple SOAP requests in batch
version_added: "1.0.0"
description:
    - Sends multiple SOAP requests simultaneously
    - Supports parallel execution
    - Stop-on-error option for error handling
    - Aggregates results from all requests
options:
    requests:
        description:
            - List of SOAP request definitions
            - Each request has the same parameters as soap_request module
        required: true
        type: list
        elements: dict
    parallel:
        description:
            - Whether to execute requests in parallel
        required: false
        type: bool
        default: false
    max_workers:
        description:
            - Maximum number of parallel workers
        required: false
        type: int
        default: 5
    stop_on_error:
        description:
            - Whether to stop on first error
        required: false
        type: bool
        default: false
    validate_certs:
        description:
            - Validate SSL certificates for all requests
        required: false
        type: bool
        default: true
requirements:
    - requests >= 2.25.0
    - lxml >= 4.6.0
author:
    - Daniel Hufschläger (@dhufe)
'''

EXAMPLES = r'''
- name: Sequential batch request
  hufschlaeger.soap_client.soap_batch:
    requests:
      - endpoint_url: "https://www.dataaccess.com/webservicesserver/NumberConversion.wso"
        soap_action: "NumberToWords"
        body_dict:
          NumberToWords:
            ubiNum: 42
        namespace: "http://www.dataaccess.com/webservicesserver/"
      - endpoint_url: "https://www.dataaccess.com/webservicesserver/NumberConversion.wso"
        soap_action: "NumberToWords"
        body_dict:
          NumberToWords:
            ubiNum: 123
        namespace: "http://www.dataaccess.com/webservicesserver/"
  register: batch_result

- name: Parallel batch request
  hufschlaeger.soap_client.soap_batch:
    parallel: true
    max_workers: 10
    requests:
      - endpoint_url: "https://api.example.com/soap"
        soap_action: "GetUser"
        body_dict:
          GetUser:
            userId: 1
      - endpoint_url: "https://api.example.com/soap"
        soap_action: "GetUser"
        body_dict:
          GetUser:
            userId: 2
      - endpoint_url: "https://api.example.com/soap"
        soap_action: "GetUser"
        body_dict:
          GetUser:
            userId: 3

- name: Batch with stop on error
  hufschlaeger.soap_client.soap_batch:
    stop_on_error: true
    requests:
      - endpoint_url: "https://api.example.com/soap"
        soap_action: "CriticalOperation1"
        body_dict:
          Operation:
            id: 1
      - endpoint_url: "https://api.example.com/soap"
        soap_action: "CriticalOperation2"
        body_dict:
          Operation:
            id: 2

- name: Batch with authentication
  hufschlaeger.soap_client.soap_batch:
    parallel: true
    requests:
      - endpoint_url: "https://secure.example.com/soap"
        soap_action: "GetData"
        auth_type: basic
        username: "user1"
        password: "{{ vault_pass1 }}"
        body_dict:
          GetData:
            id: 1
      - endpoint_url: "https://secure.example.com/soap"
        soap_action: "GetData"
        auth_type: basic
        username: "user2"
        password: "{{ vault_pass2 }}"
        body_dict:
          GetData:
            id: 2
'''

RETURN = r'''
total:
    description: Total number of requests
    type: int
    returned: always
    sample: 5
successful:
    description: Number of successful requests
    type: int
    returned: always
    sample: 4
failed:
    description: Number of failed requests
    type: int
    returned: always
    sample: 1
results:
    description: List of all request results
    type: list
    returned: always
    elements: dict
    sample:
        - success: true
          status_code: 200
          body: "<soap:Envelope>...</soap:Envelope>"
        - success: false
          error_message: "Connection timeout"
execution_time_ms:
    description: Total execution time in milliseconds
    type: float
    returned: always
    sample: 1250.5
changed:
    description: Whether any changes were made
    type: bool
    returned: always
    sample: true
'''

from ansible.module_utils.basic import AnsibleModule

# ============================================================================
# SOAP MODULE IMPORTS
# Try importing from collection (installed), fall back to local (development)
# ============================================================================

HAS_SOAP_MODULE = False
SOAP_MODULE_IMPORT_ERROR = None
IMPORT_SOURCE = None

# Try collection import (when installed via ansible-galaxy)
try:
  from ansible_collections.hufschlaeger.soap_client.plugins.module_utils.soap_module import (
    SoapRequestDTO,
    DtoMapper,
    BatchSendUseCase,
    BatchSendCommand,
    SendSoapRequestUseCase,
    HttpSoapRepository
  )

  HAS_SOAP_MODULE = True
  IMPORT_SOURCE = "collection"
except ImportError as collection_error:
  # Try local import (for development/testing)
  try:
    from ansible.module_utils.soap_module import (
      SoapRequestDTO,
      DtoMapper,
      BatchSendUseCase,
      BatchSendCommand,
      SendSoapRequestUseCase,
      HttpSoapRepository
    )

    HAS_SOAP_MODULE = True
    IMPORT_SOURCE = "local"
  except ImportError as local_error:
    HAS_SOAP_MODULE = False
    SOAP_MODULE_IMPORT_ERROR = (
      f"Failed to import SOAP module from both collection and local paths.\n"
      f"Collection import error: {collection_error}\n"
      f"Local import error: {local_error}\n"
      f"Please ensure the collection is properly installed: "
      f"ansible-galaxy collection install hufschlaeger.soap_client"
    )


def run_module():
  module_args = dict(
    endpoint_url=dict(type='str', required=True),
    soap_action=dict(type='str', required=False, default=''),
    body=dict(type='str', required=False),
    body_dict=dict(type='dict', required=False),
    body_root_tag=dict(type='str', required=False, default='Request'),
    namespace=dict(type='str', required=False),
    namespace_prefix=dict(type='str', required=False, default='ns'),
    skip_request_wrapper=dict(type='bool', required=False, default=False),
    soap_version=dict(type='str', required=False, default='1.1'),
    soap_header=dict(type='str', required=False),
    headers=dict(type='dict', required=False),
    timeout=dict(type='int', required=False, default=30),
    auth_type=dict(type='str', required=False, default='none'),
    username=dict(type='str', required=False),
    password=dict(type='str', required=False),
    cert_path=dict(type='str', required=False),
    key_path=dict(type='str', required=False),
    validate=dict(type='bool', required=False, default=True),
    use_cache=dict(type='bool', required=False, default=False),
    max_retries=dict(type='int', required=False, default=0),
    extract_xpath=dict(type='str', required=False),
    strip_namespaces=dict(type='bool', required=False, default=False),
    validate_certs=dict(type='bool', required=False, default=True),
  )

  module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

  if not HAS_SOAP_MODULE:
    module.fail_json(
      msg='SOAP Module could not be imported',
      error=SOAP_MODULE_IMPORT_ERROR,
      hint='Ensure collection is installed: ansible-galaxy collection install hufschlaeger.soap_client'
    )

  try:
    request_dto = SoapRequestDTO(
      endpoint_url=module.params.get('endpoint_url'),
      soap_action=module.params.get('soap_action', ''),
      body=module.params.get('body'),
      body_dict=module.params.get('body_dict'),
      body_root_tag=module.params.get('body_root_tag', 'Request'),
      namespace=module.params.get('namespace'),
      namespace_prefix=module.params.get('namespace_prefix', 'ns'),
      skip_request_wrapper=module.params.get('skip_request_wrapper', False),
      soap_version=module.params.get('soap_version', '1.1'),
      soap_header=module.params.get('soap_header'),
      headers=module.params.get('headers'),
      timeout=module.params.get('timeout', 30),
      auth_type=module.params.get('auth_type', 'none'),
      username=module.params.get('username'),
      password=module.params.get('password'),
      cert_path=module.params.get('cert_path'),
      key_path=module.params.get('key_path'),
      validate=module.params.get('validate', True),
      use_cache=module.params.get('use_cache', False),
      max_retries=module.params.get('max_retries', 0),
      extract_xpath=module.params.get('extract_xpath'),
      strip_namespaces=module.params.get('strip_namespaces', False),
    )

    is_valid, error_message = request_dto.validate_input()
    if not is_valid:
      module.fail_json(msg=f"Input validation failed: {error_message}", error=error_message)

    repository = HttpSoapRepository(verify_ssl=module.params.get('validate_certs', True))
    use_case = SendSoapRequestUseCase(repository)

    command = DtoMapper.dto_to_command(request_dto)
    result = use_case.execute(command)

    response_dto = DtoMapper.result_to_dto(result)
    response_payload = response_dto.to_dict()

    if not getattr(result, 'success', False):
      module.fail_json(msg='SOAP request failed', **response_payload)

    module.exit_json(changed=True, **response_payload)

  except Exception as e:
    module.fail_json(msg=f'Unexpected error: {e}')


def main():
  run_module()


if __name__ == '__main__':
  main()
