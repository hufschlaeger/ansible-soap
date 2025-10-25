"""
Use Case: SOAP Request senden.
Orchestriert die Geschäftslogik für das Senden eines SOAP-Requests.
"""
from typing import Optional, Dict, Any
from dataclasses import dataclass

from ...domain.entities.soap_request import SoapRequest
from ...domain.entities.soap_response import SoapResponse, ResponseStatus
from ...domain.entities.endpoint import Endpoint
from ...domain.repositories.soap_repository import SoapRepository
from ...domain.services.soap_service import SoapService
from ...domain.services.validation_service import ValidationService
from ...domain.value_objects.soap_action import SoapAction


@dataclass
class SendSoapRequestCommand:
    """
    Command-Objekt für Send-Request Use Case.
    Kapselt alle benötigten Daten.
    """
    endpoint: Endpoint
    soap_action: str
    body_content: str
    namespace: Optional[str] = None
    namespace_prefix: Optional[str] = None
    custom_headers: Optional[Dict[str, str]] = None
    timeout: Optional[int] = None
    validate_response: bool = True
    use_cache: bool = False
    max_retries: int = 0
    extract_xpath: Optional[str] = None
    strip_namespaces: bool = False


@dataclass
class SendSoapRequestResult:
    """
    Result-Objekt des Use Case.
    Kapselt das Ergebnis.
    """
    success: bool
    response: Optional[SoapResponse]
    extracted_data: Optional[Any] = None
    validation_errors: Optional[list] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Result zu Dictionary für Ansible"""
        result = {
            'success': self.success,
            'changed': self.success,  # Ansible convention
        }

        if self.response:
            result.update(self.response.to_ansible_result())

        if self.extracted_data:
            result['extracted_data'] = self.extracted_data

        if self.validation_errors:
            result['validation_errors'] = self.validation_errors

        if self.error_message:
            result['error_message'] = self.error_message

        return result


class SendSoapRequestUseCase:
    """
    Use Case für das Senden von SOAP-Requests.
    Orchestriert Domain Services und Repository.
    """

    def __init__(
            self,
            repository: SoapRepository,
            soap_service: Optional[SoapService] = None,
            validation_service: Optional[ValidationService] = None
    ):
        """
        Args:
            repository: SOAP Repository
            soap_service: Optional SOAP Service (wird erstellt wenn None)
            validation_service: Optional Validation Service
        """
        self._repository = repository
        self._soap_service = soap_service or SoapService(repository)
        self._validation_service = validation_service or ValidationService()

    def execute(self, command: SendSoapRequestCommand) -> SendSoapRequestResult:
        """
        Führt den Use Case aus.

        Args:
            command: Command mit allen benötigten Daten

        Returns:
            SendSoapRequestResult mit Ergebnis
        """
        # 1. Endpoint validieren
        if command.validate_response:
            validation_result = self._validation_service.validate_endpoint(
                command.endpoint
            )
            if not validation_result.is_valid:
                return SendSoapRequestResult(
                    success=False,
                    response=None,
                    validation_errors=validation_result.errors,
                    error_message="Endpoint-Validierung fehlgeschlagen"
                )

        # 2. SOAP Action erstellen
        try:
            soap_action = SoapAction.from_string(
                command.soap_action,
                namespace=command.namespace
            )
        except ValueError as e:
            return SendSoapRequestResult(
                success=False,
                response=None,
                error_message=f"Ungültige SOAP Action: {e}"
            )

        namespace_declarations = None
        if command.namespace and command.namespace_prefix:
          namespace_declarations = {
            command.namespace_prefix: command.namespace
          }

        # 3. Request senden (mit oder ohne Retry)
        try:
            if command.max_retries > 0:
                response = self._soap_service.execute_request_with_retry(
                    endpoint=command.endpoint,
                    action=soap_action,
                    body_content=command.body_content,
                    namespace_declarations=namespace_declarations,
                    custom_headers=command.custom_headers,
                    max_retries=command.max_retries
                )
            else:
                response = self._soap_service.execute_request(
                    endpoint=command.endpoint,
                    action=soap_action,
                    body_content=command.body_content,
                    namespace_declarations=namespace_declarations,
                    custom_headers=command.custom_headers,
                    use_cache=command.use_cache
                )
        except Exception as e:
            return SendSoapRequestResult(
                success=False,
                response=None,
                error_message=f"Request fehlgeschlagen: {e}"
            )

        # 4. Daten extrahieren wenn gewünscht
        extracted_data = None
        if command.extract_xpath and response.is_successful():
            try:
                extracted_data = self._soap_service.transform_response(
                    response,
                    extract_xpath=command.extract_xpath,
                    strip_namespaces=command.strip_namespaces
                )
            except Exception as e:
                # Extraktion fehlgeschlagen, aber Request war erfolgreich
                extracted_data = {"extraction_error": str(e)}

        # 5. Result erstellen
        return SendSoapRequestResult(
            success=response.is_successful(),
            response=response,
            extracted_data=extracted_data,
            error_message=response.error_message if not response.is_successful() else None
        )


class SendSoapRequestUseCaseError(Exception):
    """Exception für Use Case Fehler"""
    pass