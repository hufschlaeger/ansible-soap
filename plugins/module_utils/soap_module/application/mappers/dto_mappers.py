"""
Mapper zwischen DTOs und Domain-Objekten.
"""
from ..dtos.soap_request_dto import SoapRequestDTO, SoapResponseDTO
from ...domain.entities.endpoint import Endpoint
from ...domain.entities.soap_response import SoapResponse
from ..use_cases.send_soap_request_use_case import (
  SendSoapRequestCommand,
  SendSoapRequestResult
)
from ...domain.value_objects.auth_type import AuthType


class DtoMapper:
  """
  Mapper zwischen Application DTOs und Domain Objects.
  """

  @staticmethod
  def dto_to_command(dto: SoapRequestDTO) -> SendSoapRequestCommand:
    """
    Konvertiert SoapRequestDTO zu SendSoapRequestCommand.

    Args:
        dto: Input DTO

    Returns:
        Command-Objekt
    """
    # Auth-Type konvertieren
    if dto.auth_type and dto.auth_type.lower() != 'none':
      try:
        auth_type = AuthType[dto.auth_type.upper()]
      except KeyError:
        auth_type = None
    else:
      auth_type = None

    # Endpoint erstellen
    endpoint = Endpoint(
      url=dto.endpoint_url,
      name="default",
      auth_type=dto.auth_type,
      username=dto.username,
      password=dto.password,
      cert_path=dto.cert_path,
      key_path=dto.key_path,
      default_timeout=dto.timeout
    )

    # Body-Content bestimmen
    body_content = dto.body
    if not body_content and dto.body_dict:
      from ...domain.value_objects.xml_body import XmlBody
      xml_body = XmlBody.from_dict(
        dto.body_dict,
        root_tag=dto.body_root_tag,
        namespace=dto.namespace,  # add this
        namespace_prefix=dto.namespace_prefix
      )
      body_content = xml_body.to_string()

    # Command erstellen
    return SendSoapRequestCommand(
      endpoint=endpoint,
      soap_action=dto.soap_action,
      body_content=body_content,
      namespace=dto.namespace,
      namespace_prefix=dto.namespace_prefix,
      custom_headers=dto.headers,
      timeout=dto.timeout,
      validate_response=dto.validate,
      use_cache=dto.use_cache,
      max_retries=dto.max_retries,
      extract_xpath=dto.extract_xpath,
      strip_namespaces=dto.strip_namespaces
    )

  @staticmethod
  def result_to_dto(result: SendSoapRequestResult) -> SoapResponseDTO:
    """
    Konvertiert SendSoapRequestResult zu SoapResponseDTO.

    Args:
        result: Use Case Result

    Returns:
        Response DTO
    """
    if result.response:
      return SoapResponseDTO(
        success=result.success,
        status_code=result.response.status_code,
        body=result.response.body,
        headers=result.response.headers,
        response_time_ms=result.response.response_time_ms,
        extracted_data=result.extracted_data,
        error_message=result.error_message
      )
    else:
      return SoapResponseDTO(
        success=False,
        status_code=0,
        body="",
        error_message=result.error_message or "Unknown error"
      )

  @staticmethod
  def response_to_dto(response: SoapResponse) -> SoapResponseDTO:
    """
    Konvertiert Domain SoapResponse zu DTO.

    Args:
        response: Domain Response

    Returns:
        Response DTO
    """
    return SoapResponseDTO(
      success=response.is_successful(),
      status_code=response.status_code,
      body=response.body,
      headers=response.headers,
      response_time_ms=response.response_time_ms,
      error_message=response.error_message
    )
