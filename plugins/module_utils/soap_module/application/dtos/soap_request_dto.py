"""
Data Transfer Objects für die Application Layer.
"""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class SoapRequestDTO:
    """
    DTO für SOAP Request Input.
    Verwendet von Presentation Layer.
    """
    endpoint_url: str
    soap_action: str
    body: Optional[str] = None
    body_dict: Optional[Dict[str, Any]] = None
    body_root_tag: str = "Request"
    namespace: Optional[str] = None
    namespace_prefix: Optional[str] = None
    skip_request_wrapper: Optional[bool] = False
    soap_version: str = "1.1"
    soap_header: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    timeout: int = 30

    # Endpoint-Konfiguration
    auth_type: str = "none"
    username: Optional[str] = None
    password: Optional[str] = None
    cert_path: Optional[str] = None
    key_path: Optional[str] = None

    # Verarbeitungs-Optionen
    validate: bool = True
    use_cache: bool = False
    max_retries: int = 0
    extract_xpath: Optional[str] = None
    strip_namespaces: bool = False

    def validate_input(self) -> tuple[bool, Optional[str]]:
        """
        Validiert die DTO-Daten.

        Returns:
            Tuple (is_valid, error_message)
        """
        if not self.endpoint_url:
            return False, "endpoint_url ist erforderlich"

        # if not self.soap_action:
        #     return False, "soap_action ist erforderlich"

        if not self.body and not self.body_dict:
            return False, "Entweder body oder body_dict muss angegeben werden"

        if self.body and self.body_dict:
            return False, "body und body_dict können nicht gleichzeitig angegeben werden"

        if self.soap_version not in ["1.1", "1.2"]:
            return False, "soap_version muss 1.1 oder 1.2 sein"

        if self.auth_type not in ["none", "basic", "digest", "ntlm", "certificate"]:
            return False, f"Ungültiger auth_type: {self.auth_type}"

        if self.auth_type in ["basic", "digest", "ntlm"]:
            if not self.username or not self.password:
                return False, f"{self.auth_type} Auth benötigt username und password"

        if self.auth_type == "certificate":
            if not self.cert_path:
                return False, "certificate Auth benötigt cert_path"

        if self.timeout < 1:
            return False, "timeout muss mindestens 1 Sekunde sein"

        if self.max_retries < 0:
            return False, "max_retries kann nicht negativ sein"

        return True, None


@dataclass
class SoapResponseDTO:
    """
    DTO für SOAP Response Output.
    """
    success: bool
    status_code: int
    body: str
    headers: Optional[Dict[str, str]] = None
    response_time_ms: Optional[float] = None
    extracted_data: Optional[Any] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary für Ansible"""
        result = {
            'success': self.success,
            'status_code': self.status_code,
            'body': self.body,
        }

        if self.headers:
            result['headers'] = self.headers

        if self.response_time_ms is not None:
            result['response_time_ms'] = self.response_time_ms

        if self.extracted_data:
            result['extracted_data'] = self.extracted_data

        if self.error_message:
            result['error_message'] = self.error_message

        return result


@dataclass
class EndpointValidationDTO:
    """DTO für Endpoint-Validierung"""
    endpoint_url: str
    check_connectivity: bool = True
    check_wsdl: bool = False
    wsdl_url: Optional[str] = None
    timeout: int = 5


@dataclass
class BatchRequestDTO:
    """DTO für Batch-Requests"""
    requests: List[SoapRequestDTO]
    parallel: bool = False
    max_workers: int = 5
    stop_on_error: bool = False
