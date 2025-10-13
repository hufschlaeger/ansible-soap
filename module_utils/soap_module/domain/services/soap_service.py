"""
Domain Service für SOAP-Operationen.
Enthält Geschäftslogik, die nicht zu einer Entity gehört.
"""
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from ..entities.soap_request import SoapRequest
from ..entities.soap_response import SoapResponse, ResponseStatus
from ..entities.endpoint import Endpoint
from ..value_objects.xml_body import XmlBody
from ..value_objects.soap_action import SoapAction
from ..value_objects.soap_envelope import SoapEnvelope, SoapVersion
from ..repositories.soap_repository import SoapRepository, SoapRepositoryError


class SoapService:
    """
    Domain Service für SOAP-Operationen.
    Koordiniert komplexe Geschäftslogik zwischen Entities.
    """

    def __init__(self, repository: SoapRepository):
        """
        Args:
            repository: Repository-Implementierung für SOAP-Kommunikation
        """
        self._repository = repository
        self._request_cache: Dict[str, SoapResponse] = {}
        self._cache_ttl = timedelta(minutes=5)

    def execute_request(
            self,
            endpoint: Endpoint,
            action: SoapAction,
            body_content: str,
            use_cache: bool = False,
            custom_headers: Optional[Dict[str, str]] = None
    ) -> SoapResponse:
        """
        Führt einen SOAP-Request aus.

        Args:
            endpoint: Der Ziel-Endpoint
            action: Die SOAP Action
            body_content: Der Body-Inhalt
            use_cache: Ob Caching verwendet werden soll
            custom_headers: Optional zusätzliche Headers

        Returns:
            SoapResponse mit dem Ergebnis

        Raises:
            ValueError: Bei ungültigen Parametern
            SoapRepositoryError: Bei Kommunikationsfehlern
        """
        # Validierung
        if not endpoint.supports_operation(action.value):
            raise ValueError(
                f"Operation '{action.value}' wird von Endpoint '{endpoint.name}' nicht unterstützt"
            )

        # Cache-Key erstellen
        cache_key = self._create_cache_key(endpoint.url, action.value, body_content)

        # Cache prüfen
        if use_cache and cache_key in self._request_cache:
            cached_response = self._request_cache[cache_key]
            if self._is_cache_valid(cached_response):
                return cached_response

        # SOAP Envelope erstellen
        soap_version = SoapVersion.V1_1 if endpoint.soap_version == "1.1" else SoapVersion.V1_2
        envelope = SoapEnvelope.from_body(body_content, version=soap_version)

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

        # Request ausführen
        response = self._repository.send(request)

        # In Cache speichern
        if use_cache and response.is_successful():
            self._request_cache[cache_key] = response

        return response

    def execute_request_with_retry(
            self,
            endpoint: Endpoint,
            action: SoapAction,
            body_content: str,
            max_retries: int = 3,
            retry_delay_seconds: int = 1
    ) -> SoapResponse:
        """
        Führt einen SOAP-Request mit Retry-Logik aus.

        Args:
            endpoint: Der Ziel-Endpoint
            action: Die SOAP Action
            body_content: Der Body-Inhalt
            max_retries: Maximale Anzahl von Wiederholungen
            retry_delay_seconds: Verzögerung zwischen Versuchen

        Returns:
            SoapResponse mit dem Ergebnis
        """
        import time

        last_error = None

        for attempt in range(max_retries + 1):
            try:
                return self.execute_request(endpoint, action, body_content)
            except SoapRepositoryError as e:
                last_error = e
                if attempt < max_retries:
                    time.sleep(retry_delay_seconds * (attempt + 1))  # Exponential backoff
                    continue
                break

        # Alle Versuche fehlgeschlagen
        raise SoapRepositoryError(
            f"Request fehlgeschlagen nach {max_retries} Versuchen: {last_error}"
        )

    def batch_execute(
            self,
            endpoint: Endpoint,
            requests: List[Dict[str, str]]
    ) -> List[SoapResponse]:
        """
        Führt mehrere SOAP-Requests nacheinander aus.

        Args:
            endpoint: Der Ziel-Endpoint
            requests: Liste von Dicts mit 'action' und 'body_content'

        Returns:
            Liste von SoapResponses
        """
        responses = []

        for req_data in requests:
            action = SoapAction.from_string(req_data['action'])
            body_content = req_data['body_content']

            try:
                response = self.execute_request(endpoint, action, body_content)
                responses.append(response)
            except Exception as e:
                # Fehler-Response erstellen
                error_response = SoapResponse(
                    request_id="batch-error",
                    status=ResponseStatus.ERROR,
                    status_code=0,
                    body=f"<error>{str(e)}</error>",
                    error_message=str(e)
                )
                responses.append(error_response)

        return responses

    def validate_endpoint_connectivity(self, endpoint: Endpoint) -> bool:
        """
        Validiert ob ein Endpoint erreichbar ist.

        Args:
            endpoint: Der zu validierende Endpoint

        Returns:
            True wenn erreichbar, False sonst
        """
        return self._repository.validate_endpoint(endpoint.url)

    def discover_operations(self, endpoint: Endpoint) -> Optional[List[str]]:
        """
        Versucht die verfügbaren Operationen eines Endpoints zu ermitteln.
        Lädt dazu die WSDL-Definition.

        Args:
            endpoint: Der Endpoint

        Returns:
            Liste von Operation-Namen oder None
        """
        wsdl_url = endpoint.url + "?wsdl"
        wsdl_content = self._repository.get_wsdl(wsdl_url)

        if not wsdl_content:
            return None

        return self._parse_operations_from_wsdl(wsdl_content)

    def transform_response(
            self,
            response: SoapResponse,
            extract_xpath: Optional[str] = None,
            strip_namespaces: bool = False
    ) -> Dict:
        """
        Transformiert eine Response in ein Dictionary.

        Args:
            response: Die zu transformierende Response
            extract_xpath: Optional XPath zum Extrahieren spezifischer Daten
            strip_namespaces: Ob Namespaces entfernt werden sollen

        Returns:
            Dictionary mit transformierten Daten
        """
        if not response.is_successful():
            return {
                "success": False,
                "error": response.error_message
            }

        xml_body = XmlBody.from_string(response.body)

        # Namespaces entfernen wenn gewünscht
        if strip_namespaces:
            xml_body = xml_body.strip_namespaces()

        # SOAP Body-Content extrahieren
        if xml_body.is_soap_envelope():
            body_content = xml_body.extract_body_content()
            if body_content:
                xml_body = body_content

        # Spezifisches Element extrahieren
        if extract_xpath:
            element_text = xml_body.find_element(extract_xpath)
            return {
                "success": True,
                "data": element_text,
                "xpath": extract_xpath
            }

        # Komplettes XML zu Dict
        return {
            "success": True,
            "data": xml_body.to_dict(),
            "metadata": {
                "status_code": response.status_code,
                "response_time_ms": response.response_time_ms
            }
        }

    def compare_responses(
            self,
            response1: SoapResponse,
            response2: SoapResponse,
            ignore_namespaces: bool = True
    ) -> bool:
        """
        Vergleicht zwei Responses auf inhaltliche Gleichheit.

        Args:
            response1: Erste Response
            response2: Zweite Response
            ignore_namespaces: Ob Namespaces beim Vergleich ignoriert werden sollen

        Returns:
            True wenn inhaltlich gleich, False sonst
        """
        if response1.status != response2.status:
            return False

        if not response1.is_successful() or not response2.is_successful():
            return response1.error_message == response2.error_message

        xml1 = XmlBody.from_string(response1.body)
        xml2 = XmlBody.from_string(response2.body)

        if ignore_namespaces:
            xml1 = xml1.strip_namespaces()
            xml2 = xml2.strip_namespaces()

        return xml1 == xml2

    def _create_cache_key(self, url: str, action: str, body: str) -> str:
        """Erstellt einen Cache-Key aus Request-Parametern"""
        import hashlib
        key_string = f"{url}:{action}:{body}"
        return hashlib.sha256(key_string.encode()).hexdigest()

    def _is_cache_valid(self, response: SoapResponse) -> bool:
        """Prüft ob ein gecachtes Response noch gültig ist"""
        age = datetime.now() - response.received_at
        return age < self._cache_ttl

    def _parse_operations_from_wsdl(self, wsdl_content: str) -> List[str]:
        """
        Extrahiert Operation-Namen aus WSDL.
        Vereinfachte Implementierung.
        """
        import re

        # Suche nach operation-Tags
        operations = re.findall(r'<operation[^>]*name="([^"]*)"', wsdl_content)
        return list(set(operations))  # Duplikate entfernen

    def clear_cache(self) -> None:
        """Leert den Response-Cache"""
        self._request_cache.clear()
