"""
Domain Entity: SoapResponse
Repräsentiert die Antwort auf einen SOAP-Request.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ResponseStatus(Enum):
    """Status der SOAP-Response"""
    SUCCESS = "success"
    SOAP_FAULT = "soap_fault"
    HTTP_ERROR = "http_error"
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    FAILURE = "failure"
    ERROR = "error"
    PARSING_ERROR = "parsing_error"
    AUTH_ERROR = "auth_error"


@dataclass
class SoapResponse:
    """
    Entity für eine SOAP-Response.
    Kapselt alle Informationen über die Antwort eines SOAP-Requests.
    """

    request_id: str  # Referenz zum ursprünglichen Request
    status: ResponseStatus
    status_code: Optional[int] = None
    body: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)

    # Bei Erfolg
    parsed_body: Optional[Dict[str, Any]] = None

    # Bei Fehler/Fault
    fault_code: Optional[str] = None
    fault_string: Optional[str] = None
    fault_detail: Optional[str] = None
    error_message: Optional[str] = None

    # Metadaten
    response_time_ms: Optional[float] = None
    received_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validierung nach Initialisierung"""
        if not self.request_id:
            raise ValueError("request_id ist erforderlich")

    def is_successful(self) -> bool:
        """Prüft ob der Request erfolgreich war"""
        return self.status == ResponseStatus.SUCCESS and 200 <= (self.status_code or 0) < 300

    def has_soap_fault(self) -> bool:
        """Prüft ob eine SOAP Fault vorliegt"""
        return self.status == ResponseStatus.SOAP_FAULT

    def get_fault_info(self) -> Optional[Dict[str, str]]:
        """Gibt Fault-Informationen zurück, falls vorhanden"""
        if not self.has_soap_fault():
            return None

        return {
            "code": self.fault_code,
            "string": self.fault_string,
            "detail": self.fault_detail
        }

    def get_error_summary(self) -> str:
        """Gibt eine zusammenfassende Fehlermeldung zurück"""
        if self.is_successful():
            return "Success"

        if self.has_soap_fault():
            return f"SOAP Fault: {self.fault_code} - {self.fault_string}"

        if self.error_message:
            return f"{self.status.value}: {self.error_message}"

        return f"Error: {self.status.value}"

    def to_ansible_result(self) -> Dict[str, Any]:
        """
        Konvertiert die Response in ein Ansible-kompatibles Result-Dictionary.
        Nützlich für die Presentation Layer.
        """
        result = {
            "changed": False,  # SOAP-Requests ändern normalerweise nichts an Ansible-Seite
            "request_id": self.request_id,
            "status": self.status.value,
            "status_code": self.status_code,
            "success": self.is_successful(),
        }

        if self.response_time_ms is not None:
            result["response_time_ms"] = self.response_time_ms

        if self.is_successful():
            result["body"] = self.body
            if self.parsed_body:
                result["parsed_body"] = self.parsed_body
        else:
            result["failed"] = True
            result["msg"] = self.get_error_summary()

            if self.has_soap_fault():
                result["fault"] = self.get_fault_info()

            if self.error_message:
                result["error"] = self.error_message

        return result

    def __repr__(self) -> str:
        return (f"SoapResponse(request_id='{self.request_id}', "
                f"status={self.status.value}, code={self.status_code})")
