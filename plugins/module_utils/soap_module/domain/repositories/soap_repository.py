"""
Repository Interface für SOAP-Operationen.
Definiert die Schnittstelle für die Persistierung/Kommunikation.
"""
from abc import ABC, abstractmethod
from typing import Optional
from ..entities.soap_request import SoapRequest
from ..entities.soap_response import SoapResponse


class SoapRepository(ABC):
    """
    Abstract Repository für SOAP-Kommunikation.
    Wird in der Infrastructure-Schicht implementiert.
    """

    @abstractmethod
    def send(self, request: SoapRequest) -> SoapResponse:
        """
        Sendet einen SOAP-Request und gibt die Response zurück.

        Args:
            request: Der zu sendende SoapRequest

        Returns:
            SoapResponse mit dem Ergebnis

        Raises:
            ConnectionError: Bei Verbindungsproblemen
            TimeoutError: Bei Timeout
        """
        pass

    @abstractmethod
    def send_async(self, request: SoapRequest) -> str:
        """
        Sendet einen SOAP-Request asynchron.

        Args:
            request: Der zu sendende SoapRequest

        Returns:
            Request-ID für späteres Abrufen
        """
        pass

    @abstractmethod
    def get_response(self, request_id: str) -> Optional[SoapResponse]:
        """
        Ruft die Response für einen asynchronen Request ab.

        Args:
            request_id: Die ID des Requests

        Returns:
            SoapResponse wenn verfügbar, sonst None
        """
        pass

    @abstractmethod
    def validate_endpoint(self, url: str) -> bool:
        """
        Validiert ob ein Endpoint erreichbar ist.

        Args:
            url: Die zu validierende URL

        Returns:
            True wenn erreichbar, False sonst
        """
        pass

    @abstractmethod
    def get_wsdl(self, url: str) -> Optional[str]:
        """
        Lädt die WSDL-Definition eines Endpoints.

        Args:
            url: Die WSDL-URL

        Returns:
            WSDL-Inhalt als String oder None
        """
        pass


class SoapRepositoryError(Exception):
    """Basis-Exception für Repository-Fehler"""
    pass


class EndpointNotReachableError(SoapRepositoryError):
    """Exception wenn Endpoint nicht erreichbar ist"""
    def __init__(self, url: str, reason: str):
        self.url = url
        self.reason = reason
        super().__init__(f"Endpoint {url} nicht erreichbar: {reason}")


class InvalidResponseError(SoapRepositoryError):
    """Exception bei ungültiger Response"""
    def __init__(self, message: str, raw_response: Optional[str] = None):
        self.raw_response = raw_response
        super().__init__(message)


class AuthenticationError(SoapRepositoryError):
    """Exception bei Authentifizierungsfehlern"""
    pass
