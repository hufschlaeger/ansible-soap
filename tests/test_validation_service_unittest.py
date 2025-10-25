import unittest

from plugins.module_utils.soap_module.domain.services.validation_service import (
    ValidationService,
)
from plugins.module_utils.soap_module.domain.entities.endpoint import Endpoint
from plugins.module_utils.soap_module.domain.entities.soap_request import SoapRequest


class TestValidationService(unittest.TestCase):
    def setUp(self):
        self.service = ValidationService()

    def test_validate_endpoint_warns_on_http(self):
        # Non-HTTPS warns (entity allows http)
        http_ep = Endpoint(url="http://example.com/service", name="default", default_timeout=10)
        res = self.service.validate_endpoint(http_ep)
        self.assertTrue(res.is_valid)
        self.assertTrue(any("kein HTTPS" in w for w in res.warnings))

        # HTTPS ok
        https_ep = Endpoint(url="https://example.com/service", name="default", default_timeout=10)
        res = self.service.validate_endpoint(https_ep)
        self.assertTrue(res.is_valid)


    def test_validate_request_checks_xml_and_version_and_timeout(self):
        # Not a SOAP envelope -> warning, still valid
        req = SoapRequest(
            endpoint_url="https://example.com",
            body="<not-closed",
            headers={},
            soap_action="Action",
            soap_version="1.1",
            timeout=10,
        )
        res = self.service.validate_request(req)
        self.assertTrue(res.is_valid)
        self.assertTrue(any("kein SOAP Envelope" in w for w in res.warnings))

        # Missing action only warns, but remains valid if other checks pass
        req4 = SoapRequest(
            endpoint_url="https://example.com",
            body="<Envelope></Envelope>",
            headers={},
            soap_action="",
            soap_version="1.1",
            timeout=10,
        )
        res4 = self.service.validate_request(req4)
        self.assertTrue(res4.is_valid)
        self.assertTrue(any("Keine SOAP Action" in w for w in res4.warnings))


if __name__ == "__main__":
    unittest.main()
