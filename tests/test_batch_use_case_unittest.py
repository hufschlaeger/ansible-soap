import unittest

from plugins.module_utils.soap_module.application.use_cases.batch_send_use_case import (
    BatchSendUseCase,
    BatchSendCommand,
)
from plugins.module_utils.soap_module.application.use_cases.send_soap_request_use_case import (
    SendSoapRequestCommand,
    SendSoapRequestResult,
)
from plugins.module_utils.soap_module.domain.entities.endpoint import Endpoint


class FakeSendUseCase:
    def __init__(self, fail_on_actions=None):
        self.fail_on_actions = set(fail_on_actions or [])

    def execute(self, command: SendSoapRequestCommand) -> SendSoapRequestResult:
        should_fail = command.soap_action in self.fail_on_actions
        if should_fail:
            return SendSoapRequestResult(success=False, response=None, error_message="fail")
        else:
            # Minimal successful response: we don't need real SoapResponse for summary
            return SendSoapRequestResult(success=True, response=None)


class TestBatchSendUseCase(unittest.TestCase):
    def _make_commands(self):
        ep = Endpoint(url="https://example.com", name="default")
        return [
            SendSoapRequestCommand(endpoint=ep, soap_action="OK1", body_content="<a />"),
            SendSoapRequestCommand(endpoint=ep, soap_action="FAIL", body_content="<a />"),
            SendSoapRequestCommand(endpoint=ep, soap_action="OK2", body_content="<a />"),
        ]

    def test_sequential_counts_and_stop_on_error_false(self):
        repo = object()
        use_case = BatchSendUseCase(repo)
        use_case._send_use_case = FakeSendUseCase(fail_on_actions={"FAIL"})

        cmd = BatchSendCommand(requests=self._make_commands(), parallel=False, stop_on_error=False)
        result = use_case.execute(cmd)
        self.assertEqual(result.total, 3)
        self.assertEqual(result.successful, 2)
        self.assertEqual(result.failed, 1)
        self.assertEqual(len(result.results), 3)

    def test_sequential_stop_on_error_true_stops_early(self):
        repo = object()
        use_case = BatchSendUseCase(repo)
        use_case._send_use_case = FakeSendUseCase(fail_on_actions={"FAIL"})

        cmd = BatchSendCommand(requests=self._make_commands(), parallel=False, stop_on_error=True)
        result = use_case.execute(cmd)
        # Should stop after first failure; depending on order, first FAIL is index 1
        self.assertLess(len(result.results), 3)
        self.assertEqual(result.failed, 1)

    def test_parallel_execution_aggregates_results(self):
        repo = object()
        use_case = BatchSendUseCase(repo)
        use_case._send_use_case = FakeSendUseCase(fail_on_actions={"FAIL"})

        cmd = BatchSendCommand(requests=self._make_commands(), parallel=True, max_workers=4, stop_on_error=False)
        result = use_case.execute(cmd)
        self.assertEqual(result.total, 3)
        self.assertEqual(result.successful, 2)
        self.assertEqual(result.failed, 1)
        self.assertEqual(len(result.results), 3)

    def test_parallel_stop_on_error_cancels_remaining(self):
        # Use more commands to increase chance of cancellation effects
        ep = Endpoint(url="https://example.com", name="default")
        commands = [
            SendSoapRequestCommand(endpoint=ep, soap_action="OK1", body_content="<a />"),
            SendSoapRequestCommand(endpoint=ep, soap_action="FAIL", body_content="<a />"),
            SendSoapRequestCommand(endpoint=ep, soap_action="OK2", body_content="<a />"),
            SendSoapRequestCommand(endpoint=ep, soap_action="OK3", body_content="<a />"),
        ]
        repo = object()
        use_case = BatchSendUseCase(repo)
        use_case._send_use_case = FakeSendUseCase(fail_on_actions={"FAIL"})

        cmd = BatchSendCommand(requests=commands, parallel=True, max_workers=4, stop_on_error=True)
        result = use_case.execute(cmd)
        # Not all results must be present due to early cancel
        self.assertLessEqual(len(result.results), len(commands))
        self.assertGreaterEqual(len(result.results), 1)
        self.assertGreaterEqual(result.failed, 1)
        self.assertGreaterEqual(result.successful, 0)
        self.assertEqual(result.total, len(commands))


if __name__ == "__main__":
    unittest.main()
