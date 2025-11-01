#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Daniel Hufschläger <daniel@hufschlaeger.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

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
  """Main module execution function"""

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

  # Check if SOAP module is available
  if not HAS_SOAP_MODULE:
    module.fail_json(
      msg='SOAP Module could not be imported',
      error=SOAP_MODULE_IMPORT_ERROR,
      hint='Ensure collection is installed: ansible-galaxy collection install hufschlaeger.soap_client'
    )

  if module.check_mode:
    result['msg'] = 'Check mode: would process {} requests'.format(
      len(module.params['requests'])
    )
    result['total'] = len(module.params['requests'])
    module.exit_json(**result)

  try:
    # Convert request parameters to DTOs
    request_dtos = []
    for idx, req_params in enumerate(module.params['requests']):
      # Set defaults for optional parameters
      req_params.setdefault('body_root_tag', 'Request')
      req_params.setdefault('namespace_prefix', 'ns')
      req_params.setdefault('soap_version', '1.1')
      req_params.setdefault('timeout', 30)
      req_params.setdefault('auth_type', 'none')
      req_params.setdefault('validate', True)
      req_params.setdefault('use_cache', False)
      req_params.setdefault('max_retries', 0)
      req_params.setdefault('strip_namespaces', False)
      req_params.setdefault('skip_request_wrapper', False)

      # Create DTO
      try:
        dto = SoapRequestDTO(**req_params)
      except TypeError as e:
        module.fail_json(
          msg=f'Invalid parameters for request {idx}: {str(e)}',
          request_index=idx,
          **result
        )

      # Validate input
      is_valid, error = dto.validate_input()
      if not is_valid:
        module.fail_json(
          msg=f'Request {idx} validation failed: {error}',
          request_index=idx,
          validation_error=error,
          **result
        )

      request_dtos.append(dto)

    # Initialize repository and use case
    repository = HttpSoapRepository(
      verify_ssl=module.params['validate_certs']
    )
    use_case = BatchSendUseCase(repository)

    # Convert DTOs to commands
    commands = [DtoMapper.dto_to_command(dto) for dto in request_dtos]

    # Create batch command
    batch_command = BatchSendCommand(
      requests=commands,
      parallel=module.params['parallel'],
      max_workers=module.params['max_workers'],
      stop_on_error=module.params['stop_on_error']
    )

    # Execute batch
    batch_result = use_case.execute(batch_command)

    # Update result
    result.update(batch_result.to_dict())
    result['changed'] = batch_result.successful > 0

    # Add metadata
    result['import_source'] = IMPORT_SOURCE

    # Cleanup
    repository.close()

  except Exception as e:
    module.fail_json(
      msg=f'Unexpected error during batch execution: {str(e)}',
      exception=str(e),
      **result
    )

  module.exit_json(**result)


def main():
  run_module()


if __name__ == '__main__':
  main()
