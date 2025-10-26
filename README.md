# Ansible Collection — hufschlaeger.soap_client

[![Ansible Galaxy](https://img.shields.io/badge/Ansible%20Galaxy-hufschlaeger.soap__client-1f6feb?logo=ansible)](https://galaxy.ansible.com/hufschlaeger/soap_client)
[![License: GPL-2.0-or-later](https://img.shields.io/badge/License-GPL--2.0--or--later-0aa60d.svg)](#license)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-3776ab?logo=python&logoColor=white)](requirements.txt)

Interact with SOAP services from Ansible — validate endpoints/WSDLs, send requests, and run batches with ease.

- Validate endpoints and WSDLs
- Send single SOAP requests
- Execute batches of SOAP requests in sequence or in parallel

The collection is designed to be simple to adopt in existing playbooks and comes with runnable examples.

## Table of contents
- [Requirements](#requirements)
- [Installation](#installation)
- [Included content](#included-content)
- [Quick start — run an example](#quick-start--run-an-example)
- [Usage snippets](#usage-snippets)
- [Configuration notes](#configuration-notes)
- [Development and testing](#development-and-testing)
- [Contributing](#contributing)
- [Links](#links)
- [License](#license)

## Requirements
- Ansible >= 2.9
- Python 3.8+ (recommended)
- Python packages (install via requirements.txt):
  - requests>=2.25.0
  - requests-ntlm (for NTLM auth)
  - urllib3

Install the Python dependencies locally if you plan to run the example playbooks:

```bash
pip install -r requirements.txt
```

## Installation
Install the collection from Ansible Galaxy:

```bash
ansible-galaxy collection install hufschlaeger.soap_client
```

Alternatively, use the fully-qualified collection name (FQCN) in your playbooks without installing globally by setting a collection path in ansible.cfg or by using the provided inventory/ansible.cfg.

## Included content
Modules / Action plugins provided by this collection:
- soap_validate: Validate SOAP endpoint reachability, TLS, optional WSDL fetch and operation listing
- soap_request: Send a single SOAP request (supports XML body or body_dict to build XML, headers, auth, retries)
- soap_batch: Run multiple SOAP requests sequentially or in parallel with shared options

You can call them via FQCN, e.g. hufschlaeger.soap_client.soap_validate.

## Quick start — run an example
The repository contains ready-to-run playbooks under playbooks/examples.

Validation examples
- Basic endpoint validation:
    ansible-playbook playbooks/examples/validate/Validate_Basic.yml -vv

- WSDL validation and operations listing:
    ansible-playbook playbooks/examples/validate/Validate_WSDL.yml -vv

- Authenticated validation + conditional request:
    ansible-playbook playbooks/examples/validate/Validate_Auth_and_Conditional.yml -vv

Request and batch examples
- SOAP Request examples: playbooks/examples/request
- SOAP Batch examples: playbooks/examples/batch

Tip: to avoid typing the FQCN repeatedly, you can declare collections at the play level:

  collections:
    - hufschlaeger.soap_client

Then call modules by short name (soap_validate, soap_request, soap_batch).

## Usage snippets
- Validate an endpoint quickly

  - name: Validate endpoint
    hufschlaeger.soap_client.soap_validate:
      endpoint: "https://example.com/service"
      timeout: 5

- Send a SOAP request using body_dict (XML is auto-built)

  - name: Convert number to words
    hufschlaeger.soap_client.soap_request:
      endpoint_url: "https://www.dataaccess.com/webservicesserver/NumberConversion.wso"
      soap_action: "http://www.dataaccess.com/webservicesserver/NumberConversion.wso/NumberToWords"
      namespace: "http://www.dataaccess.com/webservicesserver/"
      body_root_tag: "NumberToWords"
      body_dict:
        ubiNum: 42

- Run a small batch

  - name: Batch of SOAP requests
    hufschlaeger.soap_client.soap_batch:
      parallel: true
      max_workers: 4
      requests:
        - endpoint_url: "https://example.com/service1"
          soap_action: "urn:Action1"
          body: "<ns:Action1 xmlns:ns=\"urn:ns\"/>"
        - endpoint_url: "https://example.com/service2"
          soap_action: "urn:Action2"
          body: "<ns:Action2 xmlns:ns=\"urn:ns\"/>"

Refer to the example playbooks for full, working configurations.

## Configuration notes
- TLS certificate validation is enabled by default. You can disable it per request with validate_certs: false (not recommended for production).
- Authentication: Basic auth, NTLM (via requests-ntlm), and client certificates are supported by the request module. See module docs and examples.
- Timeouts, retries, headers, SOAP version, and SOAP headers are supported in soap_request; soap_batch forwards these options per request.

## Development and testing
- Install Python deps: pip install -r requirements.txt
- Run example playbooks (use -vv for more details)
- If you use a virtualenv, ensure ansible can load the collection (ansible-galaxy collection list should show hufschlaeger.soap_client)

## Contributing
We welcome contributions! Here are a few good ways to get started:

- Add or enhance actions/modules
  - New action plugins similar to soap_request and soap_batch, or improvements to existing ones
  - Extend soap_request/soap_batch with new options (timeouts, auth methods, headers, XML helpers)
  - Keep naming, parameters, and return structure consistent with existing actions

- Provide example playbooks
  - Place request examples under playbooks/examples/request
  - Place batch examples under playbooks/examples/batch
  - Place validation examples under playbooks/examples/validate
  - Keep examples runnable with sensible defaults or public endpoints

- Improve docs and tests
  - Update README sections with any new options/behaviors
  - Add module/action DOCUMENTATION strings if you add parameters
  - Contribute tests or minimal playbooks under tests/ and playbooks/examples/

Development workflow
- Create a feature branch
- Install deps: pip install -r requirements.txt
- Run the example playbooks locally to validate changes
- Open a PR on GitHub with a concise description, example usage, and any breaking-change notes
- For bugs, please also open an issue linking the PR

Code style
- Follow the style used in existing action plugins (see plugins/action/soap_request.py and plugins/action/soap_batch.py)
- Prefer clear error messages and consistent parameter templating/validation
- Keep user-facing names stable; deprecate gradually when needed

## Links
- Project repository: https://github.com/hufschlaeger/ansible-soap/
- Documentation: https://hufschlaeger.net/projects/devops/ansible-soap-module/
- Issue tracker: https://github.com/hufschlaeger/ansible-soap/issues

## License
GPL-2.0-or-later
