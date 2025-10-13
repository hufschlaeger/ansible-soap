"""
Use Case: Endpoint validieren.
Prüft ob ein Endpoint erreichbar und korrekt konfiguriert ist.
"""
from typing import Optional, Dict, Any
from dataclasses import dataclass

from ...domain.entities.endpoint import Endpoint
from ...domain.repositories.soap_repository import SoapRepository
from ...domain.services.validation_service import ValidationService


@dataclass
class ValidateEndpointCommand:
    """Command für Endpoint-Validierung"""
    endpoint: Endpoint
    check_connectivity: bool = True
    check_wsdl: bool = False
    wsdl_url: Optional[str] = None


@dataclass
class ValidateEndpointResult:
    """Result der Endpoint-Validierung"""
    is_valid: bool
    is_reachable: bool = False
    has_wsdl: bool = False
    validation_errors: Optional[list] = None
    wsdl_operations: Optional[list] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary"""
        return {
            'valid': self.is_valid,
            'reachable': self.is_reachable,
            'has_wsdl': self.has_wsdl,
            'validation_errors': self.validation_errors or [],
            'wsdl_operations': self.wsdl_operations or [],
            'error_message': self.error_message
        }


class ValidateEndpointUseCase:
    """
    Use Case für Endpoint-Validierung.
    """

    def __init__(
            self,
            repository: SoapRepository,
            validation_service: Optional[ValidationService] = None
    ):
        """
        Args:
            repository: SOAP Repository
            validation_service: Optional Validation Service
        """
        self._repository = repository
        self._validation_service = validation_service or ValidationService()

    def execute(self, command: ValidateEndpointCommand) -> ValidateEndpointResult:
        """
        Führt die Validierung aus.

        Args:
            command: Command mit Validierungs-Parametern

        Returns:
            ValidateEndpointResult
        """
        # 1. Endpoint-Konfiguration validieren
        validation_result = self._validation_service.validate_endpoint(
            command.endpoint
        )

        if not validation_result.is_valid:
            return ValidateEndpointResult(
                is_valid=False,
                validation_errors=validation_result.errors,
                error_message="Endpoint-Konfiguration ungültig"
            )

        # 2. Erreichbarkeit prüfen
        is_reachable = False
        if command.check_connectivity:
            try:
                is_reachable = self._repository.validate_endpoint(
                    command.endpoint.url
                )
            except Exception as e:
                return ValidateEndpointResult(
                    is_valid=False,
                    is_reachable=False,
                    error_message=f"Connectivity-Check fehlgeschlagen: {e}"
                )

        # 3. WSDL prüfen wenn gewünscht
        has_wsdl = False
        wsdl_operations = None
        if command.check_wsdl:
            wsdl_url = command.wsdl_url or f"{command.endpoint.url}?wsdl"
            try:
                wsdl_content = self._repository.get_wsdl(wsdl_url)
                if wsdl_content:
                    has_wsdl = True
                    # Optional: WSDL parsen und Operationen extrahieren
                    wsdl_operations = self._extract_operations_from_wsdl(wsdl_content)
            except Exception as e:
                # WSDL-Fehler ist nicht kritisch
                pass

        return ValidateEndpointResult(
            is_valid=True,
            is_reachable=is_reachable,
            has_wsdl=has_wsdl,
            wsdl_operations=wsdl_operations
        )

    def _extract_operations_from_wsdl(self, wsdl_content: str) -> list:
        """
        Extrahiert Operationen aus WSDL.
        Vereinfachte Implementierung.
        """
        # TODO: Vollständige WSDL-Parsing-Implementierung
        operations = []

        # Einfaches Pattern-Matching für operation-Tags
        import re
        pattern = r'<operation.*?name="([^"]+)"'
        matches = re.findall(pattern, wsdl_content)

        return list(set(matches))  # Duplikate entfernen
