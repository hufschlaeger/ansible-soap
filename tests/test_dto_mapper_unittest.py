import unittest

from plugins.module_utils.soap_module.application.dtos.soap_request_dto import SoapRequestDTO
from plugins.module_utils.soap_module.application.mappers.dto_mappers import DtoMapper
from plugins.module_utils.soap_module.application.use_cases.send_soap_request_use_case import SendSoapRequestCommand


class TestDtoMapper(unittest.TestCase):
    def test_dto_to_command_with_body_dict_builds_xml_and_namespace(self):
        dto = SoapRequestDTO(
            endpoint_url="https://example.com/service",
            soap_action="NumberToWords",
            body_dict={
                "NumberToWords": {
                    "ubiNum": 42
                }
            },
            body_root_tag="Request",
            namespace="http://example.com/ns",
            namespace_prefix="ns",
            headers={"X-Test": "1"},
            timeout=15,
            auth_type="none",
        )

        cmd = DtoMapper.dto_to_command(dto)
        self.assertIsInstance(cmd, SendSoapRequestCommand)
        # Endpoint mapping
        self.assertEqual(cmd.endpoint.url, dto.endpoint_url)
        self.assertEqual(cmd.timeout, dto.timeout)
        # Body content was constructed from dict and contains namespace declarations
        self.assertIsNotNone(cmd.body_content)
        self.assertIn("xmlns:ns=\"http://example.com/ns\"", cmd.body_content)
        # Root tag should appear with prefix
        self.assertTrue("<ns:NumberToWords" in cmd.body_content or "<NumberToWords" in cmd.body_content)
        # Headers propagated
        self.assertEqual(cmd.custom_headers, {"X-Test": "1"})


if __name__ == "__main__":
    unittest.main()