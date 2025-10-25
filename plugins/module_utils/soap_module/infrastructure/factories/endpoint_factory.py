"""
Factory für das Erstellen von Endpoints.
"""
from typing import Dict, Any
from ...domain.entities.endpoint import Endpoint


class EndpointFactory:
    """
    Factory zum Erstellen von Endpoints aus verschiedenen Quellen.
    """

    @staticmethod
    def from_ansible_params(params: Dict[str, Any]) -> Endpoint:
        """
        Erstellt Endpoint aus Ansible-Parametern.

        Args:
            params: Dictionary mit Ansible-Parametern

        Returns:
            Endpoint
        """
        return Endpoint(
            url=params['endpoint_url'],
            name=params.get('endpoint_name', 'default'),
            auth_type=params.get('auth_type', 'none'),
            username=params.get('username'),
            password=params.get('password'),
            cert_path=params.get('cert_path'),
            key_path=params.get('key_path'),
            default_timeout=params.get('timeout', 30),
            supported_operations=params.get('supported_operations')
        )

    @staticmethod
    def from_config_file(config: Dict[str, Any]) -> Endpoint:
        """
        Erstellt Endpoint aus Config-Dictionary.

        Args:
            config: Konfiguration als Dictionary

        Returns:
            Endpoint
        """
        return Endpoint(
            url=config['url'],
            name=config.get('name', 'unnamed'),
            auth_type=config.get('auth', {}).get('type', 'none'),
            username=config.get('auth', {}).get('username'),
            password=config.get('auth', {}).get('password'),
            cert_path=config.get('auth', {}).get('cert_path'),
            key_path=config.get('auth', {}).get('key_path'),
            default_timeout=config.get('timeout', 30),
            supported_operations=config.get('operations')
        )

    @staticmethod
    def from_url(url: str, **kwargs) -> Endpoint:
        """
        Erstellt Endpoint aus URL mit optionalen Parametern.

        Args:
            url: Endpoint-URL
            **kwargs: Zusätzliche Parameter

        Returns:
            Endpoint
        """
        return Endpoint(
            url=url,
            name=kwargs.get('name', 'default'),
            auth_type=kwargs.get('auth_type', 'none'),
            username=kwargs.get('username'),
            password=kwargs.get('password'),
            default_timeout=kwargs.get('timeout', 30)
        )
