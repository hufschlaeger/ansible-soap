import unittest
import sys
import os

# Ensure project root is on sys.path so 'plugins' package can be imported
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# We will import the module under test and monkey-patch its dependencies
import importlib


class ExitCalled(BaseException):
    def __init__(self, result):
        super().__init__("exit_json called")
        self.result = result


class FailCalled(BaseException):
    def __init__(self, result):
        super().__init__("fail_json called")
        self.result = result


class FakeAnsibleModule:
    def __init__(self, argument_spec=None, supports_check_mode=False, **kwargs):
        # kwargs may contain mutually_exclusive, required_one_of, required_if etc.
        self.params = self._params
        self.check_mode = False

    # The test will inject _params before constructing this class
    _params = {}

    def exit_json(self, **kwargs):
        raise ExitCalled(kwargs)

    def fail_json(self, **kwargs):
        raise FailCalled(kwargs)


class FakeHttpSoapRepository:
    def __init__(self, verify_ssl=True, timeout=None):
        self.verify_ssl = verify_ssl
        self.timeout = timeout

    def close(self):
        pass


class FakeUseCase:
    def __init__(self, repository):
        self.repository = repository
        self._next_success = True
        self._next_result = None

    def set_result(self, success=True, extra=None):
        self._next_success = success
        self._next_result = extra or {}

    def execute(self, command):
        # Return a simple obj with attributes expected by DtoMapper.result_to_dto usage
        class Result:
            def __init__(self, success, payload):
                self.success = success
                self.response = None
                self.validation_errors = None
                self.error_message = None if success else "error"
                self.extracted_data = payload.get("extracted_data")

        return Result(self._next_success, self._next_result or {})


class FakeDtoMapper:
    @staticmethod
    def dto_to_command(dto):
        # Return a simple command placeholder
        return {"dto": dto}

    class _Resp:
        def __init__(self, data):
            self._data = data

        def to_dict(self):
            return self._data

    @staticmethod
    def result_to_dto(result):
        # Build a minimal dict based on result
        base = {"success": result.success, "status_code": 200 if result.success else 500, "body": ""}
        if result.extracted_data is not None:
            base["extracted_data"] = result.extracted_data
        return FakeDtoMapper._Resp(base)


class TestSoapRequestModule(unittest.TestCase):
    def _import_and_patch(self, params, use_case_success=True):
        # Ensure a fresh import each time
        if "plugins.modules.soap_request" in list(importlib.sys.modules.keys()):
            del importlib.sys.modules["plugins.modules.soap_request"]

        # Inject a fake 'ansible.module_utils.basic' with our FakeAnsibleModule
        import types
        fake_ansible = types.ModuleType("ansible")
        fake_module_utils = types.ModuleType("ansible.module_utils")
        fake_basic = types.ModuleType("ansible.module_utils.basic")
        fake_basic.AnsibleModule = FakeAnsibleModule
        sys.modules["ansible"] = fake_ansible
        sys.modules["ansible.module_utils"] = fake_module_utils
        sys.modules["ansible.module_utils.basic"] = fake_basic

        mod = importlib.import_module("plugins.modules.soap_request")

        # Patch AnsibleModule
        FakeAnsibleModule._params = params
        mod.AnsibleModule = FakeAnsibleModule

        # Mark SOAP module available and patch DTO symbol used later
        mod.HAS_SOAP_MODULE = True
        class FakeSoapRequestDTO:
            def __init__(self, **kwargs):
                # mimic real DTO by storing fields and providing validate_input()
                self.__dict__.update(kwargs)
            def validate_input(self):
                # replicate key validation behavior used by module
                if not self.endpoint_url:
                    return False, "endpoint_url ist erforderlich"
                if not self.body and not self.body_dict:
                    return False, "Entweder body oder body_dict muss angegeben werden"
                if self.body and self.body_dict:
                    return False, "body und body_dict können nicht gleichzeitig angegeben werden"
                if self.timeout < 1:
                    return False, "timeout muss mindestens 1 Sekunde sein"
                return True, None
        mod.SoapRequestDTO = FakeSoapRequestDTO

        # Patch dependencies
        mod.HttpSoapRepository = FakeHttpSoapRepository
        fake_use_case = FakeUseCase(None)
        fake_use_case.set_result(success=use_case_success)
        # Replace the class with a factory that returns our configured fake
        class UseCaseFactory:
            def __init__(self, repository):
                self._fake = fake_use_case
            def execute(self, command):
                return fake_use_case.execute(command)
        mod.SendSoapRequestUseCase = UseCaseFactory
        mod.DtoMapper = FakeDtoMapper
        return mod, fake_use_case

    def test_success_path_exits_with_success_result(self):
        params = {
            "endpoint_url": "https://example.com",
            "soap_action": "Action",
            "body": "<xml />",
            "body_root_tag": "Request",
            "namespace_prefix": "ns",
            "soap_version": "1.1",
            "timeout": 5,
            "auth_type": "none",
            "validate_certs": True,
            "use_cache": False,
            "max_retries": 0,
            "strip_namespaces": False,
            "validate": True,
        }
        mod, fake_uc = self._import_and_patch(params, use_case_success=True)
        with self.assertRaises(ExitCalled) as ctx:
            mod.run_module()
        out = ctx.exception.result
        self.assertTrue(out.get("success"))
        self.assertTrue(out.get("changed"))
        self.assertIn("status_code", out)

    def test_validation_error_triggers_fail_json(self):
        # Provide neither body nor body_dict to make DTO validation fail
        params = {
            "endpoint_url": "https://example.com",
            "soap_action": "Action",
            "body_root_tag": "Request",
            "namespace_prefix": "ns",
            "soap_version": "1.1",
            "timeout": 5,
            "auth_type": "none",
            "validate_certs": True,
            "use_cache": False,
            "max_retries": 0,
            "strip_namespaces": False,
            "validate": True,
        }
        mod, _ = self._import_and_patch(params, use_case_success=True)
        with self.assertRaises(FailCalled) as ctx:
            mod.run_module()
        out = ctx.exception.result
        self.assertIn("Input validation failed", out.get("msg", ""))
        self.assertIn("body oder body_dict", out.get("error", ""))

    def test_use_case_failure_results_in_fail_json(self):
        params = {
            "endpoint_url": "https://example.com",
            "soap_action": "Action",
            "body": "<xml />",
            "body_root_tag": "Request",
            "namespace_prefix": "ns",
            "soap_version": "1.1",
            "timeout": 5,
            "auth_type": "none",
            "validate_certs": True,
            "use_cache": False,
            "max_retries": 0,
            "strip_namespaces": False,
            "validate": True,
        }
        mod, fake_uc = self._import_and_patch(params, use_case_success=False)
        with self.assertRaises(FailCalled) as ctx:
            mod.run_module()
        out = ctx.exception.result
        self.assertFalse(out.get("success"))
        self.assertIn("SOAP request failed", out.get("msg", ""))


if __name__ == "__main__":
    unittest.main()
