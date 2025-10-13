#!/bin/bash
set -e

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🔧 Adding SOAP Module Files to Existing Project${NC}"
echo ""

# Prüfe ob wir im richtigen Verzeichnis sind
if [ ! -d "library" ] || [ ! -d "module_utils/soap_module" ]; then
    echo -e "${RED}❌ Error: library/ or module_utils/soap_module/ not found!${NC}"
    echo -e "${YELLOW}Please run this script from your Ansible project root.${NC}"
    exit 1
fi

# Prüfe ob schon Dateien existieren
if [ -f "library/soap_request.py" ]; then
    echo -e "${YELLOW}⚠️  Files already exist!${NC}"
    read -p "Overwrite? (y/N): " CONFIRM
    if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
        echo -e "${RED}Aborted.${NC}"
        exit 0
    fi
fi

echo -e "${YELLOW}📝 Creating module files...${NC}"
echo ""

# Die 3 Haupt-Module
echo "Creating library/soap_request.py..."
cat > library/soap_request.py << 'EOFMODULE'
#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: soap_request
short_description: Send SOAP requests
description: Sends SOAP requests to web services
options:
    endpoint_url:
        description: URL of the SOAP service
        required: true
        type: str
    soap_action:
        description: SOAP action to perform
        required: true
        type: str
'''

from ansible.module_utils.basic import AnsibleModule

def run_module():
    module_args = dict(
        endpoint_url=dict(type='str', required=True),
        soap_action=dict(type='str', required=True),
    )

    module = AnsibleModule(argument_spec=module_args)

    # TODO: Implement logic
    module.exit_json(changed=False, msg="Module needs implementation")

def main():
    run_module()

if __name__ == '__main__':
    main()
EOFMODULE

chmod +x library/soap_request.py

echo "Creating library/soap_validate.py..."
cat > library/soap_validate.py << 'EOFMODULE'
#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule

def run_module():
    module = AnsibleModule(argument_spec=dict(
        endpoint_url=dict(type='str', required=True)
    ))
    module.exit_json(changed=False, msg="Validation needs implementation")

def main():
    run_module()

if __name__ == '__main__':
    main()
EOFMODULE

chmod +x library/soap_validate.py

echo "Creating library/soap_batch.py..."
cat > library/soap_batch.py << 'EOFMODULE'
#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule

def run_module():
    module = AnsibleModule(argument_spec=dict(
        requests=dict(type='list', required=True)
    ))
    module.exit_json(changed=False, msg="Batch needs implementation")

def main():
    run_module()

if __name__ == '__main__':
    main()
EOFMODULE

chmod +x library/soap_batch.py

# __init__.py Dateien
touch module_utils/soap_module/__init__.py
touch module_utils/soap_module/domain/__init__.py
touch module_utils/soap_module/application/__init__.py
touch module_utils/soap_module/infrastructure/__init__.py
touch module_utils/soap_module/presentation/__init__.py

echo ""
echo -e "${GREEN}✅ Basic module files created!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Test basic structure:"
echo "   ${GREEN}ansible-playbook playbooks/test.yml${NC}"
echo ""
echo "2. Modules are minimal stubs - implement logic as needed"
echo ""
