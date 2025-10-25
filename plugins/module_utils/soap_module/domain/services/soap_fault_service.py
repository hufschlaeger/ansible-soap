"""
Domain Service für SOAP Fault Handling.
"""
from typing import Optional, Dict
from ..entities.soap_response import SoapResponse, ResponseStatus
from ..value_objects.xml_body import XmlBody


class SoapFault:
    """Repräsentation eines SOAP Faults"""

    def __init__(
            self,
            fault_code: str,
            fault_string: str,
            fault_actor: Optional[str] = None,
            detail: Optional[str] = None
    ):
        self.fault_code = fault_code
        self.fault_string = fault_string
        self.fault_actor = fault_actor
        self.detail = detail

    def to_dict(self) -> Dict:
        """Konvertiert zu Dictionary"""
        return {
            "fault_code": self.fault_code,
            "fault_string": self.fault_string,
            "fault_actor": self.fault_actor,
            "detail": self.detail
        }

    def __str__(self) -> str:
        return f"SOAP Fault: {self.fault_code} - {self.fault_string}"


class SoapFaultService:
    """
    Domain Service für SOAP Fault Handling.
    """

    def extract_fault(self, response: SoapResponse) -> Optional[SoapFault]:
        """
        Extrahiert SOAP Fault Informationen aus einer Response.

        Args:
            response: Die zu analysierende Response

        Returns:
            SoapFault wenn vorhanden, sonst None
        """
        if response.status == ResponseStatus.SUCCESS:
            return None

        try:
            xml_body = XmlBody.from_string(response.body)

            # Nach Fault-Element suchen
            fault_code = xml_body.find_element('.//faultcode') or \
                         xml_body.find_element('.//{http://schemas.xmlsoap.org/soap/envelope/}faultcode') or \
                         xml_body.find_element('.//{http://www.w3.org/2003/05/soap-envelope}Code')

            fault_string = xml_body.find_element('.//faultstring') or \
                           xml_body.find_element('.//{http://schemas.xmlsoap.org/soap/envelope/}faultstring') or \
                           xml_body.find_element('.//{http://www.w3.org/2003/05/soap-envelope}Reason')

            fault_actor = xml_body.find_element('.//faultactor') or \
                          xml_body.find_element('.//{http://schemas.xmlsoap.org/soap/envelope/}faultactor')

            detail = xml_body.find_element('.//detail') or \
                     xml_body.find_element('.//{http://schemas.xmlsoap.org/soap/envelope/}detail') or \
                     xml_body.find_element('.//{http://www.w3.org/2003/05/soap-envelope}Detail')

            if fault_code or fault_string:
                return SoapFault(
                    fault_code=fault_code or "Unknown",
                    fault_string=fault_string or "Unknown error",
                    fault_actor=fault_actor,
                    detail=detail
                )

        except Exception:
            pass

        return None

    def is_retriable_fault(self, fault: SoapFault) -> bool:
        """
        Bestimmt ob ein Fault wiederholt werden sollte.

        Args:
            fault: Der zu prüfende Fault

        Returns:
            True wenn Retry sinnvoll, False sonst
        """
        retriable_codes = [
            'Server',  # SOAP 1.1
            'soap:Server',
            'Receiver',  # SOAP 1.2
            'soap:Receiver'
        ]

        return fault.fault_code in retriable_codes

    def categorize_fault(self, fault: SoapFault) -> str:
        """
        Kategorisiert einen Fault.

        Args:
            fault: Der zu kategorisierende Fault

        Returns:
            Kategorie als String
        """
        code_lower = fault.fault_code.lower()

        if 'client' in code_lower or 'sender' in code_lower:
            return "CLIENT_ERROR"
        elif 'server' in code_lower or 'receiver' in code_lower:
            return "SERVER_ERROR"
        elif 'version' in code_lower:
            return "VERSION_MISMATCH"
        elif 'mustunderstand' in code_lower:
            return "MUST_UNDERSTAND"
        else:
            return "UNKNOWN"
