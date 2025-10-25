# -*- coding: utf-8 -*-
# Copyright: (c) 2024, Daniel Hufschläger <daniel@hufschlaeger.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Ansible SOAP Client Collection - Modules
=========================================

This package contains Ansible modules for interacting with SOAP web services.

Modules:
    - soap_request: Send individual SOAP requests
    - soap_batch: Send multiple SOAP requests in batch
    - soap_validate: Validate SOAP endpoint connectivity
"""

__all__ = ['soap_request', 'soap_batch', 'soap_validate']
