import unittest

from plugins.module_utils.soap_module.application.dtos.soap_request_dto import SoapRequestDTO


class TestSoapRequestDTOValidation(unittest.TestCase):
    def test_validation_requires_endpoint_url(self):
        dto = SoapRequestDTO(
            endpoint_url="",
            soap_action="Action",
            body_dict={"Req": {"a": 1}},
        )
        is_valid, err = dto.validate_input()
        self.assertFalse(is_valid)
        self.assertIn("endpoint_url", err)

    def test_validation_requires_body_or_body_dict(self):
        dto = SoapRequestDTO(
            endpoint_url="https://example.com",
            soap_action="Action",
        )
        is_valid, err = dto.validate_input()
        self.assertFalse(is_valid)
        self.assertIn("body oder body_dict", err)

    def test_validation_mutually_exclusive_body_and_body_dict(self):
        dto = SoapRequestDTO(
            endpoint_url="https://example.com",
            soap_action="Action",
            body="<xml />",
            body_dict={"Req": {"a": 1}},
        )
        is_valid, err = dto.validate_input()
        self.assertFalse(is_valid)
        self.assertIn("nicht gleichzeitig", err)

    def test_validation_timeout_and_retries_ranges(self):
        dto_bad_timeout = SoapRequestDTO(
            endpoint_url="https://example.com",
            soap_action="Action",
            body="<xml />",
            timeout=0,
        )
        is_valid, err = dto_bad_timeout.validate_input()
        self.assertFalse(is_valid)
        self.assertIn("timeout", err)

        dto_bad_retries = SoapRequestDTO(
            endpoint_url="https://example.com",
            soap_action="Action",
            body="<xml />",
            max_retries=-1,
        )
        is_valid, err = dto_bad_retries.validate_input()
        self.assertFalse(is_valid)
        self.assertIn("max_retries", err)

    def test_validation_auth_basic_requires_creds(self):
        dto = SoapRequestDTO(
            endpoint_url="https://example.com",
            soap_action="Action",
            body="<xml />",
            auth_type="basic",
        )
        is_valid, err = dto.validate_input()
        self.assertFalse(is_valid)
        self.assertIn("Auth benötigt username und password", err)


if __name__ == "__main__":
    unittest.main()
