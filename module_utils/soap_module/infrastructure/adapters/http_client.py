"""
HTTP Client Adapter für SOAP-Kommunikation.
Abstrahiert die HTTP-Bibliothek (requests, urllib3, etc.)
"""
from typing import Optional, Dict, Any
from dataclasses import dataclass
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from requests_ntlm import HttpNtlmAuth
import ssl
from urllib3.exceptions import InsecureRequestWarning
import warnings


@dataclass
class HttpResponse:
    """Response vom HTTP Client"""
    status_code: int
    body: str
    headers: Dict[str, str]
    elapsed_ms: float

    def is_successful(self) -> bool:
        """Prüft ob Request erfolgreich war"""
        return 200 <= self.status_code < 300


class HttpClientError(Exception):
    """Basis-Exception für HTTP Client Fehler"""
    pass


class HttpClient:
    """
    HTTP Client für SOAP-Requests.
    Wrapper um requests-Bibliothek.
    """

    def __init__(
            self,
            verify_ssl: bool = True,
            timeout: int = 30,
            max_retries: int = 0
    ):
        """
        Args:
            verify_ssl: Ob SSL-Zertifikate validiert werden sollen
            timeout: Standard-Timeout in Sekunden
            max_retries: Maximale Anzahl automatischer Wiederholungen
        """
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.max_retries = max_retries
        self._session: Optional[requests.Session] = None

        if not verify_ssl:
            warnings.simplefilter('ignore', InsecureRequestWarning)

    def _get_session(self) -> requests.Session:
        """Lazy Session-Initialisierung"""
        if self._session is None:
            self._session = requests.Session()

            # Retry-Strategie konfigurieren
            if self.max_retries > 0:
                from requests.adapters import HTTPAdapter
                from urllib3.util.retry import Retry

                retry_strategy = Retry(
                    total=self.max_retries,
                    backoff_factor=1,
                    status_forcelist=[429, 500, 502, 503, 504],
                    allowed_methods=["POST"]
                )
                adapter = HTTPAdapter(max_retries=retry_strategy)
                self._session.mount("http://", adapter)
                self._session.mount("https://", adapter)

        return self._session

    def post(
            self,
            url: str,
            body: str,
            headers: Optional[Dict[str, str]] = None,
            auth_config: Optional[Dict[str, Any]] = None,
            timeout: Optional[int] = None,
            proxies: Optional[Dict[str, str]] = None
    ) -> HttpResponse:
        """
        Sendet einen POST-Request.

        Args:
            url: Ziel-URL
            body: Request-Body
            headers: HTTP Headers
            auth_config: Authentifizierungs-Konfiguration
            timeout: Timeout in Sekunden (überschreibt Standard)
            proxies: Proxy-Konfiguration

        Returns:
            HttpResponse mit Ergebnis

        Raises:
            HttpClientError: Bei Kommunikationsfehlern
        """
        session = self._get_session()
        timeout_value = timeout or self.timeout

        # Authentifizierung konfigurieren
        auth = self._configure_auth(auth_config)

        # Client-Zertifikat konfigurieren
        cert = self._configure_cert(auth_config)

        try:
            import time
            start_time = time.time()

            response = session.post(
                url=url,
                data=body.encode('utf-8'),
                headers=headers or {},
                auth=auth,
                cert=cert,
                timeout=timeout_value,
                verify=self.verify_ssl,
                proxies=proxies
            )

            elapsed_ms = (time.time() - start_time) * 1000

            return HttpResponse(
                status_code=response.status_code,
                body=response.text,
                headers=dict(response.headers),
                elapsed_ms=elapsed_ms
            )

        except requests.exceptions.Timeout as e:
            raise HttpClientError(f"Request timeout nach {timeout_value}s: {e}")

        except requests.exceptions.ConnectionError as e:
            raise HttpClientError(f"Verbindungsfehler: {e}")

        except requests.exceptions.SSLError as e:
            raise HttpClientError(f"SSL-Fehler: {e}")

        except requests.exceptions.RequestException as e:
            raise HttpClientError(f"HTTP-Fehler: {e}")

    def get(
            self,
            url: str,
            headers: Optional[Dict[str, str]] = None,
            timeout: Optional[int] = None
    ) -> HttpResponse:
        """
        Sendet einen GET-Request (z.B. für WSDL).

        Args:
            url: Ziel-URL
            headers: HTTP Headers
            timeout: Timeout in Sekunden

        Returns:
            HttpResponse mit Ergebnis
        """
        session = self._get_session()
        timeout_value = timeout or self.timeout

        try:
            import time
            start_time = time.time()

            response = session.get(
                url=url,
                headers=headers or {},
                timeout=timeout_value,
                verify=self.verify_ssl
            )

            elapsed_ms = (time.time() - start_time) * 1000

            return HttpResponse(
                status_code=response.status_code,
                body=response.text,
                headers=dict(response.headers),
                elapsed_ms=elapsed_ms
            )

        except requests.exceptions.RequestException as e:
            raise HttpClientError(f"HTTP-Fehler: {e}")

    def test_connectivity(self, url: str, timeout: int = 5) -> bool:
        """
        Testet ob ein Endpoint erreichbar ist.

        Args:
            url: Zu testende URL
            timeout: Timeout in Sekunden

        Returns:
            True wenn erreichbar, False sonst
        """
        try:
            response = self.get(url, timeout=timeout)
            return response.status_code < 500
        except HttpClientError:
            return False

    def _configure_auth(
            self,
            auth_config: Optional[Dict[str, Any]]
    ) -> Optional[Any]:
        """Konfiguriert Authentifizierung"""
        if not auth_config:
            return None

        auth_type = auth_config.get('type')

        if auth_type == 'basic':
            return HTTPBasicAuth(
                auth_config['username'],
                auth_config['password']
            )

        elif auth_type == 'digest':
            return HTTPDigestAuth(
                auth_config['username'],
                auth_config['password']
            )

        elif auth_type == 'ntlm':
            return HttpNtlmAuth(
                auth_config['username'],
                auth_config['password']
            )

        return None

    def _configure_cert(
            self,
            auth_config: Optional[Dict[str, Any]]
    ) -> Optional[tuple]:
        """Konfiguriert Client-Zertifikat"""
        if not auth_config:
            return None

        if auth_config.get('type') == 'certificate':
            cert_path = auth_config.get('cert_path')
            key_path = auth_config.get('key_path')

            if cert_path:
                if key_path:
                    return (cert_path, key_path)
                return cert_path

        return None

    def close(self):
        """Schließt die Session"""
        if self._session:
            self._session.close()
            self._session = None

    def __enter__(self):
        """Context Manager Entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager Exit"""
        self.close()
