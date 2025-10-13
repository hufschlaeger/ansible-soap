import unittest

from module_utils.soap_module.domain.entities.endpoint import Endpoint
from module_utils.soap_module.domain.entities.soap_request import SoapRequest
from module_utils.soap_module.domain.entities.soap_response import SoapResponse, ResponseStatus


class MyTestCase(unittest.TestCase):
    def test_endpointconnect(self):
        # Endpoint erstellen
        endpoint = Endpoint(
            url="http://blha-dimagapps-km/soap/webservice_3_5_0.php",
            name="Example API",
            auth_type=None,
            default_timeout=60
        )

        # Request erstellen
        request = SoapRequest(
            endpoint_url=endpoint.url,
            soap_action="GetUser",
            body="<GetUser><UserId>123</UserId></GetUser>",
            timeout=endpoint.default_timeout
        )

        response = SoapResponse(
            request_id=request.id,
            status=ResponseStatus.SUCCESS,
            status_code=200,
            body="<GetUserResponse>...</GetUserResponse>",
            response_time_ms=150.5
        )

        print(f'\n')
        print(f'Response: {response.is_successful()}\n')
        print(response.to_ansible_result())


if __name__ == '__main__':
    unittest.main()
