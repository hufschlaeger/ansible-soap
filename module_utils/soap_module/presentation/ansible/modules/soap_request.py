#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Your Name <your.email@example.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: soap_request
short_description: Sendet SOAP-Requests an Webservices
version_added: "1.0.0"
description:
    - Sendet SOAP-Requests an SOAP-Webservices
    - Unterstützt SOAP 1.1 und 1.2
    - Verschiedene Authentifizierungsmethoden
    - Response-Transformation und Datenextraktion
    - Caching und Retry-Mechanismen
options:
    endpoint_url:
        description:
            - URL des SOAP-Endpoints
        required: true
        type: str
    soap_action:
        description:
            - SOAP Action Header-Wert
            - Wird für Request-Routing verwendet
        required: true
        type: str
    body:
        description:
            - SOAP Body als XML-String
            - Entweder body oder body_dict muss angegeben werden
        required: false
        type: str
    body_dict:
        description:
            - SOAP Body als Dictionary
            - Wird automatisch zu XML konvertiert
            - Entweder body oder body_dict muss angegeben werden
        required: false
        type: dict
    body_root_tag:
        description:
            - Root-Tag für body_dict Konvertierung
        required: false
        type: str
        default: "Request"
    namespace:
        description:
            - XML Namespace für den SOAP Body
        required: false
        type: str
    namespace_prefix:
        description:
            - Prefix für den Namespace
        required: false
        type: str
        default: "ns"
    soap_version:
        description:
            - SOAP Version (1.1 oder 1.2)
        required: false
        type: str
        default: "1.1"
        choices: ['1.1', '1.2']
    soap_header:
        description:
            - Optionaler SOAP Header als XML-String
        required: false
        type: str
    headers:
        description:
            - Zusätzliche HTTP-Header als Dictionary
        required: false
        type: dict
    timeout:
        description:
            - Timeout in Sekunden
        required: false
        type: int
        default: 30
    auth_type:
        description:
            - Authentifizierungstyp
        required: false
        type: str
        default: "none"
        choices: ['none', 'basic', 'digest', 'ntlm', 'certificate']
    username:
        description:
            - Username für Authentifizierung
            - Erforderlich für basic, digest, ntlm
        required: false
        type: str
    password:
        description:
            - Password für Authentifizierung
            - Erforderlich für basic, digest, ntlm
        required: false
        type: str
        no_log: true
    cert_path:
        description:
            - Pfad zum Client-Zertifikat
            - Erforderlich für certificate Auth
        required: false
        type: path
    key_path:
        description:
            - Pfad zum Private Key
            - Optional für certificate Auth
        required: false
        type: path
    validate_certs:
        description:
            - Ob SSL-Zertifikate validiert werden sollen
        required: false
        type: bool
        default: true
    use_cache:
        description:
            - Ob Response-Caching verwendet werden soll
        required: false
        type: bool
        default: false
    max_retries:
        description:
            - Maximale Anzahl von Wiederholungen bei Fehler
        required: false
        type: int
        default: 0
    extract_xpath:
        description:
            - XPath-Ausdruck zum Extrahieren von Daten aus der Response
        required: false
        type: str
    strip_namespaces:
        description:
            - Ob Namespaces vor XPath-Extraktion entfernt werden sollen
        required: false
        type: bool
        default: false
    validate:
        description:
            - Ob Request/Response validiert werden sollen
        required: false
        type: bool
        default: true

author:
    - Your Name (@yourhandle)
'''

EXAMPLES = r'''
# Einfacher SOAP Request
- name: Get user information
  soap_request:
    endpoint_url: https://api.example.com/soap
    soap_action: GetUser
    body_dict:
      UserId: "123"
    body_root_tag: GetUser
    namespace: http://example.com/api

# Mit Basic Authentication
- name: SOAP Request with auth
  soap_request:
    endpoint_url: https://secure.example.com/soap
    soap_action: UpdateUser
    auth_type: basic
    username: admin
    password: secret
    body: |
      <UpdateUser>
        <UserId>123</UserId>
        <Name>John Doe</Name>
      </UpdateUser>

# Mit XPath-Extraktion
- name: Extract specific data
  soap_request:
    endpoint_url: https://api.example.com/soap
    soap_action: GetUserList
    body_dict:
      MaxResults: 10
    extract_xpath: .//User/Name
    strip_namespaces: true
  register: result

- name: Show extracted names
  debug:
    var: result.extracted_data

# Mit Retry bei Fehler
- name: Reliable SOAP Request
  soap_request:
    endpoint_url: https://unreliable.example.com/soap
    soap_action: GetData
    body_dict:
      Id: "456"
    max_retries: 3
    timeout: 60

# Mit Client-Zertifikat
- name: SOAP Request with certificate
  soap_request:
    endpoint_url: https://secure.example.com/soap
    soap_action: SecureOperation
    auth_type: certificate
    cert_path: /path/to/client.crt
    key_path: /path/to/client.key
    body_dict:
      Action: "query"

# SOAP 1.2 mit Custom Header
- name: SOAP 1.2 Request
  soap_request:
    endpoint_url: https://api.example.com/soap12
    soap_action: http://example.com/GetData
    soap_version: "1.2"
    headers:
      X-Custom-Header: "value"
    body_dict:
      Query: "test"
'''

RETURN = r'''
success:
    description: Ob der Request erfolgreich war
    type: bool
    returned: always
    sample: true
status_code:
    description: HTTP Status Code
    type: int
    returned: always
    sample: 200
body:
    description: Response Body als String
    type: str
    returned: always
    sample: "<soap:Envelope>...</soap:Envelope>"
headers:
    description: Response Headers
    type: dict
    returned: always
    sample:
        Content-Type: "text/xml; charset=utf-8"
        Content-Length: "1234"
response_time_ms:
    description: Response-Zeit in Millisekunden
    type: float
    returned: always
    sample: 250.5
extracted_data:
    description: Extrahierte Daten (wenn extract_xpath angegeben)
    type: raw
    returned: when extract_xpath is provided
    sample: ["John", "Jane", "Bob"]
error_message:
    description: Fehlermeldung bei Fehler
    type: str
    returned: on failure
    sample: "Connection timeout"
validation_errors:
    description: Validierungsfehler
    type: list
    returned: when validation fails
    sample: ["Invalid endpoint URL", "Missing required field"]
changed:
    description: Ob Änderungen vorgenommen wurden
    type: bool
    returned: always
    sample: true
'''

from ansible.module_utils.basic import AnsibleModule

# Import der SOAP Module Komponenten
try:
    from ansible.module_utils.soap_module.application.dtos.soap_request_dto import SoapRequestDTO
    from ansible.module_utils.soap_module.application.mappers.dto_mapper import DtoMapper
    from ansible.module_utils.soap_module.application.use_cases.send_soap_request_use_case import (
        SendSoapRequestUseCase
    )
    from ansible.module_utils.soap_module.infrastructure.repositories.http_soap_repository import (
        HttpSoapRepository
    )
    HAS_SOAP_MODULE = True
except ImportError as e:
    HAS_SOAP_MODULE = False
    SOAP_MODULE_IMPORT_ERROR = str(e)


def run_module():
    """Hauptfunktion des Ansible-Moduls"""

    # Modul-Argumente definieren
    module_args = dict(
        endpoint_url=dict(type='str', required=True),
        soap_action=dict(type='str', required=True),
        body=dict(type='str', required=False),
        body_dict=dict(type='dict', required=False),
        body_root_tag=dict(type='str', required=False, default='Request'),
        namespace=dict(type='str', required=False),
        namespace_prefix=dict(type='str', required=False, default='ns'),
        soap_version=dict(type='str', required=False, default='1.1',
                          choices=['1.1', '1.2']),
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

    # Result-Dictionary initialisieren
    result = dict(
        changed=False,
        success=False,
        status_code=0,
        body='',
    )

    # Modul initialisieren
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        mutually_exclusive=[
            ['body', 'body_dict']
        ],
        required_one_of=[
            ['body', 'body_dict']
        ],
        required_if=[
            ['auth_type', 'basic', ['username', 'password']],
            ['auth_type', 'digest', ['username', 'password']],
            ['auth_type', 'ntlm', ['username', 'password']],
            ['auth_type', 'certificate', ['cert_path']],
        ]
    )

    # Prüfen ob SOAP Module verfügbar ist
    if not HAS_SOAP_MODULE:
        module.fail_json(
            msg='SOAP Module konnte nicht importiert werden',
            error=SOAP_MODULE_IMPORT_ERROR
        )

    # Check Mode
    if module.check_mode:
        module.exit_json(**result)

    try:
        # DTO aus Modul-Parametern erstellen
        request_dto = SoapRequestDTO(
            endpoint_url=module.params['endpoint_url'],
            soap_action=module.params['soap_action'],
            body=module.params.get('body'),
            body_dict=module.params.get('body_dict'),
            body_root_tag=module.params['body_root_tag'],
            namespace=module.params.get('namespace'),
            namespace_prefix=module.params['namespace_prefix'],
            soap_version=module.params['soap_version'],
            soap_header=module.params.get('soap_header'),
            headers=module.params.get('headers'),
            timeout=module.params['timeout'],
            auth_type=module.params['auth_type'],
            username=module.params.get('username'),
            password=module.params.get('password'),
            cert_path=module.params.get('cert_path'),
            key_path=module.params.get('key_path'),
            validate=module.params['validate'],
            use_cache=module.params['use_cache'],
            max_retries=module.params['max_retries'],
            extract_xpath=module.params.get('extract_xpath'),
            strip_namespaces=module.params['strip_namespaces'],
        )

        # Input validieren
        is_valid, error_message = request_dto.validate_input()
        if not is_valid:
            module.fail_json(
                msg='Input-Validierung fehlgeschlagen',
                error=error_message,
                **result
            )

        # Repository und Use Case initialisieren
        repository = HttpSoapRepository(
            verify_ssl=module.params['validate_certs'],
            timeout=module.params['timeout']
        )
        use_case = SendSoapRequestUseCase(repository)

        # DTO zu Command mappen
        command = DtoMapper.dto_to_command(request_dto)

        # Use Case ausführen
        use_case_result = use_case.execute(command)

        # Result zu DTO mappen
        response_dto = DtoMapper.result_to_dto(use_case_result)

        # Result aktualisieren
        result.update(response_dto.to_dict())
        result['changed'] = use_case_result.success

        # Bei Fehler fail_json aufrufen
        if not use_case_result.success:
            module.fail_json(
                msg='SOAP Request fehlgeschlagen',
                **result
            )

        # Repository aufräumen
        repository.close()

    except Exception as e:
        module.fail_json(
            msg=f'Unerwarteter Fehler: {str(e)}',
            exception=str(e),
            **result
        )

    # Erfolgreiche Ausführung
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
