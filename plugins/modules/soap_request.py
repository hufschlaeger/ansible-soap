# !/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Daniel Hufschläger <daniel@hufschlaeger.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: soap_request
short_description: Send SOAP requests to web services
description:
    - Sends SOAP requests to SOAP 1.1/1.2 web services
    - Supports various authentication methods (Basic, Digest, NTLM, Certificate)
    - Supports body as XML string or Python dict
    - XPath extraction and data transformation
    - Response caching and retry mechanisms
version_added: "0.1.0"
options:
    endpoint_url:
        description: SOAP endpoint URL
        required: true
        type: str
    soap_action:
        description: SOAP Action header value
        required: true
        type: str
    body:
        description: SOAP body as XML string (use body OR body_dict)
        required: false
        type: str
    body_dict:
        description: SOAP body as Python dictionary (use body OR body_dict)
        required: false
        type: dict
    body_root_tag:
        description: Root tag name when using body_dict
        required: false
        type: str
        default: "Request"
    namespace:
        description: XML namespace for SOAP body
        required: false
        type: str
    namespace_prefix:
        description: Prefix for namespace
        required: false
        type: str
        default: "ns"
    soap_version:
        description: SOAP protocol version
        required: false
        type: str
        default: "1.1"
        choices: ['1.1', '1.2']
    soap_header:
        description: Optional SOAP header as XML string
        required: false
        type: str
    headers:
        description: Additional HTTP headers
        required: false
        type: dict
    timeout:
        description: Request timeout in seconds
        required: false
        type: int
        default: 30
    auth_type:
        description: Authentication method
        required: false
        type: str
        default: "none"
        choices: ['none', 'basic', 'digest', 'ntlm', 'certificate']
    username:
        description: Username for authentication
        required: false
        type: str
    password:
        description: Password for authentication
        required: false
        type: str
        no_log: true
    cert_path:
        description: Path to client certificate file
        required: false
        type: path
    key_path:
        description: Path to private key file
        required: false
        type: path
    validate_certs:
        description: Validate SSL certificates
        required: false
        type: bool
        default: true
    use_cache:
        description: Use response caching
        required: false
        type: bool
        default: false
    max_retries:
        description: Maximum number of retries on failure
        required: false
        type: int
        default: 0
    extract_xpath:
        description: XPath expression to extract data from response
        required: false
        type: str
    strip_namespaces:
        description: Strip namespaces before XPath extraction
        required: false
        type: bool
        default: false
    validate:
        description: Validate request and response
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
- name: Simple SOAP request with dict body
  hufschlaeger.soap_client.soap_request:
    endpoint_url: "https://www.dataaccess.com/webservicesserver/NumberConversion.wso"
    soap_action: "NumberToWords"
    body_dict:
      NumberToWords:
        ubiNum: 42
    namespace: "http://www.dataaccess.com/webservicesserver/"

- name: SOAP request with XML string body
  hufschlaeger.soap_client.soap_request:
    endpoint_url: "https://api.example.com/soap"
    soap_action: "GetCustomer"
    body: |
      <GetCustomer xmlns="http://example.com/">
        <customerId>12345</customerId>
      </GetCustomer>

- name: SOAP request with basic authentication
  hufschlaeger.soap_client.soap_request:
    endpoint_url: "https://api.example.com/soap"
    soap_action: "GetOrders"
    auth_type: basic
    username: "api_user"
    password: "{{ vault_password }}"
    body_dict:
      GetOrders:
        customerId: "12345"

- name: Extract data with XPath
  hufschlaeger.soap_client.soap_request:
    endpoint_url: "https://api.example.com/soap"
    soap_action: "GetUserList"
    body_dict:
      GetUserList:
        maxResults: 10
    extract_xpath: ".//User/Name"
    strip_namespaces: true
  register: result

- name: SOAP request with retries
  hufschlaeger.soap_client.soap_request:
    endpoint_url: "https://api.example.com/soap"
    soap_action: "GetData"
    body_dict:
      GetData:
        id: "456"
    max_retries: 3
    timeout: 60

- name: SOAP request with client certificate
  hufschlaeger.soap_client.soap_request:
    endpoint_url: "https://secure.example.com/soap"
    soap_action: "SecureOperation"
    auth_type: certificate
    cert_path: /path/to/client.crt
    key_path: /path/to/client.key
    body_dict:
      SecureOperation:
        action: "query"
'''

RETURN = r'''
success:
    description: Whether the request was successful
    type: bool
    returned: always
    sample: true
status_code:
    description: HTTP status code
    type: int
    returned: always
    sample: 200
body:
    description: Response body as string
    type: str
    returned: always
    sample: "<soap:Envelope>...</soap:Envelope>"
headers:
    description: Response headers
    type: dict
    returned: always
response_time_ms:
    description: Response time in milliseconds
    type: float
    returned: always
    sample: 250.5
extracted_data:
    description: Extracted data when extract_xpath is used
    type: raw
    returned: when extract_xpath is provided
error_message:
    description: Error message on failure
    type: str
    returned: on failure
validation_errors:
    description: Validation errors
    type: list
    returned: when validation fails
changed:
    description: Whether changes were made
    type: bool
    returned: always
    sample: true
'''

from ansible.module_utils.basic import AnsibleModule

try:
  from ansible_collections.hufschlaeger.soap_client.plugins.module_utils.soap_module.application.dtos.soap_request_dto import \
    SoapRequestDTO
  from ansible_collections.hufschlaeger.soap_client.plugins.module_utils.soap_module.application.mappers.dto_mappers import \
    DtoMapper
  from ansible_collections.hufschlaeger.soap_client.plugins.module_utils.soap_module.application.use_cases.send_soap_request_use_case import \
    SendSoapRequestUseCase
  from ansible_collections.hufschlaeger.soap_client.plugins.module_utils.soap_module.infrastructure.repositories.http_soap_repository import \
    HttpSoapRepository

  HAS_SOAP_MODULE = True
except ImportError:
  try:
    from ansible.module_utils.soap_module.application.dtos.soap_request_dto import SoapRequestDTO
    from ansible.module_utils.soap_module.application.mappers.dto_mappers import DtoMapper
    from ansible.module_utils.soap_module.application.use_cases.send_soap_request_use_case import SendSoapRequestUseCase
    from ansible.module_utils.soap_module.infrastructure.repositories.http_soap_repository import HttpSoapRepository

    HAS_SOAP_MODULE = True
  except ImportError as e:
    HAS_SOAP_MODULE = False
    SOAP_MODULE_IMPORT_ERROR = str(e)


def run_module():
  """Main module function"""

  module_args = dict(
    endpoint_url=dict(type='str', required=True),
    soap_action=dict(type='str', required=True),
    body=dict(type='str', required=False),
    body_dict=dict(type='dict', required=False),
    body_root_tag=dict(type='str', required=False, default='Request'),
    namespace=dict(type='str', required=False),
    namespace_prefix=dict(type='str', required=False, default='ns'),
    skip_request_wrapper=dict(type='bool', default=False),
    soap_version=dict(type='str', required=False, default='1.1', choices=['1.1', '1.2']),
    soap_header=dict(type='str', required=False),
    headers=dict(type='dict', required=False),
    timeout=dict(type='int', required=False, default=30),
    auth_type=dict(type='str', required=False, default='none',
                   choices=['none', 'basic', 'digest', 'ntlm', 'certificate']),
    username=dict(type='str', required=False),
    password=dict(type='str', required=False, no_log=True),
    cert_path=dict(type='path', required=False),
    key_path=dict(type='path', required=False),
    validate_certs=dict(type='bool', required=False, default=True),
    use_cache=dict(type='bool', required=False, default=False),
    max_retries=dict(type='int', required=False, default=0),
    extract_xpath=dict(type='str', required=False),
    strip_namespaces=dict(type='bool', required=False, default=False),
    validate=dict(type='bool', required=False, default=True),
  )

  result = dict(
    changed=False,
    success=False,
    status_code=0,
    body='',
  )

  module = AnsibleModule(
    argument_spec=module_args,
    supports_check_mode=True,
    mutually_exclusive=[['body', 'body_dict']],
    required_one_of=[['body', 'body_dict']],
    required_if=[
      ['auth_type', 'basic', ['username', 'password']],
      ['auth_type', 'digest', ['username', 'password']],
      ['auth_type', 'ntlm', ['username', 'password']],
      ['auth_type', 'certificate', ['cert_path']],
    ]
  )

  if not HAS_SOAP_MODULE:
    module.fail_json(
      msg='SOAP Module could not be imported',
      error=SOAP_MODULE_IMPORT_ERROR
    )

  if module.check_mode:
    module.exit_json(**result)

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
      module.fail_json(
        msg='Input validation failed',
        error=error_message,
        **result
      )

    repository = HttpSoapRepository(
      verify_ssl=module.params['validate_certs'],
      timeout=module.params['timeout']
    )
    use_case = SendSoapRequestUseCase(repository)

    command = DtoMapper.dto_to_command(request_dto)
    use_case_result = use_case.execute(command)
    response_dto = DtoMapper.result_to_dto(use_case_result)

    result.update(response_dto.to_dict())
    result['changed'] = use_case_result.success

    if not use_case_result.success:
      module.fail_json(msg='SOAP request failed', **result)

    repository.close()

  except Exception as e:
    module.fail_json(
      msg=f'Unexpected error: {str(e)}',
      exception=str(e),
      **result
    )

  module.exit_json(**result)


def main():
  run_module()


if __name__ == '__main__':
  main()
