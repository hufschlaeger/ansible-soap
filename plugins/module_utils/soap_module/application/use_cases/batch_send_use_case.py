"""
Use Case: Multiple SOAP Requests gleichzeitig senden.
"""
from typing import List, Dict, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from .send_soap_request_use_case import (
    SendSoapRequestUseCase,
    SendSoapRequestCommand,
    SendSoapRequestResult
)
from ...domain.repositories.soap_repository import SoapRepository


@dataclass
class BatchSendCommand:
    """Command für Batch-Sending"""
    requests: List[SendSoapRequestCommand]
    parallel: bool = False
    max_workers: int = 5
    stop_on_error: bool = False


@dataclass
class BatchSendResult:
    """Result des Batch-Sendings"""
    total: int
    successful: int
    failed: int
    results: List[SendSoapRequestResult]

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary"""
        return {
            'total': self.total,
            'successful': self.successful,
            'failed': self.failed,
            'results': [r.to_dict() for r in self.results]
        }


class BatchSendUseCase:
    """
    Use Case für das Senden mehrerer SOAP-Requests.
    """

    def __init__(self, repository: SoapRepository):
        """
        Args:
            repository: SOAP Repository
        """
        self._send_use_case = SendSoapRequestUseCase(repository)

    def execute(self, command: BatchSendCommand) -> BatchSendResult:
        """
        Führt Batch-Sending aus.

        Args:
            command: Batch Command

        Returns:
            BatchSendResult
        """
        if command.parallel:
            return self._execute_parallel(command)
        else:
            return self._execute_sequential(command)

    def _execute_sequential(self, command: BatchSendCommand) -> BatchSendResult:
        """Führt Requests sequenziell aus"""
        results = []
        successful = 0
        failed = 0

        for request_command in command.requests:
            result = self._send_use_case.execute(request_command)
            results.append(result)

            if result.success:
                successful += 1
            else:
                failed += 1
                if command.stop_on_error:
                    break

        return BatchSendResult(
            total=len(command.requests),
            successful=successful,
            failed=failed,
            results=results
        )

    def _execute_parallel(self, command: BatchSendCommand) -> BatchSendResult:
        """Führt Requests parallel aus"""
        results = []
        successful = 0
        failed = 0

        with ThreadPoolExecutor(max_workers=command.max_workers) as executor:
            # Futures erstellen
            future_to_command = {
                executor.submit(self._send_use_case.execute, cmd): cmd
                for cmd in command.requests
            }

            # Ergebnisse sammeln
            for future in as_completed(future_to_command):
                try:
                    result = future.result()
                    results.append(result)

                    if result.success:
                        successful += 1
                    else:
                        failed += 1
                        if command.stop_on_error:
                            # Verbleibende Futures canceln
                            for f in future_to_command:
                                f.cancel()
                            break

                except Exception as e:
                    # Fehler bei Ausführung
                    failed += 1
                    results.append(SendSoapRequestResult(
                        success=False,
                        response=None,
                        error_message=f"Execution error: {e}"
                    ))

        return BatchSendResult(
            total=len(command.requests),
            successful=successful,
            failed=failed,
            results=results
        )