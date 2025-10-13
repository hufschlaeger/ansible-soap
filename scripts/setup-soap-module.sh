#!/bin/bash
# setup-soap-module.sh

set -e

echo "🚀 Setting up SOAP Module for Ansible..."

PROXY_URL=""
if [ ! -z "$PROXY" ]; then
    PROXY_URL="$PROXY"
    echo -e "${YELLOW}📡 Proxy detected for pip: $PROXY_URL${NC}"
fi

# Pip mit Proxy installieren, oder nicht...
pip_install_with_proxy() {
    if [ ! -z "$PROXY_URL" ]; then
        echo -e "${YELLOW}   Using proxy for pip: $PROXY_URL${NC}"
        pip install --proxy "$PROXY_URL" "$@"
    else
        pip install "$@"
    fi
}

# Projekt-Verzeichnis
PROJECT_DIR="ansible-soap-project"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Verzeichnisstruktur
echo "📁 Creating directory structure..."
mkdir -p library
mkdir -p module_utils/soap_module/{domain,application,infrastructure,presentation}
mkdir -p module_utils/soap_module/domain/{entities,value_objects,services,repositories}
mkdir -p module_utils/soap_module/application/{use_cases,dtos,mappers}
mkdir -p module_utils/soap_module/infrastructure/{adapters,repositories,factories}
mkdir -p playbooks

# __init__.py Dateien
echo "📝 Creating __init__.py files..."
find module_utils -type d -exec touch {}/__init__.py \;

# Python Dependencies
echo "📦 Installing Python dependencies..."
pip_install_with_proxy requests lxml requests-ntlm

# requirements.txt erstellen
cat > requirements.txt << 'EOF'
requests>=2.28.0
lxml>=4.9.0
requests-ntlm>=1.2.0
EOF

# Test-Playbook
cat > playbooks/test.yml << 'EOF'
---
- name: Test SOAP Module
  hosts: localhost
  gather_facts: false

  tasks:
    - name: Test NumberToWords Service
      soap_request:
        endpoint_url: https://www.dataaccess.com/webservicesserver/NumberConversion.wso
        soap_action: NumberToWords
        soap_version: "1.1"
        body_dict:
          ubiNum: "500"
        body_root_tag: NumberToWords
        namespace: http://www.dataaccess.com/webservicesserver/
      register: result

    - name: Show result
      debug:
        msg: "{{ result.body }}"
EOF

# ansible.cfg
cat > ansible.cfg << 'EOF'
[defaults]
inventory = inventory
library = ./library
module_utils = ./module_utils
host_key_checking = False
retry_files_enabled = False

[privilege_escalation]
become = False
EOF

# Inventory
cat > inventory << 'EOF'
[local]
localhost ansible_connection=local
EOF

# README
cat > README.md << 'EOF'
# Ansible SOAP Module Project

## Installation

```bash
pip install -r requirements.txt
```
EOF
