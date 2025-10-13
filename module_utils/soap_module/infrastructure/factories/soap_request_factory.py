"""
Factory für das Erstellen von SoapRequests.
"""
from typing import Dict, Any, Optional
from ...domain.entities.soap_request import SoapRequest
from ...domain.entities.endpoint import Endpoint
from ...domain.value_objects.soap_envelope import SoapEnvelope, SoapVersion
from ...domain.value_objects.soap_action import SoapAction
from ...domain.value_objects.xml_body import XmlBody


class SoapRequestFactory:
    """
    Factory zum Erstellen von SoapRequests aus verschiedenen Quellen.
    """

    @staticmethod
    def from_ansible_params(params: Dict[str, Any]) -> SoapRequest:
        """
        Erstellt SoapRequest aus Ansible-Parametern.

        Args:
            params: Dictionary mit Ansible-Parametern

        Returns:
            SoapRequest
        """
        # Endpoint-URL
        endpoint_url = params['endpoint_url']

        # SOAP Action
        soap_action = params.get('soap_action', '')

        # Body-Content erstellen
        body_content = params.get('body')
        if not body_content and params.get('body_dict'):
            # Aus Dictionary erstellen
            xml_body = XmlBody.from_dict(
                params['body_dict'],
                root_tag=params.get('body_root_tag', 'Request')
            )
            body_content = xml_body.to_string()

        # SOAP Envelope erstellen
        soap_version_str = params.get('soap_version', '1.1')
        soap_version = SoapVersion.V1_1 if soap_version_str == '1.1' else SoapVersion.V1_2

        envelope = SoapEnvelope.from_body(body_content, version=soap_version)

        # Namespace hinzufügen wenn angegeben
        if params.get('namespace'):
            namespace_prefix = params.get('namespace_prefix', 'ns')
            envelope = envelope.with_namespace(namespace_prefix, params['namespace'])

        # SOAP Header hinzufügen wenn angegeben
        if params.get('soap_header'):
            envelope = envelope.with_header(params['soap_header'])

        # Request erstellen
        request = SoapRequest(
            endpoint_url=endpoint_url,
            soap_action=soap_action,
            body=envelope.build(),
            namespace=params.get('namespace'),
            soap_version=soap_version_str,
            timeout=params.get('timeout', 30)
        )

        # Zusätzliche Headers
        if params.get('headers'):
            for key, value in params['headers'].items():
                request.add_header(key, value)

        return request

    @staticmethod
    def from_endpoint_and_action(
            endpoint: Endpoint,
            action: SoapAction,
            body_content: str,
            custom_headers: Optional[Dict[str, str]] = None
    ) -> SoapRequest:
        """
        Erstellt SoapRequest aus Endpoint und Action.

        Args:
            endpoint: Der Ziel-Endpoint
            action: Die SOAP Action
            body_content: Der Body-Inhalt
            custom_headers: Optional zusätzliche Headers

        Returns:
            SoapRequest
        """
        # SOAP Envelope erstellen
        soap_version = SoapVersion.V1_1 if endpoint.soap_version == '1.1' else SoapVersion.V1_2
        envelope = SoapEnvelope.from_body(body_content, version=soap_version)

        # Namespace aus Action hinzufügen
        if action.namespace:
            envelope = envelope.with_namespace('ns', action.namespace)

        # Request erstellen
        request = SoapRequest(
            endpoint_url=endpoint.url,
            soap_action=action.value,
            body=envelope.build(),
            namespace=action.namespace,
            soap_version=endpoint.soap_version,
            timeout=endpoint.default_timeout
        )

        # Custom Headers hinzufügen
        if custom_headers:
            for key, value in custom_headers.items():
                request.add_header(key, value)

        return request

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> SoapRequest:
        """
        Erstellt SoapRequest aus Dictionary.

        Args:
            data: Dictionary mit Request-Daten

        Returns:
            SoapRequest
        """
        return SoapRequest(
            endpoint_url=data['endpoint_url'],
            soap_action=data.get('soap_action', ''),
            body=data['body'],
            namespace=data.get('namespace'),
            soap_version=data.get('soap_version', '1.1'),
            timeout=data.get('timeout', 30),
            headers=data.get('headers', {})
        )
