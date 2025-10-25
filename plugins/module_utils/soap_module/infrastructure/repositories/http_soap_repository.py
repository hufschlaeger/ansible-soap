"""
HTTP-basierte Implementierung des SOAP Repository.
"""
from typing import Optional, Dict

from ...domain.entities.soap_request import SoapRequest
from ...domain.entities.soap_response import SoapResponse, ResponseStatus
from ...domain.repositories.soap_repository import (
    SoapRepository,
    SoapRepositoryError,
    EndpointNotReachableError,
    InvalidResponseError,
)
from ..adapters.http_client import HttpClient, HttpClientError, HttpResponse
from ..adapters.xml_parser import XmlParser, XmlParserError

class HttpSoapRepository(SoapRepository):
    """
    Repository-Implementierung mit HTTP Client.
    """

    def __init__(
            self,
            http_client: Optional[HttpClient] = None,
            verify_ssl: bool = True,
            timeout: int = 30  # ✅ NEU: Standard-Timeout
    ):
        """
        Args:
            http_client: Optional vorkonfigurierter HTTP Client
            verify_ssl: Ob SSL-Zertifikate validiert werden sollen
            timeout: Standard-Timeout in Sekunden (wird nur verwendet wenn kein http_client übergeben wird)
        """
        self._http_client = http_client or HttpClient(
            verify_ssl=verify_ssl,
            timeout=timeout  # ✅ Timeout übergeben
        )
        self._async_responses: Dict[str, SoapResponse] = {}

    def send(self, request: SoapRequest) -> SoapResponse:
        """
        Sendet einen SOAP-Request synchron.

        Args:
            request: Der zu sendende SoapRequest

        Returns:
            SoapResponse mit dem Ergebnis

        Raises:
            EndpointNotReachableError: Bei Verbindungsproblemen
            AuthenticationError: Bei Authentifizierungsfehlern
            InvalidResponseError: Bei ungültiger Response
        """


        try:
            # Auth-Config aus Request-Headers extrahieren
            auth_config = self._extract_auth_config(request)

            # HTTP Request ausführen
            http_response = self._http_client.post(
                url=request.endpoint_url,
                body=request.body,
                headers=request.headers,
                auth_config=auth_config,
                timeout=request.timeout  # ✅ Timeout aus Request verwenden
            )

            # Response validieren
            if not XmlParser.validate_xml(http_response.body):
                raise InvalidResponseError(
                    "Response ist kein gültiges XML",
                    raw_response=http_response.body
                )

            # SoapResponse erstellen
            return self._create_soap_response(request, http_response)

        except HttpClientError as e:
            # HTTP-Fehler zu Domain-Exceptions mappen
            if "timeout" in str(e).lower():
                raise EndpointNotReachableError(
                    request.endpoint_url,
                    f"Timeout nach {request.timeout}s"
                )
            elif "ssl" in str(e).lower():
                raise EndpointNotReachableError(
                    request.endpoint_url,
                    f"SSL-Fehler: {e}"
                )
            elif "connection" in str(e).lower():
                raise EndpointNotReachableError(
                    request.endpoint_url,
                    f"Verbindungsfehler: {e}"
                )
            else:
                raise SoapRepositoryError(f"HTTP-Fehler: {e}")

    def send_async(self, request: SoapRequest) -> str:
        """
        Sendet einen SOAP-Request asynchron.

        Args:
            request: Der zu sendende SoapRequest

        Returns:
            Request-ID für späteres Abrufen
        """
        # Vereinfachte Implementierung: Führt Request in Thread aus
        import threading

        def execute_async():
            try:
                response = self.send(request)
                self._async_responses[request.id] = response
            except Exception as e:
                # Fehler-Response erstellen
                error_response = SoapResponse(
                    request_id=request.id,
                    status=ResponseStatus.ERROR,
                    status_code=0,
                    body="",
                    error_message=str(e)
                )
                self._async_responses[request.id] = error_response

        thread = threading.Thread(target=execute_async)
        thread.daemon = True
        thread.start()

        return request.id

    def get_response(self, request_id: str) -> Optional[SoapResponse]:
        """
        Ruft die Response für einen asynchronen Request ab.

        Args:
            request_id: Die ID des Requests

        Returns:
            SoapResponse wenn verfügbar, sonst None
        """
        return self._async_responses.get(request_id)

    def validate_endpoint(self, url: str) -> bool:
        """
        Validiert ob ein Endpoint erreichbar ist.

        Args:
            url: Die zu validierende URL

        Returns:
            True wenn erreichbar, False sonst
        """
        return self._http_client.test_connectivity(url)

    def get_wsdl(self, url: str) -> Optional[str]:
        """
        Lädt die WSDL-Definition eines Endpoints.

        Args:
            url: Die WSDL-URL

        Returns:
            WSDL-Inhalt als String oder None
        """
        try:
            response = self._http_client.get(url, timeout=10)
            if response.is_successful():
                return response.body
            return None
        except HttpClientError:
            return None

    def _create_soap_response(
            self,
            request: SoapRequest,
            http_response: HttpResponse
    ) -> SoapResponse:
        """
        Erstellt SoapResponse aus HTTP Response.

        Args:
            request: Der ursprüngliche Request
            http_response: Die HTTP Response

        Returns:
            SoapResponse
        """
        # Status bestimmen
        if http_response.status_code == 401 or http_response.status_code == 403:
            status = ResponseStatus.AUTH_ERROR
            error_msg = "Authentifizierung fehlgeschlagen"
        elif http_response.status_code == 500:
            # SOAP Fault prüfen
            if self._contains_soap_fault(http_response.body):
                status = ResponseStatus.SOAP_FAULT
                error_msg = self._extract_fault_string(http_response.body)
            else:
                status = ResponseStatus.ERROR
                error_msg = "Server-Fehler"
        elif http_response.is_successful():
            status = ResponseStatus.SUCCESS
            error_msg = None
        else:
            status = ResponseStatus.ERROR
            error_msg = f"HTTP {http_response.status_code}"

        return SoapResponse(
            request_id=request.id,
            status=status,
            status_code=http_response.status_code,
            body=http_response.body,
            headers=http_response.headers,
            response_time_ms=http_response.elapsed_ms,
            error_message=error_msg
        )

    def _contains_soap_fault(self, xml_body: str) -> bool:
        """Prüft ob Response einen SOAP Fault enthält"""
        try:
            element = XmlParser.parse(xml_body)
            # Suche nach Fault-Element
            fault = XmlParser.find_element_text(element, './/Fault') or \
                    XmlParser.find_element_text(element, './/{http://schemas.xmlsoap.org/soap/envelope/}Fault') or \
                    XmlParser.find_element_text(element, './/{http://www.w3.org/2003/05/soap-envelope}Fault')
            return fault is not None
        except XmlParserError:
            return False

    def _extract_fault_string(self, xml_body: str) -> str:
        """Extrahiert Fault-String aus Response"""
        try:
            element = XmlParser.parse(xml_body)
            fault_string = XmlParser.find_element_text(element, './/faultstring') or \
                           XmlParser.find_element_text(element, './/{http://schemas.xmlsoap.org/soap/envelope/}faultstring') or \
                           XmlParser.find_element_text(element, './/{http://www.w3.org/2003/05/soap-envelope}Reason')
            return fault_string or "Unbekannter SOAP Fault"
        except XmlParserError:
            return "SOAP Fault (Details nicht verfügbar)"

    def _extract_auth_config(self, request: SoapRequest) -> Optional[Dict]:
        """
        Extrahiert Auth-Config aus Request-Headers.
        Vereinfachte Implementierung.
        """
        # In echter Implementierung würde man Auth-Infos
        # aus separatem Config-Objekt holen
        return None

    def close(self):
        """Schließt die HTTP-Verbindung"""
        self._http_client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
