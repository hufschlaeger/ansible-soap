#!/bin/bash
set -e

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Proxy Detection
PROXY_URL=""
if [ ! -z "$PROXY" ]; then
    PROXY_URL="$PROXY"
    echo -e "${YELLOW}📡 Proxy detected: $PROXY_URL${NC}"
fi

# Proxy für verschiedene Tools konfigurieren
configure_proxy() {
    if [ ! -z "$PROXY_URL" ]; then
        export http_proxy="$PROXY_URL"
        export https_proxy="$PROXY_URL"
        export HTTP_PROXY="$PROXY_URL"
        export HTTPS_PROXY="$PROXY_URL"

        # Für pip
        export PIP_PROXY="$PROXY_URL"

        # No-Proxy für localhost
        export no_proxy="localhost,127.0.0.1"
        export NO_PROXY="localhost,127.0.0.1"

        echo -e "${GREEN}✓ Proxy configured for http_proxy, https_proxy, pip${NC}"
    fi
}

# Git Proxy konfigurieren
configure_git_proxy() {
    if [ ! -z "$PROXY_URL" ]; then
        git config --global http.proxy "$PROXY_URL"
        git config --global https.proxy "$PROXY_URL"
        echo -e "${GREEN}✓ Git proxy configured${NC}"
    fi
}

# Pip mit Proxy installieren
pip_install_with_proxy() {
    if [ ! -z "$PROXY_URL" ]; then
        pip install --proxy "$PROXY_URL" "$@"
    else
        pip install "$@"
    fi
}

# URL testen (mit Proxy wenn gesetzt)
test_url() {
    local url=$1
    if [ ! -z "$PROXY_URL" ]; then
        curl -x "$PROXY_URL" --connect-timeout 5 -s -o /dev/null -w "%{http_code}" "$url"
    else
        curl --connect-timeout 5 -s -o /dev/null -w "%{http_code}" "$url"
    fi
}

echo -e "${GREEN}🚀 Ansible SOAP Module - Setup Script${NC}"
echo ""

# Proxy konfigurieren
configure_proxy

# Projekt-Namen abfragen
read -p "Enter project name (default: ansible-soap-project): " PROJECT_NAME
PROJECT_NAME=${PROJECT_NAME:-ansible-soap-project}
PROJECT_DIR="./$PROJECT_NAME"

# Prüfe ob Verzeichnis existiert
if [ -d "$PROJECT_DIR" ]; then
    echo -e "${RED}❌ Directory $PROJECT_DIR already exists!${NC}"
    read -p "Remove and recreate? (y/N): " RECREATE
    if [ "$RECREATE" = "y" ] || [ "$RECREATE" = "Y" ]; then
        rm -rf "$PROJECT_DIR"
    else
        exit 1
    fi
fi

echo -e "${YELLOW}📁 Creating project structure...${NC}"

# Verzeichnisstruktur erstellen
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

mkdir -p library
mkdir -p module_utils/soap_module/{domain,application,infrastructure,presentation}
mkdir -p module_utils/soap_module/domain/{entities,value_objects,services,repositories}
mkdir -p module_utils/soap_module/application/{use_cases,dtos,mappers}
mkdir -p module_utils/soap_module/infrastructure/{adapters,repositories,factories}
mkdir -p module_utils/soap_module/presentation/ansible
mkdir -p playbooks
mkdir -p group_vars
mkdir -p host_vars

echo -e "${GREEN}✓ Directory structure created${NC}"

# Python Dependencies mit Proxy
echo -e "${YELLOW}📦 Creating requirements.txt...${NC}"
cat > requirements.txt << 'EOF'
# Core dependencies
ansible>=2.9
requests>=2.28.0
lxml>=4.9.0

# Authentication
requests-ntlm>=1.2.0

# Optional but recommended
PyYAML>=6.0
jinja2>=3.1.0

# Development (optional)
pytest>=7.0.0
pytest-cov>=4.0.0
black>=22.0.0
flake8>=5.0.0
EOF

echo -e "${GREEN}✓ requirements.txt created${NC}"

# Python Virtual Environment
echo -e "${YELLOW}🐍 Setting up Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

echo -e "${YELLOW}📦 Installing Python packages...${NC}"
if [ ! -z "$PROXY_URL" ]; then
    echo -e "${YELLOW}   Using proxy: $PROXY_URL${NC}"
fi

pip_install_with_proxy --upgrade pip
pip_install_with_proxy -r requirements.txt

echo -e "${GREEN}✓ Python packages installed${NC}"

# Ansible Configuration
echo -e "${YELLOW}⚙️  Creating ansible.cfg...${NC}"
cat > ansible.cfg << 'EOF'
[defaults]
inventory = inventory
library = ./library
module_utils = ./module_utils
host_key_checking = False
retry_files_enabled = False
collections_paths = ./collections
roles_path = ./roles
deprecation_warnings = False
stdout_callback = yaml
bin_ansible_callbacks = True

[privilege_escalation]
become = False

[inventory]
enable_plugins = host_list, yaml, ini, auto
EOF

# Inventory
cat > inventory << 'EOF'
[local]
localhost ansible_connection=local ansible_python_interpreter=python3

[soap_targets]
# Add your SOAP service hosts here
# example-host ansible_host=soap.example.com
EOF

# Proxy-spezifische Ansible-Config
if [ ! -z "$PROXY_URL" ]; then
    echo -e "${YELLOW}🔧 Adding proxy configuration to ansible.cfg...${NC}"
    cat >> ansible.cfg << EOF

[defaults]
# Proxy configuration
http_proxy = $PROXY_URL
https_proxy = $PROXY_URL
EOF

    # Environment file für Proxy
    cat > proxy.env << EOF
# Proxy Environment Variables
export http_proxy="$PROXY_URL"
export https_proxy="$PROXY_URL"
export HTTP_PROXY="$PROXY_URL"
export HTTPS_PROXY="$PROXY_URL"
export no_proxy="localhost,127.0.0.1"
export NO_PROXY="localhost,127.0.0.1"
EOF
    chmod +x proxy.env
    echo -e "${GREEN}✓ Proxy configuration added${NC}"
    echo -e "${YELLOW}💡 To use proxy in your shell: source proxy.env${NC}"
fi

# Test Playbook mit Proxy-Hinweis
echo -e "${YELLOW}📝 Creating test playbook...${NC}"
cat > playbooks/test.yml << 'EOF'
---
- name: Test SOAP Module
  hosts: localhost
  gather_facts: false

  vars:
    # Falls Proxy benötigt wird, hier konfigurieren
    # soap_proxy: "http://proxy.example.com:8080"

  tasks:
    - name: Test Public SOAP Service
      soap_request:
        endpoint_url: https://www.dataaccess.com/webservicesserver/NumberConversion.wso
        soap_action: NumberToWords
        soap_version: "1.1"
        body_dict:
          ubiNum: "500"
        body_root_tag: NumberToWords
        namespace: http://www.dataaccess.com/webservicesserver/
        timeout: 30
        # proxy: "{{ soap_proxy | default(omit) }}"
      register: result

    - name: Show result
      debug:
        msg: "{{ result.body }}"

    - name: Validate endpoint
      soap_validate:
        endpoint_url: https://www.dataaccess.com/webservicesserver/NumberConversion.wso
        timeout: 10
      register: validation

    - name: Show validation
      debug:
        var: validation
EOF

# Test mit Proxy-Unterstützung
cat > playbooks/test_with_proxy.yml << 'EOF'
---
- name: Test SOAP Module with Proxy
  hosts: localhost
  gather_facts: false

  environment:
    http_proxy: "{{ lookup('env', 'http_proxy') }}"
    https_proxy: "{{ lookup('env', 'https_proxy') }}"

  tasks:
    - name: Show proxy settings
      debug:
        msg:
          - "HTTP Proxy: {{ lookup('env', 'http_proxy') | default('Not set') }}"
          - "HTTPS Proxy: {{ lookup('env', 'https_proxy') | default('Not set') }}"

    - name: Test with proxy
      soap_request:
        endpoint_url: https://www.dataaccess.com/webservicesserver/NumberConversion.wso
        soap_action: NumberToWords
        soap_version: "1.1"
        body_dict:
          ubiNum: "42"
        body_root_tag: NumberToWords
        namespace: http://www.dataaccess.com/webservicesserver/
        timeout: 30
      register: result

    - name: Show result
      debug:
        var: result
EOF

echo -e "${GREEN}✓ Test playbooks created${NC}"

# README
echo -e "${YELLOW}📄 Creating README.md...${NC}"
cat > README.md << 'EOF'
# Ansible SOAP Module Project

Clean Architecture SOAP module for Ansible with DDD principles.

## Installation

### 1. Setup Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
