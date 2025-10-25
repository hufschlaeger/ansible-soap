#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Daniel Hufschläger <daniel@hufschlaeger.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: soap_validate
short_description: Validate SOAP endpoint connectivity
description:
    - Checks if a SOAP endpoint is reachable
    - Validates SSL certificates
    - Tests authentication if provided
    - Measures response time
    - Can optionally fetch and validate WSDL
version_added: "0.1.0"
options:
    endpoint:
        description: 
            - SOAP endpoint URL to validate
            - Can be WSDL URL or service endpoint
        required: true
        type: str
    timeout:
        description: Connection timeout in seconds
        required: false
        type: int
        default: 10
    validate_certs:
        description: 
            - Validate SSL certificates
            - Set to false for self-signed certificates
        required: false
        type: bool
        default: true
    check_wsdl:
        description:
            - Additionally check if WSDL is accessible
            - Endpoint URL should point to WSDL
        required: false
        type: bool
        default: false
    auth_type:
        description: Authentication type for validation
        required: false
        type: str
        choices: ['basic', 'digest', 'ntlm', 'none']
        default: 'none'
    username:
        description: Username for authentication
        required: false
        type: str
    password:
        description: Password for authentication
        required: false
        type: str
        no_log: true
requirements:
    - requests >= 2.25.0
author:
    - Daniel Hufschläger (@dhufe)
'''

EXAMPLES = r'''
- name: Simple endpoint validation
  hufschlaeger.soap_client.soap_validate:
    endpoint: "https://www.dataaccess.com/webservicesserver/NumberConversion.wso"
    timeout: 5
  register: validation

- name: Validate with SSL check disabled
  hufschlaeger.soap_client.soap_validate:
    endpoint: "https://dev.example.com/soap"
    validate_certs: false
    timeout: 10

- name: Validate WSDL accessibility
  hufschlaeger.soap_client.soap_validate:
    endpoint: "https://api.example.com/service?wsdl"
    check_wsdl: true
    timeout: 15
  register: wsdl_check

- name: Validate with authentication
  hufschlaeger.soap_client.soap_validate:
    endpoint: "https://api.example.com/soap"
    auth_type: basic
    username: "api_user"
    password: "{{ vault_password }}"
    timeout: 10

- name: Fail if endpoint is not reachable
  hufschlaeger.soap_client.soap_validate:
    endpoint: "{{ soap_endpoint }}"
  register: endpoint_check
  failed_when: not endpoint_check.is_valid

- name: Use validation in conditional
  block:
    - name: Check endpoint
      hufschlaeger.soap_client.soap_validate:
        endpoint: "{{ soap_endpoint }}"
      register: check

    - name: Proceed only if valid
      hufschlaeger.soap_client.soap_request:
        endpoint: "{{ soap_endpoint }}"
        body: "{{ soap_body }}"
      when: check.is_valid
'''

RETURN = r'''
is_valid:
    description: Whether endpoint is valid and reachable
    returned: always
    type: bool
    sample: true
message:
    description: Validation result message
    returned: always
    type: str
    sample: "Endpoint is reachable"
response_time:
    description: Response time in milliseconds
    returned: success
    type: float
    sample: 245.67
status_code:
    description: HTTP status code from validation request
    returned: success
    type: int
    sample: 200
ssl_valid:
    description: Whether SSL certificate is valid
    returned: when validate_certs=true
    type: bool
    sample: true
wsdl_valid:
    description: Whether WSDL is valid and parseable
    returned: when check_wsdl=true
    type: bool
    sample: true
wsdl_operations:
    description: List of operations found in WSDL
    returned: when check_wsdl=true and wsdl_valid=true
    type: list
    sample: ['GetCustomer', 'UpdateCustomer', 'DeleteCustomer']
'''

from ansible.module_utils.basic import AnsibleModule
import time

try:
  from ansible_collections.hufschlaeger.soap_client.plugins.module_utils.soap_module.application.use_cases.validate_endpoint_use_case import \
    ValidateEndpointUseCase
except ImportError:
  try:
    from ansible.module_utils.soap_module.application.use_cases.validate_endpoint_use_case import \
      ValidateEndpointUseCase
  except ImportError as e:
    raise ImportError(f"Could not import SOAP validation utilities: {e}")


def run_module():
  """Hauptfunktion des Validierungs-Moduls"""

  module_args = dict(
    endpoint=dict(type='str', required=True),
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
    message='',
    response_time=0.0
  )

  module = AnsibleModule(
    argument_spec=module_args,
    supports_check_mode=True,
    required_together=[
      ['username', 'password']
    ],
  )

  if module.check_mode:
    result['message'] = 'Check mode - validation skipped'
    module.exit_json(**result)

  try:
    start_time = time.time()

    # Use Case ausführen
    use_case = ValidateEndpointUseCase()
    validation_result = use_case.execute(
      endpoint=module.params['endpoint'],
      timeout=module.params['timeout'],
      validate_certs=module.params['validate_certs'],
      check_wsdl=module.params['check_wsdl'],
      auth_type=module.params['auth_type'],
      username=module.params['username'],
      password=module.params['password']
    )

    end_time = time.time()

    # Ergebnisse aufbereiten
    result['is_valid'] = validation_result.is_valid
    result['message'] = validation_result.message
    result['response_time'] = (end_time - start_time) * 1000  # in ms

    if hasattr(validation_result, 'status_code'):
      result['status_code'] = validation_result.status_code

    if hasattr(validation_result, 'ssl_valid'):
      result['ssl_valid'] = validation_result.ssl_valid

    if module.params['check_wsdl']:
      result['wsdl_valid'] = validation_result.wsdl_valid
      if validation_result.wsdl_valid and hasattr(validation_result, 'operations'):
        result['wsdl_operations'] = validation_result.operations

    module.exit_json(**result)

  except ConnectionError as ce:
    result['message'] = f'Connection error: {str(ce)}'
    result['is_valid'] = False
    module.exit_json(**result)

  except TimeoutError as te:
    result['message'] = f'Timeout error: {str(te)}'
    result['is_valid'] = False
    module.exit_json(**result)

  except Exception as e:
    result['message'] = f'Validation error: {str(e)}'
    result['is_valid'] = False
    module.fail_json(**result)


def main():
  """Einstiegspunkt"""
  run_module()


if __name__ == '__main__':
  main()
