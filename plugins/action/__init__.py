# -*- coding: utf-8 -*-
# Copyright: (c) 2024, Daniel Hufschläger <daniel@hufschlaeger.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Ansible SOAP Client Collection - Action Plugins
================================================

Action plugins run on the Ansible controller before delegating to modules.
They handle:
- Variable templating (Jinja2)
- Sensitive data handling (passwords, keys)
- Controller-side preprocessing
- Module execution coordination

Available Action Plugins:
- soap_request: Single SOAP request execution
- soap_batch: Batch SOAP request execution
- soap_validate: SOAP endpoint validation
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

__all__ = ['soap_request', 'soap_batch', 'soap_validate']
