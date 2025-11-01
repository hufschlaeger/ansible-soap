#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Daniel Hufschläger <daniel@hufschlaeger.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: soap_validate
short_description: Validate SOAP endpoint connectivity and availability
version_added: "1.0.0"
description:
    - Checks if a SOAP endpoint is reachable
    - Validates SSL certificates
    - Tests authentication if provided
    - Measures response time
    - Can optionally fetch and validate WSDL
    - Returns list of available operations from WSDL
options:
    endpoint_url:
        description: 
            - SOAP endpoint URL to validate
            - Can be WSDL URL or service endpoint
        required: true
        type: str
        aliases: ['endpoint', 'url']
    timeout:
        description: 
            - Connection timeout in seconds
            - Applies to all validation checks
        required: false
        type: int
        default: 10
    validate_certs:
        description: 
            - Validate SSL certificates
            - Set to false for self-signed certificates in dev/test environments
        required: false
        type: bool
        default: true
    check_wsdl:
        description:
            - Additionally check if WSDL is accessible and valid
            - Will attempt to parse WSDL and extract operations
        required: false
        type: bool
        default: false
    auth_type:
        description: 
            - Authentication type for validation
            - Used to test if credentials work with endpoint
        required: false
        type: str
        choices: ['basic', 'digest', 'ntlm', 'none']
        default: 'none'
    username:
        description: 
            - Username for authentication
            - Required when auth_type is not 'none'
        required: false
        type: str
    password:
        description: 
            - Password for authentication
            - Required when auth_type is not 'none'
        required: false
        type: str
        no_log: true
requirements:
    - requests >= 2.25.0
    - lxml >= 4.6.0
author:
    - Daniel Hufschläger (@dhufe)
'''

EXAMPLES = r'''
- name: Simple endpoint validation
  hufschlaeger.soap_client.soap_validate:
    endpoint_url: "https://www.dataaccess.com/webservicesserver/NumberConversion.wso"
    timeout: 5
  register: validation

- name: Show validation result
  debug:
    msg: "Endpoint is {{ 'valid' if validation.is_valid else 'invalid' }} - {{ validation.msg }}"

- name: Validate with SSL check disabled
  hufschlaeger.soap_client.soap_validate:
    endpoint_url: "https://dev.example.com/soap"
    validate_certs: false
    timeout: 10
  register: dev_check

- name: Validate WSDL accessibility
  hufschlaeger.soap_client.soap_validate:
    endpoint_url: "https://api.example.com/service?wsdl"
    check_wsdl: true
    timeout: 15
  register: wsdl_check

- name: Show available WSDL operations
  debug:
    var: wsdl_check.wsdl_operations
  when: wsdl_check.is_valid and wsdl_check.wsdl_valid

- name: Validate with authentication
  hufschlaeger.soap_client.soap_validate:
    endpoint_url: "https://api.example.com/soap"
    auth_type: basic
    username: "api_user"
    password: "{{ vault_password }}"
    timeout: 10
  register: auth_check

- name: Fail if endpoint is not reachable
  hufschlaeger.soap_client.soap_validate:
    endpoint_url: "{{ soap_endpoint }}"
    timeout: 5
  register: endpoint_check
  failed_when: not endpoint_check.is_valid

- name: Use validation in conditional workflow
  block:
    - name: Check endpoint availability
      hufschlaeger.soap_client.soap_validate:
        endpoint_url: "{{ soap_endpoint }}"
        check_wsdl: true
      register: check

    - name: Proceed only if valid
      hufschlaeger.soap_client.soap_request:
        endpoint_url: "{{ soap_endpoint }}"
        soap_action: "GetData"
        body_dict:
          GetData:
            id: 123
      when: check.is_valid

- name: Validate multiple endpoints
  hufschlaeger.soap_client.soap_validate:
    endpoint_url: "{{ item }}"
    timeout: 3
  loop:
    - "https://prod.api.example.com/soap"
    - "https://staging.api.example.com/soap"
    - "https://dev.api.example.com/soap"
  register: endpoints_check

- name: Performance check with response time
  hufschlaeger.soap_client.soap_validate:
    endpoint_url: "{{ soap_endpoint }}"
    timeout: 5
  register: perf_check
  failed_when: perf_check.response_time > 1000  # Fail if > 1 second
'''

RETURN = r'''
is_valid:
    description: Whether endpoint is valid and reachable
    returned: always
    type: bool
    sample: true
msg:
    description: Validation result message
    returned: always
    type: str
    sample: "Endpoint reachable; WSDL OK"
response_time:
    description: 
        - Response time in milliseconds
        - Total time for all validation checks
    returned: always
    type: float
    sample: 245.67
reachable:
    description: Whether endpoint URL is reachable
    returned: always
    type: bool
    sample: true
status_code:
    description: HTTP status code from validation request
    returned: when reachable
    type: int
    sample: 200
ssl_valid:
    description: Whether SSL certificate is valid
    returned: when validate_certs=true and reachable
    type: bool
    sample: true
wsdl_valid:
    description: Whether WSDL is valid and parseable
    returned: when check_wsdl=true
    type: bool
    sample: true
wsdl_operations:
    description: 
        - List of operations found in WSDL
        - Each operation name extracted from WSDL definitions
    returned: when check_wsdl=true and wsdl_valid=true
    type: list
    elements: str
    sample: ['GetCustomer', 'UpdateCustomer', 'DeleteCustomer', 'CreateOrder']
error_details:
    description: Detailed error information if validation failed
    returned: when not is_valid
    type: str
    sample: "SSL certificate verification failed"
changed:
    description: Whether any changes were made (always false for validation)
    returned: always
    type: bool
    sample: false
'''

from ansible.module_utils.basic import AnsibleModule
import time

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
    Endpoint,
    ValidateEndpointUseCase,
    ValidateEndpointCommand,
    HttpSoapRepository
  )

  HAS_SOAP_MODULE = True
  IMPORT_SOURCE = "collection"
except ImportError as collection_error:
  # Try local import (for development/testing)
  try:
    from ansible.module_utils.soap_module import (
      Endpoint,
      ValidateEndpointUseCase,
      ValidateEndpointCommand,
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
  """Main module execution function for endpoint validation"""

  module_args = dict(
    endpoint_url=dict(
      type='str',
      required=True,
      aliases=['endpoint', 'url']
    ),
    timeout=dict(type='int', required=False, default=10),
    validate_certs=dict(type='bool', required=False, default=True),
    check_wsdl=dict(type='bool', required=False, default=False),
    auth_type=dict(
      type='str',
      required=False,
      default='none',
      choices=['basic', 'digest', 'ntlm', 'none']
    ),
    username=dict(type='str', required=False, default=None),
    password=dict(type='str', required=False, default=None, no_log=True),
  )

  result = dict(
    changed=False,
    is_valid=False,
    msg='',
    response_time=0.0,
    reachable=False
  )

  module = AnsibleModule(
    argument_spec=module_args,
    supports_check_mode=True,
    required_together=[
      ['username', 'password']
    ],
    required_if=[
      ['auth_type', 'basic', ['username', 'password']],
      ['auth_type', 'digest', ['username', 'password']],
      ['auth_type', 'ntlm', ['username', 'password']],
    ]
  )

  # Check if SOAP module is available
  if not HAS_SOAP_MODULE:
    module.fail_json(
      msg='SOAP Module could not be imported',
      error=SOAP_MODULE_IMPORT_ERROR,
      hint='Ensure collection is installed: ansible-galaxy collection install hufschlaeger.soap_client',
      **result
    )

  if module.check_mode:
    result['msg'] = 'Check mode: validation would be performed for {}'.format(
      module.params['endpoint_url']
    )
    module.exit_json(**result)

  try:
    start_time = time.time()

    # Create endpoint entity
    endpoint_entity = Endpoint(
      url=module.params['endpoint_url'],
      auth_type=module.params.get('auth_type', 'none'),
      username=module.params.get('username'),
      password=module.params.get('password'),
      verify_ssl=module.params['validate_certs'],
      default_timeout=module.params['timeout'],
    )

    # Determine WSDL URL if WSDL check is requested
    wsdl_url = None
    if module.params['check_wsdl']:
      # Use endpoint URL as WSDL URL if it looks like a WSDL URL
      endpoint_url = module.params['endpoint_url']
      if isinstance(endpoint_url, str) and (
          'wsdl' in endpoint_url.lower() or endpoint_url.endswith('?wsdl')
      ):
        wsdl_url = endpoint_url

    # Create validation command
    command = ValidateEndpointCommand(
      endpoint=endpoint_entity,
      check_connectivity=True,
      check_wsdl=module.params['check_wsdl'],
      wsdl_url=wsdl_url
    )

    # Execute validation with repository
    repository = HttpSoapRepository(
      verify_ssl=module.params['validate_certs'],
      timeout=module.params['timeout']
    )

    try:
      use_case = ValidateEndpointUseCase(repository)
      validation_result = use_case.execute(command)
    finally:
      repository.close()

    end_time = time.time()

    # Build result
    result['is_valid'] = validation_result.is_valid
    result['reachable'] = validation_result.is_reachable
    result['response_time'] = (end_time - start_time) * 1000  # in milliseconds

    # Build message
    if validation_result.error_message:
      result['msg'] = validation_result.error_message
      result['error_details'] = validation_result.error_message
    else:
      message_parts = []
      message_parts.append(
        'Endpoint reachable' if validation_result.is_reachable
        else 'Endpoint not reachable'
      )
      if module.params['check_wsdl']:
        message_parts.append(
          'WSDL OK' if validation_result.has_wsdl
          else 'WSDL not available'
        )
      result['msg'] = '; '.join(message_parts)

    # Add WSDL-related fields
    if module.params['check_wsdl']:
      result['wsdl_valid'] = validation_result.has_wsdl
      if validation_result.wsdl_operations:
        result['wsdl_operations'] = validation_result.wsdl_operations

    # Add SSL validation result
    if module.params['validate_certs'] and validation_result.is_reachable:
      result['ssl_valid'] = True  # If we got here with validate_certs=True, SSL is valid

    # Add import source for debugging
    result['import_source'] = IMPORT_SOURCE

    module.exit_json(**result)

  except ConnectionError as ce:
    result['msg'] = f'Connection error: {str(ce)}'
    result['error_details'] = str(ce)
    result['is_valid'] = False
    module.exit_json(**result)

  except TimeoutError as te:
    result['msg'] = f'Timeout error: {str(te)}'
    result['error_details'] = str(te)
    result['is_valid'] = False
    module.exit_json(**result)

  except Exception as e:
    result['msg'] = f'Validation error: {str(e)}'
    result['error_details'] = str(e)
    result['is_valid'] = False
    # Use exit_json instead of fail_json to allow playbook to continue
    module.exit_json(**result)


def main():
  """Module entry point"""
  run_module()


if __name__ == '__main__':
  main()
