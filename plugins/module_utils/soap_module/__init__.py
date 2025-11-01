"""
SOAP Module - Clean Architecture Implementation

Diese Collection implementiert SOAP-Client-Funktionalität nach Clean Architecture Prinzipien.
"""

from .application.dtos import SoapRequestDTO, SoapResponseDTO
from .application.mappers import DtoMapper
from .application.use_cases import (
    SendSoapRequestUseCase,
    BatchSendUseCase,
    ValidateEndpointUseCase
)
from .infrastructure.repositories import HttpSoapRepository

__version__ = '1.0.1'

__all__ = [
    'SoapRequestDTO',
    'SoapResponseDTO',
    'DtoMapper',
    'SendSoapRequestUseCase',
    'BatchSendUseCase',
    'ValidateEndpointUseCase',
    'HttpSoapRepository'
]
